# Registration Tool for Spectral MRI Data

## Overview

The DR-CSI Registration module provides robust nonlinear registration capabilities specifically designed for spectral MRI data. Registration is a critical preprocessing step that aligns multiple spectral volumes to correct for motion artifacts and ensure spatial consistency across the spectral dimension. This tool employs a multi-stage registration pipeline combining center alignment, affine registration, and nonlinear deformable registration using GPU-accelerated PyTorch/MONAI implementations.

### Why Registration is Important

Spectral MRI data consists of multiple 3D volumes acquired at different spectral points (e.g., diffusion or relaxation weightings). Patient motion, physiological movements, and scanner instabilities can cause misalignment between these volumes, leading to:

- **Spatial inconsistencies** across spectral dimensions
- **Artifacts** in downstream spectral analysis
- **Reduced accuracy** in quantitative parameter estimation
- **Loss of fine structural details**

The registration tool corrects these misalignments by:

1. **Center alignment**: Initial coarse alignment based on image centers
2. **Affine registration**: Global linear transformation (rotation, translation, scaling)
3. **Nonlinear registration**: Local deformable warping to account for tissue deformation

### Registration Pipeline Architecture

```
Input .mat file → NIfTI conversion → Registration → .mat reconstruction
     ↓                    ↓                ↓              ↓
  spectral_data    spectral_point_*.nii.gz  *.reg.nii.gz  registered.mat
```

The pipeline consists of three main components:

1. **Data Conversion**: Spectral .mat format → Individual NIfTI volumes
2. **Registration**: Multi-stage alignment with GPU acceleration
3. **Reconstruction**: Registered NIfTI → Spectral .mat format

---

## Command-Line Interface

### Complete Automated Workflow (Recommended)

For most users, the integrated module workflow provides the simplest interface:

**Shell Script:**
```bash
python run_registration_module.py <input_mat_file> <output_directory> [--processes <num>]
```

**Example:**
```bash
python run_registration_module.py data/patient_data.mat results/patient_registered
```

**MATLAB (via system call):**
```matlab
system('python run_registration_module.py data/patient_data.mat results/patient_registered');
```

### Step-by-Step Workflow

For users who need more control over individual steps:

**Step 1: Convert .mat to NIfTI**
```bash
python convert_mat_to_nifti.py <input_mat_file> <output_directory> [--res X Y Z]
```

**Step 2: Register NIfTI files**
```bash
python register_nifti.py <input_directory> <output_directory> [--processes <num>] [--template <template_file>]
```

**Step 3: Convert back to .mat**
```bash
python convert_nifti_to_mat.py <input_directory> <output_mat_file> <original_mat_file>
```

---

## Required Inputs

### `input_mat_file`

Filename of the `.mat` file storing spectral MRI data. The file must contain:

- **`data`**: 4D numpy array with shape `(z, y, x, spectral_points)`
  - Spatial dimensions: `(z, y, x)` represent the 3D MR volume
  - Spectral dimension: Last axis contains multiple spectral acquisitions
  - Data type: Typically `uint16` or `float64`

- **`resolution`** (optional but recommended): Array `[[x_res, y_res, z_res]]` in millimeters
  - Example: `[[2.3, 2.3, 5.0]]` for 2.3mm × 2.3mm × 5mm voxels
  - If not provided, default resolution `[1.0, 1.0, 1.0]` is used

Example .mat file structure:
```python
{
    'data': np.array(shape=(12, 52, 104, 31), dtype=np.uint16),
    'resolution': np.array([[2.3, 2.3, 5.0]]),
    'transform': np.eye(4),
    'spatial_dim': np.array([[12, 52, 104]])
}
```

