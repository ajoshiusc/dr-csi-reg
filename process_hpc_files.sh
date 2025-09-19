#!/bin/bash

# Process the specific files from your HPC system
# This script handles file paths with spaces properly

set -e

# Define your specific files with proper quoting
files=(
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub8.mat"
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub6.mat"
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_patient2.mat"
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_sub1.mat"
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_patient1.mat"
)

echo "========================================="
echo "Processing HPC Data Files"
echo "Starting at: $(date)"
echo "========================================="

# Check if files exist
echo "Checking file accessibility..."
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ Found: $(basename "$file")"
    else
        echo "❌ Missing: $file"
    fi
done

echo ""
read -p "Continue with batch processing? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled by user."
    exit 0
fi

# Make batch_process.sh executable
chmod +x batch_process.sh

# Run batch processing with proper quoting
echo "Starting batch processing..."
./batch_process.sh "${files[@]}"