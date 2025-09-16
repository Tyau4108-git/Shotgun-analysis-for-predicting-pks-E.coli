# clb Gene Analysis Manual

A step-by-step guide for quantitative analysis of clb gene clusters from colibactin-producing bacteria (pks+ E. coli) using shotgun metagenomic sequencing data

## 🎯 What This Manual Accomplishes

1. Prepare gut microbiome DNA sequence data (FASTQ files)
2. Perform sequence alignment (BLAST search) against 19 clb genes (clbA–clbS)
3. Quantify the abundance of each gene and determine pks+ E. coli carriage status
4. Compare results using multiple criteria (single gene vs. entire cluster)

## 🛠️ Required Software

### Essential Requirements
- **BLAST+** (version 2.16.0 or later recommended) - DNA sequence search tool
- **Python 3.6 or later** - For script execution
- **Terminal/Command Prompt** - Tool for direct computer command input

### Python Libraries
```bash
pip install pandas openpyxl
```

### Optional but Helpful
- **bunzip2/gunzip** - Tools for decompressing files

## 📋 Prerequisites

### Download Files from GitHub

Please download the following files from this repository:

1. **fastq_to_fasta.py** - FASTQ to FASTA conversion script
2. **fastaseq.py** - FASTA sequence processing script
3. **BlastDB(for loop).sh** - BLAST database construction and search script
4. **clb_genes.fna** - clb gene reference sequence file (19 genes)
5. **Countlead(for loop).py** - Results aggregation script

### Required Files
- **Metagenomic data** (FASTQ files)
  - Example: `sample_1.fastq` (forward reads)
  - Example: `sample_2.fastq` (reverse reads)

> **💡 File Format Explanation**
> - **FASTQ**: Raw data output from sequencing machines. Contains DNA sequences and their quality information
> - **FASTA**: Simple format containing only DNA sequences. Lines starting with `>` are sequence names, followed by the sequence

## Step 1: Environment Verification and Setup

### 1.1 Verify Your Computer Environment

**For Windows users:**
```
- Search for "cmd" or "PowerShell" from the Start menu
- This is your "terminal"
```

**For Mac users:**
```
- Use Spotlight search (Cmd + Space) and type "terminal"
- Open the "Terminal" application
```

**For Linux users:**
```
- Press Ctrl + Alt + T to open terminal
```

### 1.2 Practice Basic Terminal Commands

First, try the following commands:

```bash
# Display current location (directory)
pwd

# List files in current directory
ls

# Create a new folder
mkdir clb_analysis

# Move to the created folder
cd clb_analysis

# Verify current location
pwd
```

> **💡 Explanation**
> - `pwd`: "print working directory" - shows current location
> - `ls`: "list" - displays files and folders
> - `mkdir`: "make directory" - creates new folder
> - `cd`: "change directory" - moves to specified folder

### 1.3 BLAST+ Installation