**File format details**: See [File Formats](FILE_FORMATS.md#spectral-mat-file)

### `output_directory`

A string specifying the directory where output files will be saved. The directory structure will be:

```
output_directory/
├── nifti/                           # Converted NIfTI files
│   ├── spectral_point_000.nii.gz
│   ├── spectral_point_001.nii.gz
│   └── ...
├── registration/                    # Registered NIfTI files
│   ├── spectral_point_000.reg.nii.gz
│   ├── spectral_point_001.reg.nii.gz
│   ├── ...
│   └── registration_metadata.txt
└── {input_name}_registered.mat      # Final registered data
```

---

## Optional Inputs

### `--processes <num>` (or `-p <num>`)

Number of parallel processes for registration. Default: `4`

- **Higher values** (8-16): Faster processing on multi-core systems, but requires more RAM
- **Lower values** (1-4): More memory-efficient, suitable for limited resources
- **Single process** (`1`): Sequential processing, minimal overhead, useful for debugging

**Example:**
```bash
python run_registration_module.py data/input.mat output/ --processes 8
```

**Note:** GPU usage is per-process. Multiple processes share GPU resources.

### `--template <template_file>` (Registration Step Only)

Specify a custom template/reference image for registration. By default, the pipeline uses template generation strategies:

- **Default**: Average template (average of all spectral volumes)
- **Alternative**: Central volume (middle spectral point)
- **Custom**: User-specified NIfTI file

**Example with custom template:**
```bash
python register_nifti.py input_nifti/ output_nifti/ --template input_nifti/spectral_point_015.nii.gz
```

### `--template-strategy <strategy>`

Choose automatic template selection strategy:
- `average`: Compute average volume from all spectral points (default, best SNR)
- `central`: Use middle spectral volume
- `specified`: Requires `--template` with specific file

**Example:**
```bash
python register_nifti.py input_nifti/ output_nifti/ --template-strategy central
```

### `--res X Y Z` (Conversion Step Only)

Override voxel resolution when converting .mat to NIfTI. Specified in millimeters as three space-separated values.

**Example:**
```bash
python convert_mat_to_nifti.py input.mat output/ --res 2.0 2.0 3.0
```

If not specified, resolution is read from the .mat file's `resolution` field.

---

## Output

The registration pipeline produces multiple output files organized in a structured directory:

### 1. Intermediate NIfTI Files

**Location:** `<output_directory>/nifti/`

Individual NIfTI volumes for each spectral point:
- **Filenames**: `spectral_point_000.nii.gz`, `spectral_point_001.nii.gz`, ..., `spectral_point_N.nii.gz`
- **Format**: Compressed NIfTI (`.nii.gz`)
- **Content**: 3D spatial volume for each spectral acquisition
- **Metadata**: Preserved affine transformation, spacing, and orientation

**Metadata file:** `spectral_metadata.txt` contains:
```
Data from spectral format .mat file
Original data shape: (12, 52, 104, 31)
Spectral dimension: 31 (last dimension)
Spatial dimensions: (12, 52, 104) (z, y, x)
Resolution: [[2.3 2.3 5.0]]
Number of NIfTI files created: 31
Spacing used: [2.3, 2.3, 5.0]
```

### 2. Registered NIfTI Files

**Location:** `<output_directory>/registration/`

Registered volumes aligned to the template:
- **Filenames**: `spectral_point_000.reg.nii.gz`, `spectral_point_001.reg.nii.gz`, ...
- **Format**: Compressed NIfTI (`.nii.gz`)
- **Content**: Spatially aligned 3D volumes
- **Transformations**: Composed affine + nonlinear deformation fields

**Registration metadata:** `registration_metadata.txt` contains:
```
Registration completed: 2025-11-16 14:23:45
Template strategy: average
Number of volumes: 31
Successful registrations: 31
Failed registrations: 0
Processing time: 3.7 hours
GPU device: NVIDIA RTX 3090
```

**Deformation fields** (optional, saved in subdirectories):
- `spectral_point_XXX.rodreg.*/composed_ddf.map.nii.gz`: Composed forward deformation
- `spectral_point_XXX.rodreg.*/inv.composed_ddf.map.nii.gz`: Inverse deformation

### 3. Final Registered .mat File

**Location:** `<output_directory>/<input_name>_registered.mat`

Reconstructed spectral data in HDF5-based MATLAB v7.3 format:

**Variables:**
- **`data`**: 4D array, shape `(z, y, x, num_spectral)`, same dtype as input
  - Example: `(12, 52, 104, 31)` with dtype `uint16`
  - All spectral volumes aligned to common spatial reference
  
- **`resolution`**: Array `[[x_res, y_res, z_res]]`, preserved or derived from NIfTI spacing
  
- **`transform`**: 4×4 affine matrix (preserved from original file)
  
- **`spatial_dim`**: Array `[[z_dim, y_dim, x_dim]]` (preserved from original file)

**All other original metadata fields are preserved**, including custom user fields.

**File size:** Typically 3-10 MB depending on data dimensions and dtype.

**Data type preservation:** The output preserves the exact dtype from the input file:
- `uint16` → `uint16`
- `float32` → `float32`
- `float64` → `float64`

### 4. Visualization Files (Optional)

**Location:** `<output_directory>/nifti/`

PNG preview images for quality assessment:
- `spectral_point_000.png`, `spectral_point_001.png`, ..., `spectral_point_004.png`
- Orthogonal slice views (axial, sagittal, coronal)
- Generated for first 5 spectral points only

---

## Example Usage

### Example 1: Basic Registration Workflow

Complete automated processing of patient data:

```bash
# Input: data/patient001.mat with 31 spectral points
# Output: results/patient001/

python run_registration_module.py data/patient001.mat results/patient001
```

**Expected output:**
```
Step 1: Converting .mat to NIfTI format...
✅ Created 31 spectral NIfTI files

Step 2: Registering spectral volumes...
🔧 Using GPU 0 for registration
✅ Registration completed: 31/31 successful
Processing time: 3.2 hours

Step 3: Converting back to .mat format...
✅ Saved: results/patient001/patient001_registered.mat
Final data shape: (12, 52, 104, 31)
```

### Example 2: Custom Resolution and Parallel Processing

Override resolution and use 8 parallel processes:

```bash
# Step 1: Convert with custom resolution
python convert_mat_to_nifti.py data/scan_data.mat temp/nifti_out --res 1.5 1.5 3.0

# Step 2: Register with 8 parallel processes
python register_nifti.py temp/nifti_out temp/registered --processes 8

# Step 3: Reconstruct with metadata preservation
python convert_nifti_to_mat.py temp/registered results/scan_registered.mat data/scan_data.mat
```

### Example 3: Custom Template Registration

Use a specific high-quality volume as registration template:

```bash
# First, inspect volumes and identify best quality (e.g., spectral_point_020)
python convert_mat_to_nifti.py data/input.mat temp/nifti

# Register using volume 20 as template
python register_nifti.py temp/nifti temp/registered \
    --template temp/nifti/spectral_point_020.nii.gz \
    --processes 4

# Reconstruct
python convert_nifti_to_mat.py temp/registered results/output.mat data/input.mat
```

### Example 4: MATLAB Integration

Call the registration module from MATLAB:

```matlab
% Set paths
input_file = 'data/mri_data.mat';
output_dir = 'results/registered_output';

% Run registration module
cmd = sprintf('python run_registration_module.py %s %s --processes 4', ...
              input_file, output_dir);
[status, output] = system(cmd);

% Check status
if status == 0
    fprintf('Registration completed successfully\n');
    
    % Load registered data
    registered_file = fullfile(output_dir, 'mri_data_registered.mat');
    data = load(registered_file);
    
    fprintf('Registered data shape: %s\n', mat2str(size(data.data)));
else
    fprintf('Registration failed:\n%s\n', output);
end
```

---

## Processing Time and Hardware Requirements

### Hardware Requirements

**Minimum Requirements:**
- CPU: Multi-core processor (4+ cores recommended)
- RAM: 16 GB
- GPU: NVIDIA GPU with CUDA support (e.g., GTX 1060 or better)
- GPU Memory: 4 GB minimum
- Disk Space: 5-10 GB for temporary files

**Recommended Configuration:**
- CPU: 8+ cores (Intel i7/i9, AMD Ryzen 7/9)
- RAM: 32 GB
- GPU: NVIDIA RTX 3060 or better (8+ GB VRAM)
- Disk: SSD for faster I/O

### Processing Time Estimates

Typical processing times for a dataset with 31 spectral volumes (spatial dimensions: 12×52×104):

| Component | Time (GPU) | Time (CPU-only) |
|-----------|------------|-----------------|
| .mat → NIfTI conversion | 30 sec | 30 sec |
| Registration (4 processes) | 3-4 hours | 12-24 hours |
| NIfTI → .mat conversion | 1 min | 1 min |
| **Total** | **~3.5 hours** | **~12-24 hours** |

**Factors affecting processing time:**
- Number of spectral volumes (scales linearly)
- Spatial resolution (higher resolution = longer time)
- Number of registration iterations (default: 1500 affine + 5000 nonlinear)
- GPU performance (RTX 3090 ~2× faster than GTX 1060)
- Parallel processes (4-8 optimal for most systems)

---

## Technical Notes

### Registration Algorithm Details

The registration pipeline implements a three-stage approach:

1. **Center Alignment** (SimpleITK):
   - Computes center of mass for fixed and moving images
   - Applies translation to align centers
   - Fast initialization step (~1 second per volume)

2. **Affine Registration** (PyTorch/MONAI):
   - 12-parameter affine transformation (translation, rotation, scaling, shearing)
   - Adam optimizer with learning rate 0.01
   - 1500 iterations (default)
   - Local normalized cross-correlation (LNCC) similarity metric
   - GPU-accelerated gradient computation

3. **Nonlinear Registration** (PyTorch/MONAI):
   - Dense deformation field (U-Net architecture)
   - 5000 iterations (default)
   - LNCC similarity + smoothness regularization
   - Diffeomorphic (topology-preserving) transformations
   - GPU-accelerated warping and interpolation

### Template Selection Strategies

**Average Template (Default)**:
```python
# Pseudo-code for average template generation
template = np.mean([load_volume(f) for f in all_volumes], axis=0)
```
- **Advantages**: Best signal-to-noise ratio, balanced representation
- **Disadvantages**: Slightly blurred if volumes are already misaligned
- **Best for**: Most clinical datasets

**Central Volume**:
```python
# Pseudo-code for central volume selection
n_volumes = len(all_volumes)
template = load_volume(all_volumes[n_volumes // 2])
```
- **Advantages**: Fast, real acquired volume (no averaging artifacts)
- **Disadvantages**: May not be optimal reference for all volumes
- **Best for**: High-quality datasets with minimal motion

### Data Type Preservation

The pipeline preserves exact data types throughout:

```python
# Input .mat
data: dtype=uint16, shape=(12, 52, 104, 31)

# NIfTI conversion (internal float64 for processing)
spectral_point_000.nii.gz: dtype=float64

# Registration (maintains float64)
spectral_point_000.reg.nii.gz: dtype=float64

# Output .mat (restored to original dtype)
data: dtype=uint16, shape=(12, 52, 104, 31)
```

This ensures **zero precision loss** for integer data types.

### Metadata Preservation

All original .mat file fields are preserved:
```python
# Original file
original_fields = ['data', 'resolution', 'transform', 'spatial_dim', 'custom_field1', 'custom_field2']

# Registered file (only 'data' updated)
registered_fields = ['data', 'resolution', 'transform', 'spatial_dim', 'custom_field1', 'custom_field2']
                     # ↑ updated    ↑ all others preserved exactly
```

### GPU Memory Management

The registration algorithm automatically manages GPU memory:
- Batch processing for large volumes
- Automatic garbage collection between registrations
- Fallback to CPU if GPU memory exhausted

**Typical GPU memory usage:**
- Affine registration: 1-2 GB
- Nonlinear registration: 2-4 GB
- Multiple processes: Memory × processes (with some sharing)

---

## Troubleshooting

### Common Issues and Solutions

**Issue 1: "CUDA out of memory" error**

**Cause:** GPU memory insufficient for volume size or too many parallel processes

**Solutions:**
- Reduce number of processes: `--processes 2`
- Use smaller batch size (modify `src/warper.py` if needed)
- Upgrade GPU or use system with more VRAM

**Issue 2: "No CUDA-capable device detected"**

**Cause:** No NVIDIA GPU or CUDA drivers not installed

**Solutions:**
- Install CUDA toolkit and drivers
- Check with: `python -c "import torch; print(torch.cuda.is_available())"`
- Registration will fallback to CPU (much slower)

**Issue 3: Registration takes too long (>6 hours)**

**Cause:** CPU-only processing or insufficient GPU resources

**Solutions:**
- Verify GPU usage: `nvidia-smi` should show Python process
- Increase parallel processes if you have idle CPU cores
- Consider reducing registration iterations for faster (but less accurate) results

**Issue 4: "Unable to open file (file signature not found)" HDF5 error**

**Cause:** Attempting to read non-HDF5 file with h5py

**Solutions:**
- Delete any partial output files
- Ensure original .mat file is valid: `python -c "import scipy.io; scipy.io.loadmat('file.mat')"`
- Re-run the complete workflow

**Issue 5: Poor registration quality**

**Causes:** Poor template selection, insufficient iterations, or extreme motion

**Solutions:**
- Try different template strategies (`average`, `central`, or specify best volume)
- Increase registration iterations in `src/registration.py`
- Check input data quality (SNR, artifacts)
- Visual inspection: review PNG previews in `nifti/` directory

---

## Performance Optimization Tips

1. **Optimal parallel processes:**
   - Start with `--processes 4`
   - Monitor CPU/GPU usage with `htop` and `nvidia-smi`
   - Increase if resources underutilized, decrease if memory issues

2. **Fast preliminary testing:**
   - Reduce iterations in `src/registration.py` for quick tests
   - Use subset of data (manually select few spectral points)
   - Restore full iterations for final processing

3. **Storage optimization:**
   - Use SSD for intermediate NIfTI files
   - Clean up intermediate directories after successful completion
   - Compressed NIfTI (`.nii.gz`) saves 70-90% disk space

4. **GPU selection (multi-GPU systems):**
   - Set `CUDA_VISIBLE_DEVICES=0` for first GPU
   - Distribute processes across GPUs: `CUDA_VISIBLE_DEVICES=0,1`

---

## References

- MONAI (Medical Open Network for AI): https://monai.io/
- SimpleITK: https://simpleitk.org/
- NIfTI format: https://nifti.nimh.nih.gov/
- Diffeomorphic registration: Vercauteren et al., NeuroImage 2009

---

## See Also

- [Tutorial: Registration of Phantom Data](REGISTRATION_TUTORIAL.md)
- [File Format Reference](FILE_FORMATS.md)
- [API Reference](API_REFERENCE.md)
- [Installation Guide](../README.md#installation)
