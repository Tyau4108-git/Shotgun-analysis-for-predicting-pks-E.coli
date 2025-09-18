import os
import re
import pandas as pd
import glob

def count_unique_subjects_by_query(file_path):
    """
    For each line in the file (skip header lines starting with '#'):
    - Extract "clbX" (e.g., "clbA") from the 1st column (query acc.ver)
    - Extract the numeric middle portion from the 2nd column (subject acc.ver) 
      with flexible pattern matching for various ID formats
    Supports multiple sequencing data prefixes: DRR, SRR, ERR, or custom IDs
    Returns the count of unique numbers and sample ID for each group.
    
    Note: Total read counts for each sample cannot be obtained from this function.
    If total metagenomic read counts are needed, please retrieve them separately from FASTA files.
    """
    group_to_numbers = {}
    sample_id = None
    blast_hit_count = 0  # BLAST hit count (reference value)
    
    with open(file_path, 'r') as f:
        for line in f:
            # Skip header lines
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue
            query = parts[0]  # e.g., "clbA.eco"
            group = query.split(".")[0]  # "clbA" etc.
            subject = parts[1]  # e.g., "DRR171459.16276716:2" or "SRR123456_789012-3" etc.
            
            # Count BLAST hits (reference value)
            blast_hit_count += 1
            
            # Flexible pattern matching for various sample ID formats
            if sample_id is None:
                # Try multiple common patterns
                patterns = [
                    r"(DRR\d+)",           # DRR followed by any number of digits
                    r"(SRR\d+)",           # SRR followed by any number of digits
                    r"(ERR\d+)",           # ERR followed by any number of digits
                    r"([A-Z]{2,4}\d{4,})", # 2-4 uppercase letters followed by 4+ digits
                    r"^(\w+?)[\._\-:]",   # Any word characters before common separators
                    r"^([^\._\-:]+)"      # Everything before first separator
                ]
                
                for pattern in patterns:
                    m_id = re.search(pattern, subject)
                    if m_id:
                        sample_id = m_id.group(1)
                        break
                
                if sample_id is None:
                    sample_id = "Unknown"
            
            # Flexible extraction of numeric portion after sample ID
            # Try multiple separator patterns
            separators = [r"\.", r"_", r"-", r":"]
            numeric_patterns = [
                rf"{re.escape(sample_id)}[\.\_\-:](\d+)",  # ID followed by separator and numbers
                rf"[\.\_\-:](\d+)[\.\_\-:]",               # Numbers between separators
                r"[\.\_\-:](\d+)$",                        # Numbers after separator at end
                r"^[^\.\_\-:]*[\.\_\-:](\d+)"              # First numbers after any separator
            ]
            
            extracted_num = None
            for pattern in numeric_patterns:
                m = re.search(pattern, subject)
                if m:
                    extracted_num = m.group(1)
                    break
            
            # If no pattern matched, try to extract any sequence of digits
            if not extracted_num:
                # Find all sequences of digits and take the first substantial one (>3 digits)
                all_numbers = re.findall(r'\d+', subject)
                for num in all_numbers:
                    if len(num) > 3 and not num.startswith(sample_id[-3:] if len(sample_id) > 3 else sample_id):
                        extracted_num = num
                        break
            
            if extracted_num:
                if group not in group_to_numbers:
                    group_to_numbers[group] = set()
                group_to_numbers[group].add(extracted_num)
    
    # Calculate the count of unique numbers for each group
    group_counts = {group: len(nums) for group, nums in group_to_numbers.items()}
    
    # Also try to extract sample ID from filename if not found
    if sample_id is None or sample_id == "Unknown":
        file_name = os.path.basename(file_path)
        
        # Try various filename patterns
        filename_patterns = [
            r"([A-Z]{2,4}\d{4,}).*_alignment\.txt",  # Standard prefix with numbers
            r"(.+?)_identity\d+.*_alignment\.txt",    # Sample name before parameters
            r"(.+?)_alignment\.txt",                  # Simple pattern
            r"^([^_]+)"                              # Everything before first underscore
        ]
        
        for pattern in filename_patterns:
            m_file = re.search(pattern, file_name)
            if m_file:
                potential_id = m_file.group(1)
                if potential_id and potential_id != "Unknown":
                    sample_id = potential_id
                    break
    
    return sample_id, group_counts, blast_hit_count