#### For Windows
1. Open [NCBI BLAST+ download page](https://blast.ncbi.nlm.nih.gov/doc/blast-help/downloadblastdata.html)
2. Download the latest version from the "Windows" section
3. Run the downloaded file to install

#### For Mac
1. Open [NCBI BLAST+ download page](https://blast.ncbi.nlm.nih.gov/doc/blast-help/downloadblastdata.html)
2. Download the file matching your Mac's CPU:
   - Intel Mac: `x64-macosx.tar.gz`
   - Apple M1/M2 Mac: `arm64-macosx.tar.gz`

```bash
# Extract downloaded file (example)
tar xvfz ncbi-blast-2.16.0+-x64-macosx.tar.gz
```

### 1.4 Installation Verification

```bash
blastn -version
```

**Success example:**
```
Package: blast 2.16.0, build Jun 25 2024 11:53:51
```

**If errors occur:**
- PATH configuration may be required
- Administrator privileges may be needed for installation

### 1.5 Python Library Installation

```bash
pip install pandas openpyxl
```

## Step 2: Working Directory Preparation

### 2.1 Directory Structure Creation

```bash
# Create analysis folder
mkdir clb_analysis
cd clb_analysis

# Create necessary subfolders
mkdir data
mkdir scripts
mkdir results
mkdir references
```

### 2.2 File Placement

```bash
# Place downloaded scripts in scripts folder
cp fastq_to_fasta.py scripts/
cp fastaseq.py scripts/
cp "BlastDB(for loop).sh" scripts/
cp "Countlead(for loop).py" scripts/

# Place reference sequence file in references folder
cp clb_genes.fna references/

# Place your metagenomic data in data folder
cp your_sample_1.fastq data/
cp your_sample_2.fastq data/
```

## Step 3: Script Configuration

### 3.1 Required Configuration Areas in Each Script

Each script has a clearly marked "**User Configuration Area**" where paths must be modified.

#### fastq_to_fasta.py Configuration

Open the script in a text editor and modify the following section:

```python
# ===== User Configuration Area =====
# Input directory (where FASTQ files are located) - Required modification
input_dir = "/path/to/your/fastq/files"  # ← Modify this

# Output base directory - Required modification
output_base_dir = "/path/to/output/directory"  # ← Modify this
# ===== End User Configuration Area =====
```

#### fastaseq.py Configuration

```python
# ===== User Configuration Area =====
# Folder containing target DRR files - Required modification
folder = "/path/to/your/fasta/folder"  # ← Modify this

# DRR number - Required modification
drr = "DRR123456"  # ← Modify this (example: DRR171459)

# Output folder for combined files - Required modification
output_folder = "/path/to/output/folder"  # ← Modify this
# ===== End User Configuration Area =====
```

#### BlastDB(for loop).sh Configuration (Important: Research Parameter Adjustment)

```bash
# ===== User Configuration Area =====
# 1. BLAST executable directory - Required modification
blast_dir="/path/to/blast/bin"

# 2. Input file directory - Required modification
input_dir="/path/to/combined/fasta/files"

# 3. Query file specification - Required modification
query_file="/path/to/clb_genes.fna"

# 4. BLAST DB and output file destination - Required modification
blast_db_folder="/path/to/blast/output"

# 5. BLAST search parameter settings - Adjust according to research purpose
# Sequence identity threshold (%)
PERC_IDENTITY=97  # ← Set to 60, 70, 80, 90, 97 etc. according to research

# E-value threshold
EVALUE=1e-5  # ← Paper-compliant setting

# Maximum target sequences
MAX_TARGET_SEQS=10000000

# Number of threads
NUM_THREADS=2
# ===== End User Configuration Area =====
```

> **🔬 Important Notes for Researchers**
> 
> **Sequence Identity Selection Guidelines:**
> - **60-70%**: Detect more diverse sequence variants (sensitivity-focused)
> - **80-90%**: Balanced detection (recommended setting)
> - **95-97%**: High specificity detection (specificity-focused)
> 
> **The paper evaluated performance at 60%, 70%, 80%, and 90%**, and we recommend selecting from these values according to research objectives.

#### Countlead(for loop).py Configuration

```python
# ===== User Configuration Area =====
# Input directory path - Required modification
input_dir = "/path/to/blast/results"

# Output Excel file path - Required modification
output_excel = "/path/to/output/clb_counts.xlsx"

# Whether to output parameter-specific results (True/False)
SEPARATE_BY_PARAMETERS = True  # ← For sequence identity comparison
# ===== End User Configuration Area =====
```

## Step 4: FASTQ to FASTA Conversion

### 4.1 Why Conversion is Necessary

**FASTQ format example:**
```
@sequence_ID
ATGCGATCGATCGATCG
+
IIIIIIIIIIIIIIIII
```

**FASTA format example:**
```
>sequence_ID
ATGCGATCGATCGATCG
```

### 4.2 Script Execution

```bash
python scripts/fastq_to_fasta.py
```

## Step 5: FASTA Sequence Processing

### 5.1 Paired-Read Merging

```bash
python scripts/fastaseq.py
```

## Step 6: BLAST Database Construction and Search

### 6.1 Important: Research Parameter Settings

Based on the paper's research results, we recommend the following parameter settings:

| Parameter | Recommended Value | Description | Research Findings |
|-----------|------------------|-------------|-------------------|
| Sequence Identity | 60-90% | Adjust according to research purpose | Good performance at 70-90% |
| E-value | 1e-5 | Statistical significance | Paper-compliant setting |
| Maximum Targets | 10,000,000 | Allow massive hits | Required for comprehensive search |

### 6.2 Script Execution

```bash
# Grant execution permission
chmod +x scripts/"BlastDB(for loop).sh"

# Execute script
bash scripts/"BlastDB(for loop).sh"
```

### 6.3 Comparative Execution with Multiple Parameters (Recommended)

To enhance research validity, we recommend executing analysis with multiple sequence identity thresholds:

```bash
# Execute at 60%
# Change PERC_IDENTITY=60 in script and execute
bash scripts/"BlastDB(for loop).sh"

# Execute at 70%
# Change PERC_IDENTITY=70 in script and execute
bash scripts/"BlastDB(for loop).sh"

# Execute at 80%
# Change PERC_IDENTITY=80 in script and execute
bash scripts/"BlastDB(for loop).sh"

# Execute at 90%
# Change PERC_IDENTITY=90 in script and execute
bash scripts/"BlastDB(for loop).sh"
```

## Step 7: Results Aggregation

### 7.1 Aggregation Script Execution

```bash
python scripts/"Countlead(for loop).py"
```

### 7.2 Output File Format

The generated Excel file contains the following information:

#### Basic Information
| Column | Content | Description |
|--------|---------|-------------|
| Sample | Sample ID | DRR number, etc. |
| Identity_Threshold | Sequence identity | 60%, 70%, 80%, 90%, etc. |
| E_value | E-value threshold | Statistical significance setting |
| Total_reads | Total read count | Total reads per sample (from FASTA file) |

#### clb Gene-Specific Read Counts
| Column | Content | Description |
|--------|---------|-------------|
| clbA–clbS | Read count per gene | Each of 19 clb genes |
| Total_clb_reads | Total clb read count | Abundance of entire cluster |
| Detected_genes_count | Number of detected genes | Detection count out of 19 genes |

#### pks+ E. coli Determination Results
| Column | Content | Description |
|--------|---------|-------------|
| pks_positive_clbB | clbB-based determination | Single gene marker |
| pks_positive_cluster | Cluster-based determination | Nooij et al. method |

> **💡 About Total Read Count Acquisition**
> 
> Total read counts for each sample are automatically obtained from corresponding FASTA files (e.g., `DRR123456.fa`).
> If FASTA files are not found, "N/A" is displayed.
> Please correctly set the `fasta_dir` parameter in script configuration.

## Step 8: Results Interpretation

### 8.1 Criteria Selection Guidelines

**Recommendations based on paper research results:**

#### Single Gene Marker (clbB)
- **AUC: 0.826** - High discriminatory performance
- **Advantages**: High computational efficiency, simple execution
- **Applications**: Rapid screening of large datasets

#### Entire Cluster (19 gene sum)
- **AUC: 0.838** - Highest discriminatory performance
- **Advantages**: Robustness against gene deletions, biological validity
- **Applications**: Detailed functional analysis, research paper reporting

### 8.2 Impact of Sequence Identity

**Research-based findings:**
- **60-70%**: High sensitivity but risk of false positives
- **80-90%**: Balanced performance (recommended)
- **95% or higher**: High specificity but risk of missing novel variants

### 8.3 Application to Statistical Analysis

**Utilizing normalized quantitative values:**
```
RPM (Reads Per Million) = (clb gene read count / total read count) × 1,000,000
```

**ROC analysis thresholds (from paper):**
- clbB alone: 0.0166 RPM
- Entire cluster: 0.0124 RPM

## 📁 Directory Structure After Completion

```
clb_analysis/
├── data/
│   ├── your_sample_1.fastq
│   └── your_sample_2.fastq
├── scripts/
│   ├── fastq_to_fasta.py
│   ├── fastaseq.py
│   ├── BlastDB(for loop).sh
│   └── Countlead(for loop).py
├── references/
│   └── clb_genes.fna
└── results/
    ├── fasta_converted/
    ├── combined_fasta/
    ├── blast_results/
    │   ├── sample_identity60_evalue1e-5/
    │   ├── sample_identity70_evalue1e-5/
    │   ├── sample_identity80_evalue1e-5/
    │   └── sample_identity90_evalue1e-5/
    └── clb_counts_comparison.xlsx
```
---
