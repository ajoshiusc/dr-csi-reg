# Spectral MRI Data Registration Module Documentation

**Part of the Diffusion-Relaxation Suite**

This repository contains a robust spectral MRI data registration module. The module includes three main components: conversion from .mat to NIfTI format, robust registration, and reverse conversion with complete metadata preservation.

## 🆕 Recent Major Improvements

- ✅ **Eliminated SimpleITK Registration Errors**: Fixed "All samples map outside moving image buffer" using center alignment
- ✅ **Enhanced Metadata Preservation**: All original .mat fields preserved in final output  
- ✅ **Race Condition Protection**: Thread-safe parallel processing with atomic file locking
- ✅ **Streamlined Registration**: Center alignment + PyTorch/MONAI (no more rigid registration failures)
- ✅ **GPU Memory Management**: Better CUDA device handling prevents conflicts

## Table of Contents

1. [Full Module Workflow Script](#full-module-workflow-script) - **Recommended Approach**
2. [spectral_mat_to_nifti.py](#spectral_mat_to_niftipy) - Forward Conversion (.mat → NIfTI)
3. [nifti_registration_pipeline.py](#nifti_registration_pipelinepy) - Enhanced Registration Module
4. [spectral_nifti_to_mat.py](#spectral_nifti_to_matpy) - Reverse Conversion (NIfTI → .mat)
5. [Installation & Setup](#installation--setup)
6. [Usage Examples](#usage-examples)

---

## Full Module Workflow Script

### Purpose
**Recommended approach**: Automated complete module workflow that handles all steps with proper error handling and monitoring.

### Key Features
- ✅ **Complete Automation**: Single command runs entire module workflow
- ✅ **Progress Monitoring**: Real-time progress updates and logging
- ✅ **Error Handling**: Validates each step before proceeding
- ✅ **Race Condition Protection**: Thread-safe parallel processing
- ✅ **Metadata Preservation**: Ensures all original fields are maintained

### Usage
```bash
# Run complete module workflow (recommended)
bash run_registration_module.sh <input_mat_file> <output_directory> [parallel_processes]

# Examples:
bash run_registration_module.sh data/patient1.mat results/patient1_output
bash run_registration_module.sh /path/to/data.mat /path/to/output 8

# Monitor progress in separate terminal
tail -f <output_directory>/registration_log.txt
```

### What It Does
1. Converts `data/data_wip_patient2.mat` → NIfTI files
2. Registers all files using enhanced registration module (center alignment + PyTorch/MONAI)  
3. Converts back to `.mat` preserving ALL original metadata fields
4. Generates comprehensive processing reports

---

## spectral_mat_to_nifti.py

### Purpose
Converts spectral .mat files to individual NIfTI files, with each spectral point saved as a separate 3D volume.

### Key Features
- ✅ **Automatic Resolution Reading**: Reads resolution directly from .mat file metadata
- ✅ **Spectral Dimension Handling**: Properly handles (N, X, Y, Z) spectral data format
- ✅ **PNG Visualizations**: Creates orthogonal slice visualizations for first 5 spectral points
- ✅ **Metadata Preservation**: Saves processing metadata and statistics
- ✅ **Error Handling**: Comprehensive validation and error reporting

### Command-Line Usage
```bash
# Basic usage - uses resolution from .mat file
python spectral_mat_to_nifti.py input_file.mat output_directory [--res x y z]

# Examples
python spectral_mat_to_nifti.py data_wip_patient2.mat patient2_nifti_spectral_output
python spectral_mat_to_nifti.py data_wip_patient2.mat custom_output/ --res 2.0 2.0 3.0

# Get help
python spectral_mat_to_nifti.py -h
```

**Arguments:**
- `input_file.mat` (required): Path to input .mat file containing spectral data
- `output_directory` (required): Output directory for NIfTI files
- `--res x y z` (optional): Custom voxel resolution in mm (overrides .mat file values)

### Function Signature
```python
def convert_spectral_mat_to_nifti(mat_file, output_dir, res=None):
    """
    Convert spectral format .mat file to individual NIfTI files
    
    Args:
        mat_file (str): Path to input .mat file
        output_dir (str): Directory to save NIfTI files
        res (list): Optional resolution override [x, y, z]
    
    Returns:
        dict: Conversion results with statistics
    """
```

### Output Files
- `spectral_point_000.nii.gz`, `spectral_point_001.nii.gz`, etc. - Individual spectral volumes
- `spectral_point_000.png` ... `spectral_point_004.png` - Visualization previews
- `spectral_metadata.txt` - Processing metadata and statistics

### Data Format Handling
- **Input**: .mat file with `data` array of shape (N, X, Y, Z)
- **Resolution**: Read from `resolution` field in .mat file, fallback to [1,1,1]
- **Output**: N individual NIfTI files with proper spatial resolution

---

## spectral_nifti_to_mat.py

### Purpose
Converts spectral NIfTI files back to the original .mat format with **complete metadata preservation**, enabling perfect round-trip conversion.

### 🆕 Enhanced Metadata Preservation
- ✅ **ALL Original Fields Preserved**: transform, spatial_dim, and any custom fields
- ✅ **Data Type Preservation**: Maintains original data types (uint16, float64, etc.) without conversion
- ✅ **Smart Resolution Handling**: Uses NIfTI spacing, preserves original resolution field
- ✅ **Perfect Round-Trip**: Exact reconstruction of original .mat structure with zero data loss
- ✅ **Flexible Input**: Works with registered or unregistered NIfTI files

### Key Features
- ✅ **Complete Field Preservation**: Preserves ALL fields from original .mat except 'data'
- ✅ **Data Type Preservation**: Maintains original data types (uint16, float64, etc.) exactly
- ✅ **Data Validation**: Comprehensive shape and format checking
- ✅ **Automatic Resolution**: Derives resolution from NIfTI file spacing
- ✅ **Fallback Handling**: Uses defaults when original metadata unavailable

### Command-Line Usage
```bash
# RECOMMENDED: With original file for complete metadata preservation
python spectral_nifti_to_mat.py input_directory output.mat original_input.mat

# Basic usage (loses some metadata)
python spectral_nifti_to_mat.py input_directory output.mat

# Examples
python spectral_nifti_to_mat.py \
    data/patient2_registration_output \
    data/final_registered.mat \
    data/data_wip_patient2.mat   # ← IMPORTANT for metadata preservation
```

**⚠️ Important**: Always provide the third argument (original .mat file) to preserve all metadata fields!

### Function Signature
```python
def convert_spectral_nifti_to_mat(nifti_dir, output_mat_file, original_mat_file=None):
    """
    Convert spectral NIfTI files back to the original .mat format
    
    Args:
        nifti_dir (str): Directory containing spectral_point_*.nii.gz files
        output_mat_file (str): Output .mat file path
        original_mat_file (str): Optional original .mat file for metadata comparison
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
```

### Output Format
- **Data Structure**: Reconstructed 4D array (N, X, Y, Z)
- **Resolution**: Derived from NIfTI spacing information
- **Metadata**: transform and spatial_dim preserved from original file

---

## nifti_registration_pipeline.py

### Purpose
**Enhanced registration module** with robust error handling, center alignment initialization, and race condition protection. Registers all files in a directory to a template using modern PyTorch/MONAI-based methods.

### 🆕 Major Improvements
- ✅ **Eliminated SimpleITK Errors**: No more "All samples map outside moving image buffer"
- ✅ **Center Alignment**: Better initialization using image center alignment
- ✅ **Race Condition Protection**: Atomic file locking prevents parallel processing conflicts
- ✅ **GPU Memory Management**: Smart CUDA device allocation
- ✅ **Robust Error Handling**: Graceful fallback mechanisms

### Registration Workflow
1. **Center Alignment**: Aligns image centers using SimpleITK transforms
2. **Affine Registration**: PyTorch/MONAI-based robust affine alignment
3. **Non-linear Registration**: PyTorch/MONAI-based deformable registration  
4. **Transformation Composition**: Combines all transforms for final output

### ⚠️ System Requirements
- **NVIDIA GPU with CUDA support** (recommended, falls back to CPU)
- **Processing time**: 3-4 hours for typical spectral datasets (31 files)
- **Memory requirements**: 8GB+ GPU memory recommended
- **System requirements**: 16GB+ RAM, ~5GB disk space for outputs
- **Parallel processes**: Use `--processes 4` (default, can be adjusted based on system resources)

### Key Features
- ✅ **Auto-Template Selection**: Automatically selects central file when none specified
- ✅ **Generic File Support**: Works with any NIfTI files (not spectral-specific)
- ✅ **Thread-Safe Processing**: Atomic file operations prevent race conditions
- ✅ **Comprehensive Reporting**: Detailed success/failure tracking with metadata
- ✅ **Smart File Filtering**: Excludes already processed `.reg.nii.gz` files
- ✅ **GPU Fallback**: Automatic CPU fallback if CUDA unavailable

### Command-Line Usage
```bash
# Recommended usage (single process for GPU systems)
python nifti_registration_pipeline.py input_dir output_dir --processes 4

# With custom template
python nifti_registration_pipeline.py input_dir output_dir \
    --template custom_template.nii.gz \
    --processes 4

# Custom file pattern
python nifti_registration_pipeline.py input_dir output_dir \
    --pattern "spectral_point_0*.nii.gz" \
    --processes 4

# Example with spectral data
python nifti_registration_pipeline.py \
    data/patient2_nifti_output \
    data/patient2_registration_output \
    --processes 4
```

### Arguments
- `input_dir`: Directory containing input NIfTI files
- `output_dir`: Output directory for registered files
- `--template`: Template NIfTI file (if not specified, uses central file from input directory)
- `--pattern`: File pattern to match (default: `*.nii.gz`)
- `--processes`: Number of parallel processes (default: 4)

### Function Signatures
```python
def register_nifti_directory(input_dir, template, output_dir, 
                           file_pattern="*.nii.gz", num_processes=4):
    """
    Register all NIfTI files in a directory to a template
    
    Args:
        input_dir (str): Directory containing input NIfTI files
        template (str or None): Template file (None = auto-select central file)
        output_dir (str): Output directory for registered files
        file_pattern (str): Pattern to match input files (default: "*.nii.gz")
        num_processes (int): Number of parallel processes (default: 4)
        
    Returns:
        dict: Processing results with statistics and file details
    """

def register_single_nifti_file(args):
    """
    Register a single NIfTI file to a template
    
    Args:
        args (tuple): (input_file, template, output_file)
    
    Returns:
        dict: Registration result with success status and message
    """
```

### Output Files
- `original_name.reg.nii.gz` for each input file
- `registration_metadata.txt` with detailed processing report

### Auto-Template Selection
When no template is specified:
1. Finds all matching NIfTI files
2. Sorts them alphabetically
3. Selects the middle file (e.g., file 16 of 31)
4. Uses this as the template for all registrations

### Example Output
```
=== Generic NIfTI Registration Processing ===
Input directory: patient2_nifti_spectral_output
Template file: Auto-select (central file from input directory)
Output directory: patient2_registration_output
File pattern: *.nii.gz
Parallel processes: 4

Processing registration for files in patient2_nifti_spectral_output...
Auto-selected template: spectral_point_015.nii.gz
  (File 16 of 31 sorted files)
Found 31 input files to process
Template: patient2_nifti_spectral_output/spectral_point_015.nii.gz
Using 4 parallel processes

✅ Successfully registered: spectral_point_000.reg.nii.gz
✅ Successfully registered: spectral_point_001.reg.nii.gz
...
```

---

## Installation & Setup

### Prerequisites
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install required packages
pip install scipy nibabel nilearn SimpleITK numpy matplotlib opencv-python
```

### Dependencies
- **scipy**: MATLAB file I/O
- **nibabel/nilearn**: NIfTI processing and visualization
- **SimpleITK**: Medical image I/O and processing
- **numpy**: Array operations
- **matplotlib**: Plotting for visualizations
- **opencv-python**: Image processing for visualizations

---

## Usage Examples

### Complete Workflow Example
```bash
# 1. Convert .mat to NIfTI files
python spectral_mat_to_nifti.py data_wip_patient2.mat patient2_nifti_spectral_output
# Output: 31 spectral NIfTI files + visualizations

# 2. Register all files to central template
python nifti_registration_pipeline.py \
    patient2_nifti_spectral_output \
    patient2_registration_output \
    --processes 4
# Output: 31 registered .reg.nii.gz files

# 3. Convert back to .mat format (optional verification)
python spectral_nifti_to_mat.py patient2_nifti_spectral_output reconstructed.mat data_wip_patient2.mat
# Output: reconstructed .mat file
```

### Custom Resolution Example
```python
# Use programmatically with custom resolution
from spectral_mat_to_nifti import convert_spectral_mat_to_nifti

result = convert_spectral_mat_to_nifti(
    "input_data.mat", 
    "output_directory",
    res=[2.3, 2.3, 5.0]  # Custom resolution
)
```

### Batch Processing Example
```python
# Register multiple directories
from nifti_registration_pipeline import register_nifti_directory

for subject in ["subject1", "subject2", "subject3"]:
    results = register_nifti_directory(
        f"{subject}_nifti_output",
        template=None,  # Auto-select
        output_dir=f"{subject}_registration_output",
        num_processes=8
    )
    print(f"Subject {subject}: {results['successful']} files registered")
```

---

## Error Handling & Troubleshooting

### Common Issues
1. **File Not Found**: Verify input paths and file existence
2. **Memory Issues**: Reduce number of parallel processes
3. **CUDA Errors**: Set device='cpu' in registration functions
4. **Format Errors**: Ensure .mat files contain 'data' array with correct shape

### Validation
All functions include comprehensive error handling:
- File existence validation
- Data format verification
- Shape and dimension checking
- Memory and processing error catching

---

## Architecture Notes

### Design Principles
- **Single Responsibility**: Each script has one clear purpose
- **Professional Naming**: Functions use descriptive, professional names
- **Clean Interfaces**: Functions can be imported and used programmatically
- **Comprehensive Logging**: Detailed status and error reporting
- **Flexible Configuration**: Command-line arguments and function parameters
- **Data Integrity**: Careful handling of medical imaging data formats

### File Naming Conventions
- Input files: Original names from .mat files
- Spectral files: `spectral_point_XXX.nii.gz` (zero-padded 3 digits)
- Registered files: `original_name.reg.nii.gz`
- Metadata files: `*_metadata.txt`

<<<<<<< HEAD
### Function Naming Conventions
- **convert_**: Functions that transform data between formats
- **register_**: Functions that perform image registration
- **perform_**: Functions that execute core algorithms
- Descriptive names that clearly indicate purpose and scope
=======
>>>>>>> 72f2a45e84f2d49749850497bba2559581fda6aa