def get_total_reads_from_fasta(fasta_file_path):
    """
    Retrieve total read count from FASTA file
    
    Args:
        fasta_file_path (str): Path to FASTA file
        
    Returns:
        int: Total read count (returns -1 if file not found)
    """
    if not os.path.exists(fasta_file_path):
        return -1
    
    try:
        total_reads = 0
        with open(fasta_file_path, 'r') as f:
            for line in f:
                if line.startswith('>'):
                    total_reads += 1
        return total_reads
    except:
        return -1

def find_matching_fasta(fasta_dir, sample_id):
    """
    Find matching FASTA file with flexible naming patterns
    
    Args:
        fasta_dir (str): Directory containing FASTA files
        sample_id (str): Sample identifier
        
    Returns:
        str: Path to matching FASTA file or None if not found
    """
    if not os.path.exists(fasta_dir):
        return None
    
    # Try multiple file extensions and naming patterns
    extensions = ['.fa', '.fasta', '.fna', '.fa.gz', '.fasta.gz']
    
    for ext in extensions:
        # Try exact match
        exact_path = os.path.join(fasta_dir, f"{sample_id}{ext}")
        if os.path.exists(exact_path):
            return exact_path
        
        # Try with wildcards
        pattern_paths = glob.glob(os.path.join(fasta_dir, f"{sample_id}*{ext}"))
        if pattern_paths:
            return pattern_paths[0]
        
        # Try case-insensitive match
        all_files = glob.glob(os.path.join(fasta_dir, f"*{ext}"))
        for file_path in all_files:
            if sample_id.lower() in os.path.basename(file_path).lower():
                return file_path
    
    return None

def extract_parameters_from_filename(file_path):
    """
    Extract BLAST parameters from filename with flexible pattern matching
    """
    file_name = os.path.basename(file_path)
    
    # Try multiple parameter patterns
    patterns = [
        r"identity(\d+).*evalue([\de\-\+\.]+)",     # Standard pattern
        r"id(\d+).*e([\de\-\+\.]+)",                # Shortened version
        r"(\d+).*evalue([\de\-\+\.]+)",             # Just numbers and evalue
        r"identity(\d+)",                            # Identity only
        r"evalue([\de\-\+\.]+)"                      # E-value only
    ]
    
    identity = "unknown"
    evalue = "unknown"
    
    for pattern in patterns:
        m = re.search(pattern, file_name, re.IGNORECASE)
        if m:
            if len(m.groups()) == 2:
                identity = m.group(1)
                evalue = m.group(2)
            elif "identity" in pattern.lower() or pattern.startswith(r"(\d+)"):
                identity = m.group(1)
            elif "evalue" in pattern.lower():
                evalue = m.group(1)
            
            if identity != "unknown" and evalue != "unknown":
                break
    
    return identity, evalue

# ===== User Configuration Area =====

# Input directory path - Required modification
input_dir = "/path/to/blast/results"  # ← Specify directory containing BLAST result files (*_alignment.txt)

# FASTA file directory path - For total read count retrieval (optional)
fasta_dir = "/path/to/combined/fasta/files"  # ← Directory containing combined FASTA files (for total read count retrieval)

# Output Excel file path - Required modification
output_excel = "/path/to/output/clb_counts.xlsx"  # ← Specify path for saving result Excel file

# Whether to output results by parameters (True/False)
SEPARATE_BY_PARAMETERS = True  # ← Set to True to output results separated by sequence identity

# Advanced pattern configuration (optional)
# Add custom sample ID patterns if your data uses non-standard formats
CUSTOM_ID_PATTERNS = [
    # Add your custom patterns here, e.g.:
    # r"(MYLAB\d{8})",  # Custom lab ID format
    # r"(Sample_\d+)",   # Sample_123 format
]

# ===== End of User Configuration Area =====

print(f"clb Gene Count Analysis Script (Colibactin Research)")
print(f"Version: Flexible Pattern Matching")
print(f"Input directory: {input_dir}")
print(f"FASTA directory: {fasta_dir}")
print(f"Output file: {output_excel}")
print(f"Parameter-specific output: {SEPARATE_BY_PARAMETERS}")
print("-" * 50)

# Check directory existence
if not os.path.exists(input_dir):
    print(f"Error: Input directory not found: {input_dir}")
    print("Please modify input_dir at the top of the script to the correct path.")
    exit(1)

# Get list of files matching *_alignment.txt pattern
alignment_files = glob.glob(os.path.join(input_dir, "*_alignment.txt"))

# Also search subdirectories
if not alignment_files:
    alignment_files = glob.glob(os.path.join(input_dir, "**/*_alignment.txt"), recursive=True)

