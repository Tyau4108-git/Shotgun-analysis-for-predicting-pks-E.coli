#!/bin/bash
# -----------------------------------------------------------
# BLAST Database Construction and Search Script for Colibactin Research
# Batch script for processing multiple FASTA files to search for clb genes
# 
# Usage:
# 1. Modify the paths in the "User Configuration Area" below
# 2. Execute with: bash BlastDB\(for\ loop\).sh
# -----------------------------------------------------------

# ===== User Configuration Area =====

# 1. BLAST executable directory - Required modification
blast_dir="/path/to/blast/bin"  # ← Specify your BLAST installation directory

# 2. Input file directory - Required modification
input_dir="/path/to/combined/fasta/files"  # ← Specify directory containing combined FASTA files

# 3. Query file specification - Required modification
query_file="/path/to/clb_genes.fna"  # ← Specify full path to clb_genes.fna file

# 4. BLAST DB and output file destination - Required modification
blast_db_folder="/path/to/blast/output"  # ← Specify directory for BLAST results

# 5. BLAST search parameter configuration
# Nucleotide sequence identity threshold (%) - Adjust according to research objectives
# Validated at 60%, 70%, 80%, 90% in referenced studies
PERC_IDENTITY=97  # ← Specify nucleotide sequence identity (set within 60-100 range)

# E-value threshold - Statistical significance threshold
EVALUE=1e-5  # ← Publication-compliant setting (can be changed to 1e-10 for stricter criteria)

# Maximum number of target sequences
MAX_TARGET_SEQS=10000000

# Number of threads (adjust according to your computer's performance)
NUM_THREADS=2

# 6. BLASTDB environment variable (optional)
export BLASTDB="$blast_db_folder"

# ===== End of User Configuration Area =====

# BLAST executable path configuration
makeblastdb_cmd="$blast_dir/makeblastdb"
blastn_cmd="$blast_dir/blastn"

# For Windows BLAST, add .exe extension as follows
# makeblastdb_cmd="$blast_dir/makeblastdb.exe"
# blastn_cmd="$blast_dir/blastn.exe"

# Create output directory
[ ! -d "$blast_db_folder" ] && mkdir -p "$blast_db_folder"

# Log file to record processed files
log_file="$blast_db_folder/processed_files.log"
touch "$log_file"

# Error log file
error_log="$blast_db_folder/error.log"

echo "BLAST Database Construction and Search Script for Colibactin Research"
echo "Input directory: $input_dir"
echo "Query file: $query_file"
echo "Output directory: $blast_db_folder"
echo "BLAST executable: $blast_dir"
echo "Nucleotide sequence identity threshold: ${PERC_IDENTITY}%"
echo "E-value threshold: $EVALUE"
echo "====================================="

# Configuration verification
if [ ! -d "$input_dir" ]; then
    echo "Error: Input directory not found: $input_dir"
    echo "Please correct the input_dir path at the top of the script."
    exit 1
fi

if [ ! -f "$query_file" ]; then
    echo "Error: Query file not found: $query_file"
    echo "Please correct the query_file path at the top of the script."
    exit 1
fi

if [ ! -f "$makeblastdb_cmd" ]; then
    echo "Error: makeblastdb not found: $makeblastdb_cmd"
    echo "Please correct the blast_dir path at the top of the script."
    exit 1
fi

if [ ! -f "$blastn_cmd" ]; then
    echo "Error: blastn not found: $blastn_cmd"
    echo "Please correct the blast_dir path at the top of the script."
    exit 1
fi

# Parameter validation
if [ "$PERC_IDENTITY" -lt 60 ] || [ "$PERC_IDENTITY" -gt 100 ]; then
    echo "Warning: Nucleotide sequence identity threshold ($PERC_IDENTITY%) is outside recommended range."
    echo "Validated within 60-90% range in referenced studies."
fi

# Function to check file size
check_file_size() {
    [ -s "$1" ]
}

# Function to get file line count
count_file_lines() {
    wc -l < "$1"
}

# Begin processing
echo "Starting batch processing of FASTA files at $(date)" | tee -a "$log_file"
echo "Parameters: identity=${PERC_IDENTITY}%, evalue=${EVALUE}" | tee -a "$log_file"
echo "-------------------------------------------" | tee -a "$log_file"

