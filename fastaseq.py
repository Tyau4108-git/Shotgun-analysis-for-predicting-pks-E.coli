import os

def process_and_write_fasta(input_path, suffix, output_handle):
    """
    Read the specified FASTA file line by line.
    For header lines (lines starting with ">"), append ":{suffix}" to the end of the initial sequence ID portion and output.
    Output all other lines as is.
    """
    with open(input_path, 'r') as infile:
        for line in infile:
            if line.startswith('>'):
                # For header lines, extract only the first token and append :suffix to the end
                parts = line.strip().split(None, 1)  # Split the first token of the header from the rest
                header = parts[0]  # ID with ">"
                rest = parts[1] if len(parts) > 1 else ""
                new_header = f"{header}:{suffix}"
                if rest:
                    new_header += " " + rest
                output_handle.write(new_header + "\n")
            else:
                output_handle.write(line)

def combine_fasta_files(fasta1_path, fasta2_path, output_path):
    """
    Process FASTA files for _1 and _2 line by line,
    add ":1" for forward reads and ":2" for reverse reads, concatenate them, and write to output_path.
    """
    with open(output_path, 'w') as out_f:
        process_and_write_fasta(fasta1_path, 1, out_f)
        process_and_write_fasta(fasta2_path, 2, out_f)
    print(f"Concatenation completed: {output_path}")

# ===== User Configuration Area =====

# Folder containing target DRR files - Required modification
folder = "/path/to/your/fasta/folder"  # ← Please modify here

# DRR accession number - Required modification
drr = "DRR123456"  # ← Please modify here (e.g., DRR171459)

# Output folder for concatenated file - Required modification
output_folder = "/path/to/output/folder"  # ← Please modify here

# ===== End of User Configuration Area =====

# File path configuration (usually no modification needed)
fasta1_path = os.path.join(folder, f"{drr}_1.fa")
fasta2_path = os.path.join(folder, f"{drr}_2.fa")

# Create output folder if it does not exist
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, f"{drr}.fa")

print(f"FASTA Sequence Concatenation Script")
print(f"Target DRR accession: {drr}")
print(f"Input folder: {folder}")
print(f"Output folder: {output_folder}")
print("-" * 50)

# File existence check
if not os.path.exists(fasta1_path):
    print(f"Error: File not found: {fasta1_path}")
    print("Please check the folder and drr settings.")
    exit(1)

if not os.path.exists(fasta2_path):
    print(f"Error: File not found: {fasta2_path}")
    print("Please check the folder and drr settings.")
    exit(1)

# Execute concatenation process
print(f"Processing: {drr}")
print(f"  Input 1: {fasta1_path}")
print(f"  Input 2: {fasta2_path}")
print(f"  Output: {output_path}")

combine_fasta_files(fasta1_path, fasta2_path, output_path)