# Try alternative patterns if no files found
if not alignment_files:
    alternative_patterns = ["*.txt", "*alignment*", "*blast*", "*result*"]
    for pattern in alternative_patterns:
        alignment_files = glob.glob(os.path.join(input_dir, f"**/{pattern}"), recursive=True)
        if alignment_files:
            print(f"Found files using pattern: {pattern}")
            break

if not alignment_files:
    print(f"Error: No alignment files found in {input_dir}.")
    print("Please verify that BLAST search completed successfully.")
    print("Searched patterns: *_alignment.txt, *.txt, *alignment*, *blast*, *result*")
    exit(1)

print(f"Number of files to process: {len(alignment_files)}")

# List to store all results
all_results = []

# Dictionary to store results by parameters (if SEPARATE_BY_PARAMETERS=True)
parameter_results = {}

# Track unique sample ID patterns found
found_patterns = set()

# Process each file
for file_path in alignment_files:
    print(f"Processing: {os.path.basename(file_path)}")
    
    # Extract sample name and parameters from filename
    file_name = os.path.basename(file_path)
    
    # Extract parameters (flexible patterns)
    identity, evalue = extract_parameters_from_filename(file_name)
    
    if identity != "unknown" and evalue != "unknown":
        parameter_key = f"identity{identity}_evalue{evalue}"
    else:
        parameter_key = "default"
    
    # Get count of unique subject numeric portions, sample ID, and BLAST hit count for each query
    sample_id, counts, blast_hit_count = count_unique_subjects_by_query(file_path)
    
    # Track the pattern type found
    if sample_id and sample_id != "Unknown":
        if sample_id.startswith("DRR"):
            found_patterns.add("DRR")
        elif sample_id.startswith("SRR"):
            found_patterns.add("SRR")
        elif sample_id.startswith("ERR"):
            found_patterns.add("ERR")
        else:
            found_patterns.add("Custom")
    
    # Try to find matching FASTA file with flexible patterns
    fasta_file_path = find_matching_fasta(fasta_dir, sample_id)
    total_reads = -1
    
    if fasta_file_path:
        total_reads = get_total_reads_from_fasta(fasta_file_path)
        print(f"  → Found FASTA file: {os.path.basename(fasta_file_path)}")
    else:
        print(f"  → FASTA file not found for sample: {sample_id}")
    
    # Set 0 for missing groups from clbA to clbS
    all_groups = [f"clb{chr(i)}" for i in range(ord('A'), ord('S')+1)]
    
    # Basic result dictionary
    row_data = {
        "Sample": sample_id,
        "Identity_Threshold": f"{identity}%" if identity != "unknown" else "unknown",
        "E_value": evalue,
        "Total_reads": total_reads if total_reads > 0 else "N/A"  # Add total read count
    }
    
    for group in all_groups:
        row_data[group] = counts.get(group, 0)
    
    # Add total clb gene count and cluster score
    total_clb_count = sum(counts.values())
    detected_genes_count = sum(1 for count in counts.values() if count > 0)
    
    row_data["Total_clb_reads"] = total_clb_count
    row_data["Detected_genes_count"] = detected_genes_count
    
    # pks+ determination (based on literature criteria)
    # Criterion 1: clbB-only determination (positive if >0 reads)
    row_data["pks_positive_clbB"] = 1 if counts.get("clbB", 0) > 0 else 0
    
    # Criterion 2: Total read sum of all clb genes (Nooij et al. criterion)
    row_data["pks_positive_cluster"] = 1 if total_clb_count > 0 else 0
    
    # Add results to list
    all_results.append(row_data)
    
    # Also save parameter-specific results
    if SEPARATE_BY_PARAMETERS:
        if parameter_key not in parameter_results:
            parameter_results[parameter_key] = []
        parameter_results[parameter_key].append(row_data)
    
    # Progress display
    print(f"  → Sample ID: {sample_id}")
    print(f"  → Total reads of detected clb genes: {total_clb_count}")
    print(f"  → Number of detected genes: {detected_genes_count}/19")
    print(f"  → Parameters: identity={identity}%, evalue={evalue}")
    print(f"  → Total reads: {total_reads if total_reads > 0 else 'FASTA file not detected'}")

# Display detected patterns
if found_patterns:
    print(f"\nDetected sample ID patterns: {', '.join(sorted(found_patterns))}")

# Create output directory if it doesn't exist
output_dir = os.path.dirname(output_excel)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

# Convert all results to DataFrame
df_all = pd.DataFrame(all_results)

# Sort by Sample (with handling for unknown values)
sort_columns = []
if 'Identity_Threshold' in df_all.columns:
    sort_columns.append('Identity_Threshold')
