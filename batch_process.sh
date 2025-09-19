#!/bin/bash

# Batch DR-CSI Registration Pipeline
# Processes multiple .mat files in parallel

set -e

# Print usage if no arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <mat_file1> [mat_file2] [mat_file3] ..."
    echo ""
    echo "Example:"
    echo "  $0 \"/path/to/data_patient1.mat\" \"/path/to/data_patient2.mat\""
    echo ""
    echo "This script will:"
    echo "  1. Process each .mat file through the full DR-CSI module workflow"
    echo "  2. Create separate output directories for each file"
    echo "  3. Generate final reconstructed .mat files"
    echo ""
    exit 1
fi

# Configuration
PARALLEL_PROCESSES=4
BASE_OUTPUT_DIR="batch_output_$(date +%Y%m%d_%H%M%S)"

echo "========================================="
echo "DR-CSI Batch Registration Module (Diffusion-Relaxation Suite)"
echo "Starting at: $(date)"
echo "========================================="
echo "Number of files to process: $#"
echo "Output directory: $BASE_OUTPUT_DIR"
echo "Parallel processes: $PARALLEL_PROCESSES"
echo ""

# Create base output directory
mkdir -p "$BASE_OUTPUT_DIR"

# Function to process a single file
process_file() {
    local input_file="$1"
    local file_num="$2"
    local total_files="$3"
    
    # Extract filename without path and extension for output naming
    local basename=$(basename "$input_file" .mat)
    local output_dir="$BASE_OUTPUT_DIR/${basename}"
    
    echo "[$file_num/$total_files] Processing: $input_file"
    echo "Output directory: $output_dir"
    
    # Create output subdirectories
    mkdir -p "$output_dir"
    local nifti_dir="$output_dir/nifti"
    local registration_dir="$output_dir/registration"
    local final_mat="$output_dir/${basename}_reconstructed.mat"
    
    # Check if input file exists
    if [ ! -f "$input_file" ]; then
        echo "ERROR: Input file not found: $input_file"
        return 1
    fi
    
    # Step 1: Convert .mat to NIfTI
    echo "[$file_num/$total_files] Step 1: Converting .mat to NIfTI..."
    if ! python convert_mat_to_nifti.py "$input_file" "$nifti_dir"; then
        echo "ERROR: .mat to NIfTI conversion failed for $input_file"
        return 2
    fi
    
    # Check NIfTI files were created
    local nifti_count=$(ls -1 "$nifti_dir"/*.nii.gz 2>/dev/null | wc -l)
    if [ "$nifti_count" -eq 0 ]; then
        echo "ERROR: No NIfTI files created for $input_file"
        return 3
    fi
    echo "[$file_num/$total_files] Created $nifti_count NIfTI files"
    
    # Step 2: Register NIfTI files
    echo "[$file_num/$total_files] Step 2: Registering NIfTI files..."
    if ! python register_nifti.py "$nifti_dir" "$registration_dir" --processes "$PARALLEL_PROCESSES"; then
        echo "ERROR: Registration failed for $input_file"
        return 4
    fi
    
    # Check registered files were created
    local reg_count=$(ls -1 "$registration_dir"/*.reg.nii.gz 2>/dev/null | wc -l)
    echo "[$file_num/$total_files] Registered $reg_count files"
    
    # Step 3: Convert back to .mat
    echo "[$file_num/$total_files] Step 3: Converting back to .mat..."
    if ! python convert_nifti_to_mat.py "$registration_dir" "$final_mat" "$input_file"; then
        echo "ERROR: NIfTI to .mat conversion failed for $input_file"
        return 5
    fi
    
    # Verify final output
    if [ -f "$final_mat" ]; then
        local file_size=$(du -h "$final_mat" | cut -f1)
        echo "[$file_num/$total_files] ✅ SUCCESS: $final_mat (size: $file_size)"
    else
        echo "[$file_num/$total_files] ❌ ERROR: Final output not created"
        return 6
    fi
    
    return 0
}

# Export function for parallel execution
export -f process_file
export BASE_OUTPUT_DIR
export PARALLEL_PROCESSES

# Create array of all input files
input_files=()
for file in "$@"; do
    input_files+=("$file")
done

# Process files sequentially (to avoid GPU conflicts)
# Note: Each file uses parallel processing internally for registration
total_files=${#input_files[@]}
success_count=0
error_count=0

for i in "${!input_files[@]}"; do
    file_num=$((i + 1))
    echo ""
    echo "========================================="
    echo "Processing file $file_num of $total_files"
    echo "========================================="
    
    if process_file "${input_files[$i]}" "$file_num" "$total_files"; then
        ((success_count++))
    else
        ((error_count++))
        echo "❌ Failed to process: ${input_files[$i]}"
    fi
done

# Final summary
echo ""
echo "========================================="
echo "BATCH PROCESSING COMPLETE"
echo "========================================="
echo "Total files processed: $total_files"
echo "Successful: $success_count"
echo "Failed: $error_count"
echo "Output directory: $BASE_OUTPUT_DIR"
echo "Completed at: $(date)"

# List all output files
echo ""
echo "Output files created:"
find "$BASE_OUTPUT_DIR" -name "*_reconstructed.mat" -type f | sort

if [ $error_count -gt 0 ]; then
    echo ""
    echo "⚠️  Some files failed to process. Check the error messages above."
    exit 1
else
    echo ""
    echo "🎉 All files processed successfully!"
    exit 0
fi