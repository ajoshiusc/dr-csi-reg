# File Format Issues - Solutions

## 🔍 Problem Diagnosis

Your error shows file paths with spaces:
```
/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub8.mat
/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub6.mat
...
```

This suggests **TWO potential issues**:
1. **File paths with spaces** - shell/argument parsing problems
2. **MATLAB file format compatibility** - different .mat versions

## 🚀 Immediate Solutions

### **Option 1: Use the Batch Processing Script (Recommended)**
```bash
# Make scripts executable
chmod +x batch_process.sh

# Process all your files at once with proper space handling
./batch_process.sh \
  "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub8.mat" \
  "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub6.mat" \
  "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_patient2.mat" \
  "/deneb_disk/dr_csi_data/software compatible prostate data/data_sub1.mat" \
  "/deneb_disk/dr_csi_data/software compatible prostate data/data_patient1.mat"
```

### **Option 2: Process One File at a Time**
```bash
# Test with a single file first
python convert_mat_to_nifti.py \
  "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub8.mat" \
  "output_sub8_nifti"
```

### **Option 3: Copy Files to Path Without Spaces**
```bash
# Create working directory without spaces
mkdir -p /tmp/dr_csi_working
cp "/deneb_disk/dr_csi_data/software compatible prostate data/"*.mat /tmp/dr_csi_working/

# Process from the space-free path
cd /tmp/dr_csi_working
for file in *.mat; do
  echo "Processing: $file"
  python /path/to/dr-csi-reg/convert_mat_to_nifti.py "$file" "${file%.mat}_nifti"
done
```

## 🔧 Format Compatibility Fixes

### **Test File Format Compatibility**
```bash
# Run our diagnostic script
python quick_test_mat.py "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub8.mat"
```

### **If Files are HDF5 Format (.mat v7.3)**
```bash
# Install h5py if needed
pip install h5py

# The updated scripts now handle HDF5 automatically
```

### **If Files Have Format Issues**
```bash
# Convert to compatible format
python fix_mat_format.py \
  "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub8.mat" \
  "data_wip_sub8_compatible.mat"
```

## 📋 Step-by-Step Troubleshooting

### **Step 1: Test File Access**
```bash
# Check if files exist and are readable
ls -la "/deneb_disk/dr_csi_data/software compatible prostate data/"*.mat
```

### **Step 2: Test Single File Processing**
```bash
# Try the most basic conversion
python convert_mat_to_nifti.py \
  "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub8.mat" \
  "test_output"
```

### **Step 3: Check Python Environment**
```bash
# Verify all required packages
python -c "import scipy.io, nibabel, SimpleITK; print('All packages OK')"
```

### **Step 4: Run Diagnostic**
```bash
# Run comprehensive diagnostic
chmod +x diagnose_hpc_files.sh
./diagnose_hpc_files.sh
```

## 🎯 Most Likely Solution

Based on the error pattern, try this first:

```bash
# Use the HPC-specific processing script
chmod +x process_hpc_files.sh
./process_hpc_files.sh
```

This script:
- ✅ Handles file paths with spaces correctly
- ✅ Processes all your specific files
- ✅ Uses the robust format handling
- ✅ Creates organized output directories

## 📞 If Issues Persist

1. **Run the diagnostic**: `python quick_test_mat.py`
2. **Check the exact error message** when running single file conversion
3. **Verify MATLAB version** used to create the .mat files
4. **Consider file permissions** on the HPC system

The updated conversion scripts now handle:
- ✅ MATLAB v5, v7, and v7.3 (HDF5) formats
- ✅ Different data field names ('data', 'Data', 'img')
- ✅ File paths with spaces
- ✅ Robust error handling and fallback methods