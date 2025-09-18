import os
import bz2
import gzip
import re
from pathlib import Path

def process_fastq_content(fastq_content, fasta_file):
    """
    Convert FASTQ content to FASTA file
    
    Args:
        fastq_content: FASTQ file content (string iterator)
        fasta_file (str): Output FASTA file path
    """
    with open(fasta_file, 'w') as fa:
        lines = []
        for line in fastq_content:
            # Decode if bytes
            if isinstance(line, bytes):
                line = line.decode('utf-8')
            lines.append(line.strip())
            
            if len(lines) == 4:
                header = lines[0]
                seq = lines[1]
                # lines[2] is the + line
                # lines[3] is the quality score line
                
                if header.startswith('@'):
                    fa.write(f">{header[1:]}\n{seq}\n")
                
                lines = []

def process_compressed_fastq(input_file, output_file):
    """
    Convert compressed FASTQ files (.bz2, .gz) to FASTA
    
    Args:
        input_file (str): Input file path
        output_file (str): Output FASTA file path
    """
    print(f"Processing: {os.path.basename(input_file)}")
    
    if input_file.endswith('.bz2'):
        with bz2.open(input_file, 'rt') as f:
            process_fastq_content(f, output_file)
    elif input_file.endswith('.gz'):
        with gzip.open(input_file, 'rt') as f:
            process_fastq_content(f, output_file)
    else:
        with open(input_file, 'r') as f:
            process_fastq_content(f, output_file)
    
    print(f"  → Conversion completed: {os.path.basename(output_file)}")

def extract_drr_number(filename):
    """
    Extract DRR number from filename
    
    Args:
        filename (str): Filename
        
    Returns:
        str: DRR number (e.g., "DRR171459")
    """
    match = re.search(r'(DRR\d{6})', filename)
    return match.group(1) if match else None

def process_dra_directory(input_dir, output_base_dir):
    """
    Process DRA directory and create directories for each DRR number with FASTA conversion
    
    Args:
        input_dir (str): Input directory path (directory containing FASTQ files)
        output_base_dir (str): Output base directory path
    """
    # Create output directory
    os.makedirs(output_base_dir, exist_ok=True)
    
    # Group files by DRR number
    drr_files = {}
    
    # Supported extensions
    supported_extensions = ('.fastq', '.fq', '.fastq.bz2', '.fq.bz2', '.fastq.gz', '.fq.gz')
    
    # Scan files and group by DRR number
    for file in os.listdir(input_dir):
        if any(file.endswith(ext) for ext in supported_extensions):
            drr_number = extract_drr_number(file)
            if drr_number:
                if drr_number not in drr_files:
                    drr_files[drr_number] = []
                drr_files[drr_number].append(file)
    
    # Process files for each DRR number
    total_files = 0
    for drr_number, files in sorted(drr_files.items()):
        print(f"\nProcessing DRR number: {drr_number}")
        print(f"  Number of files: {len(files)}")
        
        # Create directory for DRR number
        drr_output_dir = os.path.join(output_base_dir, drr_number)
        os.makedirs(drr_output_dir, exist_ok=True)
        
        # Convert each file
        for file in sorted(files):
            input_path = os.path.join(input_dir, file)
            
            # Determine output filename (remove compression extension then change to .fa)
            base_name = file
            for ext in ('.bz2', '.gz'):
                if base_name.endswith(ext):
                    base_name = base_name[:-len(ext)]
            
            if base_name.endswith('.fastq'):
                output_name = base_name.replace('.fastq', '.fa')
            elif base_name.endswith('.fq'):
                output_name = base_name.replace('.fq', '.fa')
            else:
                output_name = base_name + '.fa'
            
            output_path = os.path.join(drr_output_dir, output_name)
            
            # Convert file
            process_compressed_fastq(input_path, output_path)
            total_files += 1
    
    print(f"\nProcessing completed:")
    print(f"  Total number of DRR numbers: {len(drr_files)}")
    print(f"  Total number of converted files: {total_files}")
    print(f"  Output directory: {output_base_dir}")

def main():
    """
    Main execution function
    """
    # ===== User Configuration Area =====
    # Input directory (location of FASTQ files) - Required modification
    input_dir = "/path/to/your/fastq/files"  # ← Please modify here
    
    # Output base directory - Required modification
    output_base_dir = "/path/to/output/directory"  # ← Please modify here
    # ===== End of User Configuration Area =====

    print(f"FASTQ to FASTA Conversion Script")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_base_dir}")
    print("-" * 50)
    
    # Check directory existence
    if not os.path.exists(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        print("Please modify input_dir at the top of the script to the correct path.")
        return
    
    # Confirm processing
    response = input("\nDo you want to start processing? (y/n): ")
    if response.lower() != 'y':
        print("Processing cancelled.")
        return
    
    # Execute processing
    process_dra_directory(input_dir, output_base_dir)

if __name__ == "__main__":
    main()