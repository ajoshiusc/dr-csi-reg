#!/bin/bash

# Full DR-CSI Registration Workflow Script
# Runs the complete pipeline with parallel registration

set -e  # Exit on any error

echo "========================================="
echo "DR-CSI Registration Pipeline - Full Workflow"
echo "Starting at: $(date)"
echo "========================================="

# Configuration
INPUT_MAT="data/data_wip_patient2.mat"
NIFTI_OUTPUT="data/workflow_nifti"
REGISTRATION_OUTPUT="data/workflow_registration"
FINAL_MAT_OUTPUT="data/workflow_final_reconstructed.mat"
PARALLEL_PROCESSES=2

# Clean up any previous runs
echo "Cleaning up previous workflow outputs..."
rm -rf "$NIFTI_OUTPUT" "$REGISTRATION_OUTPUT" "$FINAL_MAT_OUTPUT"

echo ""
echo "Step 1: Converting .mat to NIfTI files..."
echo "----------------------------------------"
python convert_mat_to_nifti.py "$INPUT_MAT" "$NIFTI_OUTPUT"

if [ $? -eq 0 ]; then
    echo "✓ Successfully converted .mat to NIfTI files"
    echo "  Output directory: $NIFTI_OUTPUT"
    echo "  Number of files: $(ls -1 $NIFTI_OUTPUT/*.nii.gz 2>/dev/null | wc -l)"
else
    echo "✗ Failed to convert .mat to NIfTI files"
    exit 1
fi

echo ""
echo "Step 2: Running NIfTI registration with $PARALLEL_PROCESSES parallel processes..."
echo "----------------------------------------"
echo "⚠️  WARNING: This step requires NVIDIA GPU and will take 3-4 hours!"
echo "⚠️  Starting registration at: $(date)"

python register_nifti.py "$NIFTI_OUTPUT" "$REGISTRATION_OUTPUT" --processes "$PARALLEL_PROCESSES"

if [ $? -eq 0 ]; then
    echo "✓ Successfully completed NIfTI registration"
    echo "  Output directory: $REGISTRATION_OUTPUT"
    echo "  Registration completed at: $(date)"
else
    echo "✗ Failed to complete NIfTI registration"
    exit 1
fi

echo ""
echo "Step 3: Converting registered NIfTI back to .mat..."
echo "----------------------------------------"
python convert_nifti_to_mat.py "$REGISTRATION_OUTPUT" "$FINAL_MAT_OUTPUT" "$INPUT_MAT"

if [ $? -eq 0 ]; then
    echo "✓ Successfully converted registered NIfTI back to .mat"
    echo "  Output file: $FINAL_MAT_OUTPUT"
else
    echo "✗ Failed to convert registered NIfTI back to .mat"
    exit 1
fi

echo ""
echo "========================================="
echo "DR-CSI Registration Pipeline - COMPLETE!"
echo "Completed at: $(date)"
echo "========================================="
echo ""
echo "Final outputs:"
echo "  - NIfTI files: $NIFTI_OUTPUT"
echo "  - Registered NIfTI: $REGISTRATION_OUTPUT"
echo "  - Final reconstructed .mat: $FINAL_MAT_OUTPUT"
echo ""
echo "Workflow completed successfully! 🎉"
