# Spectral Data Conversion Scripts Documentation

This repository contains three main scripts for processing spectral MRI data: conversion from .mat to NIfTI format, reverse conversion, and registration. All scripts are designed with clean architecture and modern Python practices.

## Table of Contents

1. [main_mat2nifti_spectral.py](#main_mat2nifti_spectralpy) - Forward Conversion (.mat → NIfTI)
2. [main_nifti2mat_spectral.py](#main_nifti2mat_spectralpy) - Reverse Conversion (NIfTI → .mat)
3. [main_register2template_enhanced.py](#main_register2template_enhancedpy) - Registration
4. [verify_roundtrip_conversion.py](#verify_roundtrip_conversionpy) - Verification
5. [Installation & Setup](#installation--setup)
6. [Usage Examples](#usage-examples)

---

## main_mat2nifti_spectral.py

### Purpose
Converts spectral MRI data from MATLAB .mat format to individual NIfTI files, where each spectral point becomes a separate 3D NIfTI volume.

### Data Format Support
- **Input**: .mat files with spectral data structure `(N, X, Y, Z)`
  - `N`: Number of spectral points (e.g., 31)
  - `X, Y, Z`: Spatial dimensions (e.g., 104×52×12)
- **Output**: N individual NIfTI files + visualizations + metadata

### Key Features
- ✅ **Automatic Resolution Reading**: Reads resolution from .mat file's `Resolution` field
- ✅ **Smart Fallbacks**: Uses provided parameters or defaults when needed
- ✅ **Proper Axis Handling**: Correctly transposes data for SimpleITK (z,y,x) ordering
- ✅ **Visualization**: Creates PNG previews of first 5 spectral points
- ✅ **Metadata Preservation**: Saves detailed processing information

### Required .mat File Structure
```python
{
    'data': numpy.ndarray,       # Shape: (spectral_points, x, y, z)
    'Resolution': numpy.ndarray, # Shape: (1, 3) - [x_res, y_res, z_res]
    'spatial_dim': numpy.ndarray # Optional: (1, 3) - [x_size, y_size, z_size]
}
```

### Function Signature
```python
def process_spectral_format(mat_file, output_dir, res=None):
    """
    Process spectral format .mat file
    
    Args:
        mat_file (str): Path to input .mat file
        output_dir (str): Output directory for NIfTI files
        res (list, optional): Override resolution [x, y, z] in mm
        
    Returns:
        int: Number of spectral points processed, or None if error
    """
```

### Output Files
- `spectral_point_000.nii.gz` through `spectral_point_N.nii.gz`
- `spectral_point_000.png` through `spectral_point_004.png` (visualizations)
- `spectral_metadata.txt` (processing details)

### Usage
```bash
# Basic usage (reads resolution from .mat file)
python main_mat2nifti_spectral.py

# Or import as module
python -c "from main_mat2nifti_spectral import process_spectral_format; 
           process_spectral_format('data.mat', 'output_dir')"
```

### Configuration
Edit the `__main__` section to modify:
```python
mat_file = "/path/to/your/data.mat"
output_dir = "/path/to/output/directory"
```

---

## main_nifti2mat_spectral.py

### Purpose
Performs reverse conversion from individual spectral NIfTI files back to the original .mat format, enabling round-trip data preservation.

### Key Features
- ✅ **Perfect Reconstruction**: Preserves exact data values and dimensions
- ✅ **Automatic File Detection**: Finds all `spectral_point_*.nii.gz` files
- ✅ **Resolution Preservation**: Reads spacing from NIfTI headers
- ✅ **Metadata Validation**: Compares with original file when available
- ✅ **Clean Output**: Creates properly formatted .mat file

### Function Signature
```python
def nifti_to_spectral_mat(nifti_dir, output_mat_file, original_mat_file=None):
    """
    Convert spectral NIfTI files back to .mat format
    
    Args:
        nifti_dir (str): Directory containing spectral_point_*.nii.gz files
        output_mat_file (str): Output .mat file path
        original_mat_file (str, optional): Original .mat file for comparison
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
```

### Output .mat Structure
```python
{
    'data': numpy.ndarray,       # Shape: (spectral_points, x, y, z)
    'Resolution': numpy.ndarray, # Shape: (1, 3) - reconstructed from NIfTI spacing
    'spatial_dim': numpy.ndarray # Shape: (1, 3) - spatial dimensions
}
```

### Usage
```bash
# Basic usage
python main_nifti2mat_spectral.py

# Or import as module
python -c "from main_nifti2mat_spectral import nifti_to_spectral_mat; 
           nifti_to_spectral_mat('nifti_dir', 'output.mat')"
```

### Automatic File Detection
The script automatically:
1. Finds all files matching `spectral_point_*.nii.gz`
2. Sorts them numerically (000, 001, 002, ...)
3. Reconstructs the original (N, X, Y, Z) array structure
4. Preserves resolution from NIfTI spacing information

---

## main_register2template_enhanced.py

### Purpose
Generic NIfTI registration script that registers all files in a directory to a template, with automatic template selection and parallel processing.

### Key Features
- ✅ **Auto-Template Selection**: Automatically selects central file as template when none specified
- ✅ **Generic File Support**: Works with any NIfTI files (not limited to spectral data)
- ✅ **Parallel Processing**: Configurable number of parallel processes
- ✅ **Comprehensive Reporting**: Detailed success/failure tracking
- ✅ **Command-Line Interface**: Full argument parsing and help system
- ✅ **Smart File Filtering**: Excludes already processed `.reg.nii.gz` files

### Command-Line Usage
```bash
# Auto-select central file as template
python main_register2template_enhanced.py input_dir output_dir

# Specify custom template
python main_register2template_enhanced.py input_dir output_dir \
    --template /path/to/template.nii.gz

# With custom options
python main_register2template_enhanced.py input_dir output_dir \
    --pattern "spectral_point_*.nii.gz" \
    --processes 8
```

### Arguments
- `input_dir`: Directory containing input NIfTI files
- `output_dir`: Output directory for registered files
- `--template`: Optional template file (default: auto-select central file)
- `--pattern`: File pattern to match (default: `*.nii.gz`)
- `--processes`: Number of parallel processes (default: 12)

### Function Signatures
```python
def process_directory_registration(input_dir, template, output_dir, 
                                 file_pattern="*.nii.gz", num_processes=12):
    """
    Process registration for all NIfTI files in a directory
    
    Args:
        input_dir (str): Directory containing input NIfTI files
        template (str or None): Template file (None = auto-select central file)
        output_dir (str): Output directory for registered files
        file_pattern (str): Pattern to match input files
        num_processes (int): Number of parallel processes
        
    Returns:
        dict: Processing results with statistics and file details
    """

def process_registration_file(args):
    """Process a single file for registration"""
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

## verify_roundtrip_conversion.py

### Purpose
Independent verification script that tests the accuracy of round-trip conversion (.mat → NIfTI → .mat).

### Key Features
- ✅ **Data Integrity Verification**: Ensures perfect data preservation
- ✅ **Comprehensive Analysis**: Checks shapes, values, metadata
- ✅ **Statistical Reporting**: Detailed difference analysis
- ✅ **Independent Operation**: Clean separation from conversion scripts

### Usage
```bash
python verify_roundtrip_conversion.py
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
python main_mat2nifti_spectral.py
# Output: 31 spectral NIfTI files + visualizations

# 2. Register all files to central template
python main_register2template_enhanced.py \
    patient2_nifti_spectral_output \
    patient2_registration_output \
    --processes 4
# Output: 31 registered .reg.nii.gz files

# 3. Convert back to .mat format (optional verification)
python main_nifti2mat_spectral.py
# Output: reconstructed .mat file

# 4. Verify round-trip accuracy (optional)
python verify_roundtrip_conversion.py
# Output: verification report
```

### Custom Resolution Example
```python
from main_mat2nifti_spectral import process_spectral_format

# Override resolution for specific requirements
process_spectral_format(
    mat_file="data.mat",
    output_dir="output",
    res=[2.0, 2.0, 4.0]  # Custom resolution in mm
)
```

### Batch Processing Example
```python
import glob
from main_register2template_enhanced import process_directory_registration

# Process multiple datasets
datasets = glob.glob("*_nifti_output/")
for dataset in datasets:
    output_dir = dataset.replace("_output", "_registered")
    results = process_directory_registration(
        input_dir=dataset,
        template=None,  # Auto-select
        output_dir=output_dir,
        num_processes=8
    )
    print(f"Processed {dataset}: {results['successful']} files registered")
```

---

## Error Handling & Troubleshooting

### Common Issues
1. **Missing Python Environment**: Ensure virtual environment is activated
2. **File Not Found**: Check file paths and permissions
3. **Memory Issues**: Reduce number of parallel processes
4. **Registration Convergence**: Normal for some files to have convergence warnings

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Validation
All scripts include comprehensive error checking and detailed status reporting. Check the generated metadata files for processing details and any warnings.

---

## Architecture Notes

### Design Principles
- **Single Responsibility**: Each script has one clear purpose
- **Clean Interfaces**: Functions can be imported and used programmatically
- **Comprehensive Logging**: Detailed status and error reporting
- **Flexible Configuration**: Command-line arguments and function parameters
- **Data Integrity**: Careful handling of medical imaging data formats

### File Naming Conventions
- Input files: Original names from .mat files
- Spectral files: `spectral_point_XXX.nii.gz` (zero-padded 3 digits)
- Registered files: `original_name.reg.nii.gz`
- Metadata files: `*_metadata.txt`

This documentation provides complete guidance for using the spectral data conversion and registration pipeline.
