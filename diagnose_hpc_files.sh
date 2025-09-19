#!/bin/bash

# Diagnostic script to identify issues with HPC file processing

echo "========================================="
echo "DR-CSI HPC File Diagnostic"
echo "========================================="

# The files you mentioned
files=(
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub8.mat"
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub6.mat"
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_patient2.mat"
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_sub1.mat"
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_patient1.mat"
)

echo "1. Checking file accessibility..."
echo "---------------------------------"
accessible_files=()
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        echo "✅ $file ($size)"
        accessible_files+=("$file")
    elif [ -e "$file" ]; then
        echo "⚠️  $file (exists but not a regular file)"
    else
        echo "❌ $file (not found)"
    fi
done

echo ""
echo "2. Checking directory permissions..."
echo "-----------------------------------"
base_dir="/deneb_disk/dr_csi_data/software compatible prostate data"
if [ -d "$base_dir" ]; then
    echo "✅ Base directory exists: $base_dir"
    echo "   Permissions: $(ls -ld "$base_dir" | cut -d' ' -f1)"
    echo "   Contents:"
    ls -la "$base_dir"/*.mat 2>/dev/null | head -10 || echo "   No .mat files found or permission denied"
else
    echo "❌ Base directory not found: $base_dir"
fi

echo ""
echo "3. Testing Python environment..."
echo "-------------------------------"
echo "Python version: $(python --version 2>&1)"
echo "Current directory: $(pwd)"

# Test import of required modules
echo "Testing Python modules..."
python -c "
import sys
import os
import scipy.io
import nibabel
import SimpleITK
print('✅ All required Python modules available')
" 2>/dev/null && echo "✅ Python environment OK" || echo "❌ Python module issues"

echo ""
echo "4. Testing file processing with first accessible file..."
echo "------------------------------------------------------"
if [ ${#accessible_files[@]} -gt 0 ]; then
    test_file="${accessible_files[0]}"
    echo "Testing with: $test_file"
    
    # Test loading the file
    echo "Testing .mat file loading..."
    python -c "
import scipy.io as sio
import sys
try:
    mat_file = sys.argv[1]
    print(f'Loading: {mat_file}')
    data = sio.loadmat(mat_file)
    print(f'✅ Successfully loaded .mat file')
    print(f'   Keys: {[k for k in data.keys() if not k.startswith(\"__\")]}')
    if 'data' in data:
        print(f'   Data shape: {data[\"data\"].shape}')
        print(f'   Data type: {data[\"data\"].dtype}')
    # Check for resolution field (new format first, then old format for compatibility)
    if 'resolution' in data:
        print(f'   Resolution: {data[\"resolution\"]}')
    elif 'Resolution' in data:
        print(f'   Resolution (old format): {data[\"Resolution\"]}')
    else:
        print('   Resolution: Not found')
except Exception as e:
    print(f'❌ Error loading file: {e}')
    sys.exit(1)
" "$test_file"
    
    if [ $? -eq 0 ]; then
        echo "✅ File processing test passed"
    else
        echo "❌ File processing test failed"
    fi
else
    echo "❌ No accessible files to test"
fi

echo ""
echo "5. Command line argument testing..."
echo "----------------------------------"
echo "Testing how arguments with spaces are handled:"
echo "Arguments received by this script: $#"
for i in $(seq 1 $#); do
    echo "  Arg $i: ${!i}"
done

echo ""
echo "6. Suggested solutions..."
echo "------------------------"
echo "Based on the diagnostic above, try one of these approaches:"
echo ""
echo "A. Use the batch processing script:"
echo "   ./batch_process.sh \\"
for file in "${files[@]}"; do
    echo "     \"$file\" \\"
done
echo ""
echo "B. Process files one at a time:"
echo "   for file in \\"
for file in "${files[@]}"; do
    echo "     \"$file\" \\"
done
echo "   do"
echo "     echo \"Processing: \$file\""
echo "     python convert_mat_to_nifti.py \"\$file\" \"output_\$(basename \"\$file\" .mat)\""
echo "   done"
echo ""
echo "C. Copy files to a path without spaces:"
echo "   mkdir -p /tmp/dr_csi_data"
echo "   cp \"/deneb_disk/dr_csi_data/software compatible prostate data/\"*.mat /tmp/dr_csi_data/"
echo "   # Then process from /tmp/dr_csi_data/"
echo ""
echo "D. Use the HPC-specific script:"
echo "   ./process_hpc_files.sh"