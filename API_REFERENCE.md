# API Reference

## Function Reference

### main_mat2nifti_spectral.py

#### `process_spectral_format(mat_file, output_dir, res=None)`
Convert spectral .mat file to individual NIfTI files.

**Parameters:**
- `mat_file` (str): Path to input .mat file
- `output_dir` (str): Output directory path
- `res` (list, optional): Override resolution [x, y, z] in mm

**Returns:**
- `int`: Number of spectral points processed
- `None`: If error occurred

**Example:**
```python
from main_mat2nifti_spectral import process_spectral_format

# Basic usage
count = process_spectral_format("data.mat", "output")

# With custom resolution
count = process_spectral_format("data.mat", "output", res=[2.0, 2.0, 3.0])
```

---

### main_nifti2mat_spectral.py

#### `nifti_to_spectral_mat(nifti_dir, output_mat_file, original_mat_file=None)`
Convert spectral NIfTI files back to .mat format.

**Parameters:**
- `nifti_dir` (str): Directory containing spectral_point_*.nii.gz files
- `output_mat_file` (str): Output .mat file path
- `original_mat_file` (str, optional): Original .mat file for comparison

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
from main_nifti2mat_spectral import nifti_to_spectral_mat

# Basic conversion
success = nifti_to_spectral_mat("nifti_dir", "output.mat")

# With validation against original
success = nifti_to_spectral_mat("nifti_dir", "output.mat", "original.mat")
```

---

### main_register2template_enhanced.py

#### `process_directory_registration(input_dir, template, output_dir, file_pattern="*.nii.gz", num_processes=12)`
Register all NIfTI files in a directory to a template.

**Parameters:**
- `input_dir` (str): Directory containing input NIfTI files
- `template` (str or None): Template file path (None = auto-select central file)
- `output_dir` (str): Output directory for registered files
- `file_pattern` (str): File pattern to match (default: "*.nii.gz")
- `num_processes` (int): Number of parallel processes (default: 12)

**Returns:**
- `dict`: Results dictionary with processing statistics

**Example:**
```python
from main_register2template_enhanced import process_directory_registration

# Auto-select template
results = process_directory_registration("input", None, "output")

# Custom template
results = process_directory_registration(
    "input", "template.nii.gz", "output", num_processes=8
)

# Access results
print(f"Successful: {results['successful']}")
print(f"Failed: {results['failed']}")
```

#### `process_registration_file(args)`
Process single file registration (internal function for parallel processing).

**Parameters:**
- `args` (tuple): (input_file, template, output_dir)

**Returns:**
- `dict`: Single file processing result

---

### verify_roundtrip_conversion.py

#### `verify_roundtrip_conversion(original_mat, reconstructed_mat)`
Verify round-trip conversion accuracy.

**Parameters:**
- `original_mat` (str): Path to original .mat file
- `reconstructed_mat` (str): Path to reconstructed .mat file

**Returns:**
- `dict`: Verification results with detailed statistics

**Example:**
```python
from verify_roundtrip_conversion import verify_roundtrip_conversion

results = verify_roundtrip_conversion("original.mat", "reconstructed.mat")
print(f"Data preserved: {results['data_identical']}")
```

---

## Return Value Structures

### process_directory_registration() Results
```python
{
    'input_dir': str,           # Input directory path
    'template': str,            # Template file used
    'output_dir': str,          # Output directory path
    'file_pattern': str,        # File pattern used
    'total_files': int,         # Total files processed
    'successful': int,          # Successfully registered files
    'skipped': int,            # Files skipped (already existed)
    'failed': int,             # Failed registrations
    'errors': list,            # List of error messages
    'file_results': list       # Detailed per-file results
}
```

### process_registration_file() Results
```python
{
    'input_file': str,         # Input file path
    'output_file': str,        # Output file path
    'success': bool,           # Registration successful
    'message': str             # Status/error message
}
```

### verify_roundtrip_conversion() Results
```python
{
    'data_identical': bool,        # Data arrays identical
    'shape_identical': bool,       # Array shapes match
    'resolution_identical': bool,  # Resolution values match
    'max_difference': float,       # Maximum data difference
    'mean_difference': float,      # Mean absolute difference
    'metadata_comparison': dict    # Detailed metadata comparison
}
```

---

## Error Handling

All functions include comprehensive error handling:

- **File not found**: Returns None or False with error messages
- **Invalid data format**: Validates input structure before processing
- **Memory issues**: Handles large datasets gracefully
- **Permission errors**: Clear error messages for file access issues

## Logging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Dependencies

Required packages for all functions:
```python
import os
import numpy as np
import scipy.io as sio
import nibabel as nib
import SimpleITK as sitk
from nilearn import plotting
import glob
from multiprocessing import Pool
import argparse
```
