#!/bin/bash

# Full DR-CSI Registration Workflow Script
# Runs the complete pipeline with parallel registration

set -e
set -x  # Print each command before executing

# Print environment info
echo "========================================="
echo "DR-CSI Registration Pipeline - Full Workflow"
echo "Starting at: $(date)"
echo "========================================="
echo "Python version: $(python --version 2>&1)"
echo "Python executable: $(which python)"
echo "Current directory: $(pwd)"

# Configuration
INPUT_MAT="data/data_wip_patient2.mat"
NIFTI_OUTPUT="data/workflow_nifti"
REGISTRATION_OUTPUT="data/workflow_registration"
FINAL_MAT_OUTPUT="data/workflow_final_reconstructed.mat"
PARALLEL_PROCESSES=4  # Optimized for balanced parallel processing

# Clean up any previous runs
echo "Cleaning up previous workflow outputs..."
rm -rf "$NIFTI_OUTPUT" "$REGISTRATION_OUTPUT" "$FINAL_MAT_OUTPUT"

# Check input file exists
if [ ! -f "$INPUT_MAT" ]; then
    echo "ERROR: Input .mat file not found: $INPUT_MAT"
    exit 1
fi

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

echo "\n========================================="
echo "DR-CSI Registration Pipeline - COMPLETE!"
echo "Final outputs:"
echo "  - NIfTI files: $NIFTI_OUTPUT"
echo "  - Registered NIfTI: $REGISTRATION_OUTPUT"
echo "  - Final reconstructed .mat: $FINAL_MAT_OUTPUT"
echo "========================================="
echo "Workflow completed successfully! 🎉"