# Search for FASTA files (files ending with .fa)
for input_file in "$input_dir"/*.fa; do
    # Check if file exists
    if [ ! -f "$input_file" ]; then
        echo "No .fa files found in $input_dir" | tee -a "$error_log"
        exit 1
    fi
    
    # Extract base name from filename
    file_base=$(basename "$input_file")
    sample_name="${file_base%.fa}"
    
    # Check if already processed (including parameters)
    search_pattern="${sample_name}_identity${PERC_IDENTITY}_evalue${EVALUE} completed"
    if grep -q "$search_pattern" "$log_file"; then
        echo "Skipping $sample_name - already processed with current parameters" | tee -a "$log_file"
        continue
    fi
    
    echo "Processing file: $file_base ($(date))" | tee -a "$log_file"
    echo "Parameters: identity=${PERC_IDENTITY}%, evalue=${EVALUE}" | tee -a "$log_file"
    
    # Create dedicated folder for sample (including parameters)
    sample_folder="$blast_db_folder/${sample_name}_identity${PERC_IDENTITY}_evalue${EVALUE}"
    [ ! -d "$sample_folder" ] && mkdir -p "$sample_folder"
    
    # Output filename configuration
    output_tsv="$sample_folder/${sample_name}_identity${PERC_IDENTITY}_evalue${EVALUE}.tsv"
    output_alignment="$sample_folder/${sample_name}_identity${PERC_IDENTITY}_evalue${EVALUE}_alignment.txt"
    
    # Database file configuration
    db_name="$sample_name"
    db_out="$sample_folder/$db_name"
    
    # Check if database files exist
    db_files_exist=true
    for ext in ndb nhr nin njs nog nos not nsq ntf nto; do
        if [ ! -f "${db_out}.${ext}" ]; then
            db_files_exist=false
            break
        fi
    done
    
    # Create database only if it doesn't exist
    if [ "$db_files_exist" = false ]; then
        echo "Creating BLAST database for $sample_name..." | tee -a "$log_file"
        
        # Temporarily change current directory to sample folder
        current_dir=$(pwd)
        cd "$sample_folder"
        
        # Execute makeblastdb
        "$makeblastdb_cmd" -in "$input_file" -dbtype nucl -out "$db_name" -title "$sample_name" -parse_seqids
        
        if [ $? -ne 0 ]; then
            echo "Error creating BLAST database for $sample_name" | tee -a "$error_log"
            cd "$current_dir"
            continue
        fi
        
        # Return to original directory
        cd "$current_dir"
        echo "BLAST database creation complete for $sample_name." | tee -a "$log_file"
    else
        echo "BLAST database already exists for $sample_name. Skipping database creation." | tee -a "$log_file"
    fi
    
    # BLAST search (with alignment information)
    echo "Running interactive BLAST search for $sample_name with identity=${PERC_IDENTITY}%..." | tee -a "$log_file"
    
    # Temporarily change current directory to sample folder
    current_dir=$(pwd)
    cd "$sample_folder"
    
    "$blastn_cmd" -query "$query_file" \
                 -db "$db_name" \
                 -out "${sample_name}_identity${PERC_IDENTITY}_evalue${EVALUE}_alignment.txt" \
                 -outfmt 7 \
                 -evalue "$EVALUE" \
                 -max_target_seqs "$MAX_TARGET_SEQS" \
                 -perc_identity "$PERC_IDENTITY" \
                 -num_threads "$NUM_THREADS"
    
    # BLAST search (tab-delimited TSV output)
    echo "Running structured BLAST search for $sample_name with identity=${PERC_IDENTITY}%..." | tee -a "$log_file"
    "$blastn_cmd" -query "$query_file" \
                 -db "$db_name" \
                 -out "${sample_name}_identity${PERC_IDENTITY}_evalue${EVALUE}.tsv" \
                 -outfmt 6 \
                 -evalue "$EVALUE" \
                 -max_target_seqs "$MAX_TARGET_SEQS" \
                 -perc_identity "$PERC_IDENTITY" \
                 -num_threads "$NUM_THREADS"
    
    # Return to original directory
    cd "$current_dir"
    
    # Verify results
    if check_file_size "$output_tsv"; then
        hits=$(count_file_lines "$output_tsv")
        echo "Results saved in $output_tsv" | tee -a "$log_file"
        echo "Number of hits found: $hits (identity≥${PERC_IDENTITY}%)" | tee -a "$log_file"
    else
        echo "No BLAST hits found for $sample_name with identity≥${PERC_IDENTITY}%." | tee -a "$log_file"
    fi
    
    if check_file_size "$output_alignment"; then
        echo "Alignment results saved in $output_alignment" | tee -a "$log_file"
    else
        echo "No alignment output generated for $sample_name." | tee -a "$log_file"
    fi
    
    # Record processing completion (including parameters)
    echo "${sample_name}_identity${PERC_IDENTITY}_evalue${EVALUE} completed at $(date)" | tee -a "$log_file"
    echo "-------------------------------------------" | tee -a "$log_file"
done

echo "All files have been processed with parameters: identity=${PERC_IDENTITY}%, evalue=${EVALUE}" | tee -a "$log_file"
echo "Batch processing completed at $(date)" | tee -a "$log_file"