if 'E_value' in df_all.columns:
    sort_columns.append('E_value')
sort_columns.append('Sample')

df_all = df_all.sort_values(sort_columns)

# Save with multiple sheets using ExcelWriter
with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    # All results sheet
    df_all.to_excel(writer, sheet_name='All_Results', index=False)
    
    # Parameter-specific sheets (if configured)
    if SEPARATE_BY_PARAMETERS and parameter_results:
        for param_key, param_data in parameter_results.items():
            df_param = pd.DataFrame(param_data)
            df_param = df_param.sort_values('Sample')
            # Handle sheet name length limitation
            sheet_name = param_key[:31]  # Excel sheet names limited to 31 characters
            df_param.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"\nProcessing complete:")
print(f"  Number of processed files: {len(alignment_files)}")
print(f"  Results saved to Excel file '{output_excel}'.")
print(f"  Number of output rows: {len(all_results)}")

# Display basic statistics
if all_results:
    print(f"\nStatistics:")
    
    # Group by parameters if they exist
    group_columns = []
    if df_all['Identity_Threshold'].nunique() > 1 or df_all['E_value'].nunique() > 1:
        group_columns = ['Identity_Threshold', 'E_value']
    
    if group_columns:
        parameter_groups = df_all.groupby(group_columns)
        
        for params, group in parameter_groups:
            if len(group_columns) == 2:
                identity, evalue = params
                print(f"\n  Parameters: identity={identity}, evalue={evalue}")
            else:
                print(f"\n  Parameters: {params}")
            
            total_samples = len(group)
            
            # Positive rate for each criterion
            clbB_positive = group['pks_positive_clbB'].sum()
            cluster_positive = group['pks_positive_cluster'].sum()
            
            print(f"    Positive by clbB criterion: {clbB_positive}/{total_samples} samples ({clbB_positive/total_samples*100:.1f}%)")
            print(f"    Positive by cluster criterion: {cluster_positive}/{total_samples} samples ({cluster_positive/total_samples*100:.1f}%)")
            
            # Display total read statistics
            valid_reads = group[group['Total_reads'] != 'N/A']['Total_reads']
            if len(valid_reads) > 0:
                avg_total_reads = valid_reads.astype(int).mean()
                print(f"    Average total reads: {avg_total_reads:.0f} reads/sample (retrieved from {len(valid_reads)}/{total_samples} samples)")
            else:
                print(f"    Total reads: Could not retrieve from FASTA files")
            
            # Detection rate for each clb gene
            all_groups = [f"clb{chr(i)}" for i in range(ord('A'), ord('S')+1)]
            detected_by_gene = {}
            for gene in all_groups:
                positive_samples = (group[gene] > 0).sum()
                if positive_samples > 0:
                    detected_by_gene[gene] = f"{positive_samples}/{total_samples} ({positive_samples/total_samples*100:.1f}%)"
            
            if detected_by_gene:
                print(f"    Individual gene detection rates:")
                for gene, rate in detected_by_gene.items():
                    print(f"      {gene}: {rate}")
    else:
        # If no parameter grouping, show overall statistics
        total_samples = len(df_all)
        clbB_positive = df_all['pks_positive_clbB'].sum()
        cluster_positive = df_all['pks_positive_cluster'].sum()
        
        print(f"\n  Overall Statistics:")
        print(f"    Total samples: {total_samples}")
        print(f"    Positive by clbB criterion: {clbB_positive}/{total_samples} samples ({clbB_positive/total_samples*100:.1f}%)")
        print(f"    Positive by cluster criterion: {cluster_positive}/{total_samples} samples ({cluster_positive/total_samples*100:.1f}%)")

print(f"\nAnalysis complete! Result file: {output_excel}")
print(f"\nFlexible pattern matching features:")
print(f"  - Supports multiple sequencing platforms (DRR, SRR, ERR, custom)")
print(f"  - Automatic detection of various file naming patterns")
print(f"  - Flexible FASTA file matching")
print(f"  - Robust parameter extraction from filenames")
print(f"\nLiterature-compliant analysis results:")
print(f"  - Enables comparison at different sequence identity thresholds")
print(f"  - Employs two determination criteria (clbB alone, entire cluster)")
print(f"  - Outputs detailed data including total read counts for each sample")
print(f"  - Data format suitable for ROC analysis and meta-analysis")
print(f"\nNote: Total read counts are retrieved from FASTA files.")
print(f"'N/A' is displayed when FASTA files are not found.")