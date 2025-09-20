# API Reference - DR-CSI Registration Module

**Part of the Diffusion-Relaxation Suite**

## Function Reference

### spectral_mat_to_nifti.py

**Command Line Usage:**
```bash
python spectral_mat_to_nifti.py input_file.mat output_dir [--res x y z]
```

#### `convert_spectral_mat_to_nifti(mat_file, output_dir, res=None)`
Convert spectral format .mat file to individual NIfTI files.

**Parameters:**
- `mat_file` (str): Path to input .mat file
- `output_dir` (str): Directory to save NIfTI files  
- `res` (list): Optional resolution override [x, y, z]

**Returns:**
- `dict`: Conversion results with statistics

**Example:**
```python
from spectral_mat_to_nifti import convert_spectral_mat_to_nifti

result = convert_spectral_mat_to_nifti(
    "data_wip_patient2.mat", 
    "patient2_nifti_spectral_output"
)
print(f"Created {result['num_spectral']} NIfTI files")
```

---

### spectral_nifti_to_mat.py

**Command Line Usage:**
```bash
python spectral_nifti_to_mat.py input_dir output_mat_file [original_mat_file]
```

#### `convert_spectral_nifti_to_mat(nifti_dir, output_mat_file, original_mat_file=None)`
Convert spectral NIfTI files back to the original .mat format with complete metadata and data type preservation.

**Parameters:**
- `nifti_dir` (str): Directory containing spectral_point_*.nii.gz files
- `output_mat_file` (str): Output .mat file path
- `original_mat_file` (str): Optional original .mat file for metadata preservation (recommended)

**Returns:**
- `bool`: True if conversion successful, False otherwise

**Key Features:**
- Preserves original data types (uint16, float64, etc.) exactly
- Maintains all metadata fields from original .mat file
- Zero data loss in roundtrip conversion

**Example:**
```python
from spectral_nifti_to_mat import convert_spectral_nifti_to_mat

success = convert_spectral_nifti_to_mat(
    "patient2_nifti_spectral_output", 
    "reconstructed_from_nifti.mat",
    "data_wip_patient2.mat"
)
print(f"Conversion {'succeeded' if success else 'failed'}")
```

---

### nifti_registration_pipeline.py

#### `register_nifti_directory(input_dir, template, output_dir, file_pattern="*.nii.gz", num_processes=4, template_strategy="average")`
Register all NIfTI files in a directory to a template.

**Parameters:**
- `input_dir` (str): Directory containing input NIfTI files
- `template` (str or None): Template file (None = auto-generate based on strategy)
- `output_dir` (str): Output directory for registered files
- `file_pattern` (str): Pattern to match input files (default: "*.nii.gz")
- `num_processes` (int): Number of parallel processes (default: 4)
- `template_strategy` (str): Template generation strategy - "average" (default), "central", or "specified"

**Returns:**
- `dict`: Processing results with statistics and file details

**Example:**
```python
from nifti_registration_pipeline import register_nifti_directory

# Using default average template strategy
results = register_nifti_directory(
    "patient2_nifti_spectral_output",
    template=None,  # Auto-generate average template
    output_dir="patient2_registration_output",
    num_processes=4,
    template_strategy="average"  # Default strategy
)
)
print(f"Successfully registered: {results['successful']} files")
```

#### `register_single_nifti_file(args)`
Register a single NIfTI file to a template.

**Parameters:**
- `args` (tuple): (input_file, template, output_file)

**Returns:**
- `dict`: Registration result with success status and message

---

### registration.py

#### `perform_nonlinear_registration(moving, fixed, output, linloss='cc', nonlinloss='cc', le=1500, ne=5000, device='cuda')`
Perform nonlinear registration between two medical images.

**Parameters:**
- `moving` (str): Path to moving image
- `fixed` (str): Path to fixed/template image  
- `output` (str): Path for output registered image
- `linloss` (str): Linear loss function (default: 'cc')
- `nonlinloss` (str): Nonlinear loss function (default: 'cc')
- `le` (int): Linear epochs (default: 1500)
- `ne` (int): Nonlinear epochs (default: 5000)
- `device` (str): Computing device (default: 'cuda')

**Returns:**
- None (saves registered image to output path)

**Example:**
```python
from registration import perform_nonlinear_registration

perform_nonlinear_registration(
    moving="input.nii.gz",
    fixed="template.nii.gz", 
    output="registered.nii.gz",
    device='cpu'
)
```

---

## Return Value Structures

### register_nifti_directory() Results
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

### register_single_nifti_file() Results
```python
{
    'input_file': str,         # Input file path
    'output_file': str,        # Output file path
    'success': bool,           # Registration successful
    'message': str             # Status/error message
}
```

---

## Error Handling

All functions include comprehensive error handling:

- **File not found**: Returns None or False with error messages
- **Invalid data format**: Validates input structure before processing
- **Memory errors**: Graceful handling of large data processing
- **CUDA errors**: Automatic fallback options available
- **Parallel processing errors**: Individual process error isolation

---

## Usage Patterns

### Complete Pipeline
```python
# Full workflow using all functions
from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
from nifti_registration_pipeline import register_nifti_directory  
from spectral_nifti_to_mat import convert_spectral_nifti_to_mat

# Step 1: Convert .mat to NIfTI
result = convert_spectral_mat_to_nifti("input.mat", "nifti_output")

# Step 2: Register all files
reg_results = register_nifti_directory(
    "nifti_output", None, "registration_output", num_processes=4
)

# Step 3: Convert back (verification)
success = convert_spectral_nifti_to_mat(
    "nifti_output", "reconstructed.mat", "input.mat"
)
```

### Batch Processing
```python
# Process multiple subjects
subjects = ["subject1", "subject2", "subject3"]

for subject in subjects:
    # Convert to NIfTI
    convert_spectral_mat_to_nifti(
        f"{subject}.mat", 
        f"{subject}_nifti"
    )
    
    # Register files
    register_nifti_directory(
        f"{subject}_nifti",
        template=None,
        output_dir=f"{subject}_registered"
    )
```

### Custom Configuration
```python
# Advanced usage with custom settings
results = register_nifti_directory(
    input_dir="spectral_data",
    template="custom_template.nii.gz",
    output_dir="registered_output", 
    file_pattern="spectral_*.nii.gz",
    num_processes=8
)

print(f"Processing summary:")
print(f"  Total files: {results['total_files']}")
print(f"  Successful: {results['successful']}")
print(f"  Failed: {results['failed']}")
print(f"  Skipped: {results['skipped']}")
```
