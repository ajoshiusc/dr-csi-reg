#!/bin/bash

# DR-CSI Registration Module Runner
# Part of the Diffusion-Relaxation Suite
# Runs the complete registration module workflow with parallel processing

# Function to show usage
show_usage() {
    echo "========================================="
    echo "DR-CSI Registration Module Runner"
    echo "Part of the Diffusion-Relaxation Suite"
    echo "========================================="
    echo ""
    echo "Usage: $0 <input_mat_file> <output_directory> [parallel_processes]"
    echo ""
    echo "Arguments:"
    echo "  input_mat_file      Path to input .mat file"
    echo "  output_directory    Directory for all outputs (will be created)"
    echo "  parallel_processes  Number of parallel processes (default: 4)"
    echo ""
    echo "Examples:"
    echo "  $0 data/patient1.mat results/patient1_output"
    echo "  $0 /path/to/data.mat /path/to/output 8"
    echo ""
    echo "Output structure:"
    echo "  output_directory/"
    echo "  ├── nifti/                    # Converted NIfTI files"
    echo "  ├── registration/             # Registered NIfTI files"
    echo "  └── final_reconstructed.mat   # Final registered .mat file"
    echo ""
    echo "Requirements:"
    echo "  - NVIDIA GPU with CUDA support (for registration)"
    echo "  - 8GB+ GPU memory recommended"
    echo "  - 3-4 hours processing time for typical datasets"
    echo ""
}

# Check arguments
if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    show_usage
    exit 1
fi

# Parse arguments
INPUT_MAT="$1"
OUTPUT_BASE_DIR="$2"
PARALLEL_PROCESSES="${3:-4}"  # Default to 4 if not provided

# Validate parallel processes argument
if ! [[ "$PARALLEL_PROCESSES" =~ ^[0-9]+$ ]] || [ "$PARALLEL_PROCESSES" -lt 1 ] || [ "$PARALLEL_PROCESSES" -gt 16 ]; then
    echo "ERROR: parallel_processes must be a number between 1 and 16"
    echo "Got: $PARALLEL_PROCESSES"
    exit 1
fi

# Set up paths
NIFTI_OUTPUT="$OUTPUT_BASE_DIR/nifti"
REGISTRATION_OUTPUT="$OUTPUT_BASE_DIR/registration"
FINAL_MAT_OUTPUT="$OUTPUT_BASE_DIR/final_reconstructed.mat"

set -e
set -x  # Print each command before executing

# Print environment info
echo "========================================="
echo "DR-CSI Registration Module - Full Workflow (Diffusion-Relaxation Suite)"
echo "Starting at: $(date)"
echo "========================================="
echo "Input file: $INPUT_MAT"
echo "Output directory: $OUTPUT_BASE_DIR"
echo "Parallel processes: $PARALLEL_PROCESSES"
echo "Python version: $(python --version 2>&1)"
echo "Python executable: $(which python)"
echo "Current directory: $(pwd)"

# Validate input file
if [ ! -f "$INPUT_MAT" ]; then
    echo "ERROR: Input .mat file not found: $INPUT_MAT"
    exit 1
fi

# Create output directory structure
echo "Setting up output directories..."
mkdir -p "$OUTPUT_BASE_DIR"
rm -rf "$NIFTI_OUTPUT" "$REGISTRATION_OUTPUT" "$FINAL_MAT_OUTPUT"

# Step 1: Convert .mat to NIfTI
echo ""
echo "Step 1: Converting .mat to NIfTI files..."
echo "----------------------------------------"
python convert_mat_to_nifti.py "$INPUT_MAT" "$NIFTI_OUTPUT"
if [ $? -ne 0 ]; then
    echo "ERROR: .mat to NIfTI conversion failed"
    exit 2
fi

# Check NIfTI output exists
if [ ! -d "$NIFTI_OUTPUT" ] || [ $(ls -1 "$NIFTI_OUTPUT"/*.nii.gz 2>/dev/null | wc -l) -eq 0 ]; then
    echo "ERROR: No NIfTI files created in $NIFTI_OUTPUT"
    exit 3
fi

# Step 2: Register NIfTI files
echo ""
echo "Step 2: Running NIfTI registration with $PARALLEL_PROCESSES parallel processes..."
echo "----------------------------------------"
echo "⚠️  WARNING: This step requires NVIDIA GPU and will take 3-4 hours!"
echo "⚠️  Starting registration at: $(date)"

python register_nifti.py "$NIFTI_OUTPUT" "$REGISTRATION_OUTPUT" --processes "$PARALLEL_PROCESSES"
if [ $? -ne 0 ]; then
    echo "ERROR: NIfTI registration failed"
    exit 4
fi

# Check registration output exists
if [ ! -d "$REGISTRATION_OUTPUT" ] || [ $(ls -1 "$REGISTRATION_OUTPUT"/*.nii.gz 2>/dev/null | wc -l) -eq 0 ]; then
    echo "ERROR: No registered NIfTI files created in $REGISTRATION_OUTPUT"
    exit 5
fi

# Step 3: Convert registered NIfTI back to .mat
echo ""
echo "Step 3: Converting registered NIfTI back to .mat..."
echo "----------------------------------------"
python convert_nifti_to_mat.py "$REGISTRATION_OUTPUT" "$FINAL_MAT_OUTPUT" "$INPUT_MAT"
if [ $? -ne 0 ]; then
    echo "ERROR: Registered NIfTI to .mat conversion failed"
    exit 6
fi

# Check final .mat output exists
if [ ! -f "$FINAL_MAT_OUTPUT" ]; then
    echo "ERROR: Final .mat file not created: $FINAL_MAT_OUTPUT"
    exit 7
fi

set +x

echo ""
echo "========================================="
echo "DR-CSI Registration Module - COMPLETE!"
echo "========================================="
echo "Input file: $INPUT_MAT"
echo "Output directory: $OUTPUT_BASE_DIR"
echo ""
echo "Generated outputs:"
echo "  - NIfTI files: $NIFTI_OUTPUT"
echo "  - Registered NIfTI: $REGISTRATION_OUTPUT"  
echo "  - Final reconstructed .mat: $FINAL_MAT_OUTPUT"
echo ""
echo "Final .mat file size: $(du -h "$FINAL_MAT_OUTPUT" | cut -f1)"
echo "Completed at: $(date)"
echo "========================================="
echo "Workflow completed successfully! 🎉"
