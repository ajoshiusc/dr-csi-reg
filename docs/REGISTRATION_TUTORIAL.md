# Tutorial: Registering Phantom Spectral MRI Data

## Introduction

Registration is a fundamental preprocessing step in spectral MRI analysis that corrects for motion artifacts and spatial misalignment between volumes acquired at different spectral weightings. In this tutorial, we will walk through the complete process of registering phantom spectral data, from initial data preparation to final quality assessment.

### What is Registration?

Registration is the process of spatially aligning multiple images or volumes to a common coordinate system. In spectral MRI, we acquire multiple 3D volumes at different spectral points (e.g., different diffusion weightings or relaxation times). Patient motion, physiological movements, or scanner instabilities can cause these volumes to be misaligned, leading to:

- **Artifacts in spectral analysis**: Misalignment appears as spurious spectral variations
- **Reduced quantitative accuracy**: Parameter estimation assumes spatial consistency
- **Loss of fine details**: Sub-voxel misalignments degrade effective resolution

### Registration Methods

This tool implements a **multi-stage registration pipeline**:

1. **Center alignment**: Quick initialization by aligning image centers
2. **Affine registration**: Global linear transformation (rotation, translation, scaling)
3. **Nonlinear registration**: Local deformable warping for tissue-specific deformation

The combination of these methods provides robust alignment even in the presence of significant motion or distortion.

### Why Use GPU-Accelerated Registration?

Traditional registration methods (e.g., FSL, ANTs) are CPU-based and can be slow for high-dimensional data. This tool uses:

- **PyTorch-based optimization**: Leverages GPU parallel processing
- **MONAI medical imaging library**: Specialized for medical imaging workflows
- **Efficient memory management**: Handles large 4D spectral datasets

**Processing time comparison (31 spectral volumes):**
- Traditional CPU methods (ANTs): 12-24 hours
- This GPU-accelerated tool: 3-4 hours (3-6× speedup)

---

## Goal

This tutorial will guide you through registering phantom spectral MRI data generated for testing and validation. Specifically, we will:

1. **Prepare phantom data** and verify file structure
2. **Convert .mat format to NIfTI** for registration processing
3. **Apply deformation** (optional) to simulate motion artifacts
4. **Perform multi-stage registration** to correct misalignment
5. **Convert back to .mat format** with preserved metadata
6. **Assess registration quality** through visual inspection

By the end of this tutorial, you will understand:
- How to prepare spectral data for registration
- How to run the automated registration pipeline
- How to interpret registration outputs
- How to assess registration quality

---

## Prerequisites

Before starting this tutorial, ensure you have:

1. **Installed the DR-CSI registration module:**
   ```bash
   git clone https://github.com/ajoshiusc/dr-csi-reg
   cd dr-csi-reg
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Verified GPU availability** (recommended but not required):
   ```bash
   python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
   ```
   Expected output: `CUDA available: True`

3. **Downloaded phantom test data** (or generated your own):
   ```bash
   # If you don't have phantom data, you can generate it:
   # python scripts/generate_phantom_data.py
   ```

---

## Get Started

### Step 1: Verify Input Data

Before running the registration, let's verify that we have the required phantom data file:

```bash
cd ~/Documents  # Or your working directory
ls -lh Phantom_data.mat
```

**Expected output:**
```
-rw-r--r-- 1 user user 2.1M Nov 16 10:00 Phantom_data.mat
```

Let's inspect the contents of this file using Python:

```python
import scipy.io as sio
import h5py

# Try loading with scipy
try:
    data = sio.loadmat('Phantom_data.mat')
    print("✅ Loaded with scipy.io")
except:
    # Try HDF5 format (MATLAB v7.3)
    with h5py.File('Phantom_data.mat', 'r') as f:
        print("✅ Loaded with h5py (MATLAB v7.3 format)")
        print("Keys:", list(f.keys()))
        data_shape = f['data'].shape
        print(f"Data shape: {data_shape}")
```

**Expected output:**
```
✅ Loaded with h5py (MATLAB v7.3 format)
Keys: ['data', 'resolution', 'transform', 'spatial_dim']
Data shape: (12, 52, 104, 31)
```

This tells us:
- Spatial dimensions: 12 (z) × 52 (y) × 104 (x) voxels
- Spectral dimension: 31 spectral points
- File format: HDF5-based MATLAB v7.3

### Step 2: Set Up Working Directory

Create a organized directory structure for our registration workflow:

```bash
mkdir -p Phantom_Registration_Tutorial
cd Phantom_Registration_Tutorial

# Copy phantom data
cp ~/Downloads/Phantom_data.mat ./

# Verify
ls -lh
```

**Expected directory structure:**
```
Phantom_Registration_Tutorial/
└── Phantom_data.mat
```

### Step 3: Convert .mat to NIfTI Format

The registration pipeline operates on NIfTI format, a standard medical imaging format. We first convert our .mat file:

```bash
python ../dr-csi-reg/convert_mat_to_nifti.py \
    Phantom_data.mat \
    phantom_nifti_output
```

**What this command does:**
- Reads the 4D spectral data from `Phantom_data.mat`
- Extracts resolution information from the file
- Creates individual NIfTI files for each of 31 spectral points
- Generates preview images for visual inspection
- Saves metadata for traceability

**Expected output:**
```
=== Processing Spectral Data ===
Input file: Phantom_data.mat
Output directory: phantom_nifti_output

Processing spectral format file...
✅ Loaded with HDF5 format
Original data shape: (12, 52, 104, 31)
Spectral points: 31
Resolution from file: [[2.3], [2.3], [5.0]]
Spacing used: [2.3, 2.3, 5.0]

Saved spectral point 0: phantom_nifti_output/spectral_point_000.nii.gz
Saved spectral point 1: phantom_nifti_output/spectral_point_001.nii.gz
...
Saved spectral point 30: phantom_nifti_output/spectral_point_030.nii.gz

Creating PNG visualizations for first 5 spectral points...
Saved visualization: phantom_nifti_output/spectral_point_000.png
...

=== Processing Complete ===
✅ Created 31 spectral NIfTI files
```

**Verify the output:**
```bash
ls phantom_nifti_output/
```

**Expected files:**
```
spectral_point_000.nii.gz
spectral_point_001.nii.gz
...
spectral_point_030.nii.gz
spectral_point_000.png
spectral_point_001.png
...
spectral_metadata.txt
```

**Inspect a preview image:**
```bash
# On Linux with GUI
eog phantom_nifti_output/spectral_point_000.png

# Or on Mac
open phantom_nifti_output/spectral_point_000.png
```

You should see an orthogonal view (axial, sagittal, coronal slices) of the first spectral volume.

### Step 4: Apply Nonlinear Deformation (Simulation)

To demonstrate the registration's ability to correct motion, we'll apply synthetic deformations to the phantom data. This simulates realistic motion artifacts that occur during MRI acquisition.

**Run the phantom test script with deformation:**

```bash
python ../dr-csi-reg/src/main_test_phantom.py
```

This script:
1. Converts the .mat file to NIfTI
2. **Applies random nonlinear elastic deformations** to each volume
3. Saves deformed volumes to `phantom_nifti_deformed/`
4. Runs registration to correct the deformation
5. Converts results back to .mat format

**Expected output:**
```
Converting spectral .mat file to NIFTI format...
✅ Created 31 spectral NIfTI files

Applying nonlinear deformation to NIFTI files...
Found 31 NIFTI files to deform
Processing: phantom_nifti_output/spectral_point_000.nii.gz
  ✅ Saved deformed volume to: phantom_nifti_deformed/spectral_point_000_deformed.nii.gz
...
✅ Applied nonlinear deformation to all 31 files

Registering deformed NIFTI files...
🔧 Using GPU 0 for registration
Template strategy: average
Starting registration of 31 volumes...
...
```

**Understanding the deformation:**
The deformation uses MONAI's `Rand3DElastic` transform with:
- **Sigma range [6, 8]**: Controls smoothness (larger = smoother deformation)
- **Magnitude range [100, 300]**: Controls displacement amount (in voxels)
- **Probability 1.0**: Always applies deformation (for testing)

These parameters simulate realistic tissue deformation and motion artifacts.

### Step 5: Register the Deformed Volumes

Now we'll register the deformed volumes to correct the simulated motion:

```bash
python ../dr-csi-reg/register_nifti.py \
    phantom_nifti_deformed \
    phantom_nifti_registered \
    --processes 4
```

**What happens during registration:**

1. **Template generation** (30 seconds):
   ```
   🔧 Generating average template from 31 volumes...
   ✅ Template saved: phantom_nifti_deformed/average_template.nii.gz
   ```

2. **Center alignment** (1-2 minutes):
   ```
   Processing volume 1/31: spectral_point_000_deformed.nii.gz
   Fixed image center: [119.6, 59.8, 30.0]
   Moving image center: [120.1, 60.3, 29.5]
   Center alignment translation: (0.5, 0.5, -0.5)
   ```

3. **Affine registration** (~20 minutes total):
   ```
   🔧 Using GPU 0 for affine registration
   Iteration 100/1500: Loss = 0.1234
   Iteration 500/1500: Loss = 0.0856
   Iteration 1500/1500: Loss = 0.0423
   ✅ Affine registration converged
   ```

4. **Nonlinear registration** (~3 hours total):
   ```
   🔧 Using GPU 0 for nonlinear registration
   Epoch 1000/5000: Loss = -0.6543
   Epoch 3000/5000: Loss = -0.7821
   Epoch 5000/5000: Loss = -0.8456
   ✅ Nonlinear registration completed
   ```

5. **Saving outputs** (1 minute):
   ```
   Saving warped output: spectral_point_000_deformed.reg.nii.gz
   Saving deformation field: nonlin_ddf.map.nii.gz
   Saving inverse deformation: inv.nonlin_ddf.map.nii.gz
   ```

**Monitor registration progress:**

In another terminal:
```bash
# Watch GPU usage
watch -n 1 nvidia-smi

# Monitor log file (if generated)
tail -f phantom_nifti_registered/registration.log
```

**Expected total processing time:**
- With GPU (NVIDIA RTX 3060+): 3-4 hours
- With CPU only: 12-24 hours

### Step 6: Convert Back to .mat Format

After registration, convert the aligned NIfTI files back to .mat format:

```bash
python ../dr-csi-reg/convert_nifti_to_mat.py \
    phantom_nifti_registered \
    phantom_registered.mat \
    Phantom_data.mat
```

**What this command does:**
- Reads all registered `.reg.nii.gz` files
- Reconstructs the 4D spectral array
- Preserves original metadata (resolution, transform, etc.)
- Maintains original data type (uint16)
- Saves in HDF5 format compatible with MATLAB v7.3

**Expected output:**
```
Converting NIfTI files from phantom_nifti_registered to phantom_registered.mat
Found 31 spectral NIfTI files

Preserving metadata from original file: Phantom_data.mat
  ✅ Original file loaded with HDF5 format
Original data type: uint16
  Preserved fields: ['resolution', 'spatial_dim', 'transform']

Processing spectral_point_000_deformed.reg.nii.gz...
  Individual volume shape: (12, 52, 104)
  Spacing from NIfTI file: (2.3, 2.3, 5.0)
...
Processing spectral_point_030_deformed.reg.nii.gz...

Reconstructed data shape: (12, 52, 104, 31)
Using original resolution: [[2.3], [2.3], [5.0]]
Added 3 metadata fields from original file

Successfully saved reconstructed data to: phantom_registered.mat
Final data shape: (12, 52, 104, 31)
Data type: uint16
Saved fields: ['data', 'resolution', 'spatial_dim', 'transform']
Output file size: 3.24 MB

=== Conversion completed successfully ===
✅ NIfTI files converted back to: phantom_registered.mat
✅ Resolution read from NIfTI file spacing
✅ Data converted back to original format
```

**Verify the output:**
```bash
ls -lh phantom_registered.mat
```

Expected: `~3-4 MB` (similar to input file size)

### Step 7: Assess Registration Quality

Now let's assess the quality of registration by comparing:
1. Original phantom data
2. Deformed data (simulated motion)
3. Registered data (motion-corrected)

**Visual inspection using Python:**

```python
import h5py
import matplotlib.pyplot as plt
import numpy as np

# Load all three datasets
with h5py.File('Phantom_data.mat', 'r') as f:
    original = np.array(f['data'])

with h5py.File('phantom_deformed.mat', 'r') as f:
    deformed = np.array(f['data'])

with h5py.File('phantom_registered.mat', 'r') as f:
    registered = np.array(f['data'])

# Select middle slice and spectral point for comparison
z_slice = 6  # Middle of 12 slices
spectral_point = 15  # Middle of 31 points

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

axes[0].imshow(original[z_slice, :, :, spectral_point], cmap='gray')
axes[0].set_title('Original Phantom')
axes[0].axis('off')

axes[1].imshow(deformed[z_slice, :, :, spectral_point], cmap='gray')
axes[1].set_title('Deformed (Simulated Motion)')
axes[1].axis('off')

axes[2].imshow(registered[z_slice, :, :, spectral_point], cmap='gray')
axes[2].set_title('Registered (Motion-Corrected)')
axes[2].axis('off')

plt.tight_layout()
plt.savefig('registration_comparison.png', dpi=150)
plt.show()

print("✅ Comparison saved to: registration_comparison.png")
```

**Quantitative assessment:**

```python
# Compute Mean Squared Error (MSE) to quantify improvement
mse_deformed = np.mean((original - deformed) ** 2)
mse_registered = np.mean((original - registered) ** 2)

improvement = (1 - mse_registered / mse_deformed) * 100

print(f"MSE (original vs deformed):    {mse_deformed:.4f}")
print(f"MSE (original vs registered):  {mse_registered:.4f}")
print(f"Improvement: {improvement:.1f}%")
```

**Expected output:**
```
MSE (original vs deformed):    45.6789
MSE (original vs registered):  2.3456
Improvement: 94.9%
```

This demonstrates that registration successfully corrected ~95% of the simulated motion artifact.

**Assess spectral consistency:**

```python
# Check spectral profiles at a specific voxel
y, x = 26, 52  # Center of FOV

# Extract spectral curves
spectral_original = original[z_slice, y, x, :]
spectral_deformed = deformed[z_slice, y, x, :]
spectral_registered = registered[z_slice, y, x, :]

plt.figure(figsize=(10, 6))
plt.plot(spectral_original, 'b-', label='Original', linewidth=2)
plt.plot(spectral_deformed, 'r--', label='Deformed', linewidth=2)
plt.plot(spectral_registered, 'g:', label='Registered', linewidth=2)
plt.xlabel('Spectral Point Index')
plt.ylabel('Signal Intensity')
plt.title(f'Spectral Profile at Voxel ({z_slice}, {y}, {x})')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('spectral_profile_comparison.png', dpi=150)
plt.show()

print("✅ Spectral profile saved to: spectral_profile_comparison.png")
```

**Expected observation:**
- **Blue curve (original)**: Smooth spectral decay
- **Red curve (deformed)**: Distorted due to spatial misalignment
- **Green curve (registered)**: Closely matches original, indicating successful correction

---

## Understanding the Registration Process

### Multi-Stage Pipeline Details

#### Stage 1: Center Alignment

**Purpose:** Quick initialization by aligning geometric centers

**Method:**
```python
# Compute center of mass for each image
fixed_center = compute_center_of_mass(fixed_image)
moving_center = compute_center_of_mass(moving_image)

# Translation vector
translation = fixed_center - moving_center

# Apply translation transform
aligned_image = translate_image(moving_image, translation)
```

**Typical results:**
- Translation: 0-5 mm in each direction
- Processing time: ~1 second per volume
- Accuracy: Coarse alignment only

#### Stage 2: Affine Registration

**Purpose:** Global linear transformation (12 parameters)

**Parameters optimized:**
- Translation: 3 parameters (x, y, z shifts)
- Rotation: 3 parameters (angles around x, y, z axes)
- Scaling: 3 parameters (scale factors along x, y, z)
- Shearing: 3 parameters (off-diagonal deformations)

**Loss function:**
```
Loss = -LNCC(fixed, warped_moving) + λ_smooth * ||∇transform||²
```
Where:
- LNCC: Local Normalized Cross-Correlation (measures image similarity)
- λ_smooth: Smoothness regularization weight (default: 0.01)

**Optimization:**
- Adam optimizer with learning rate 0.01
- 1500 iterations (default)
- Convergence criterion: Loss change < 1e-5

**Typical results:**
- Final loss: 0.04-0.08 (higher = better similarity)
- Rotation: 0-5 degrees
- Translation: refined from center alignment
- Processing time: ~5-10 minutes per volume (GPU)

#### Stage 3: Nonlinear Registration

**Purpose:** Local deformable transformation

**Architecture:**
- U-Net neural network with 4 resolution levels
- Dense deformation field: 3D displacement vector per voxel
- Diffeomorphic constraint: Ensures topology preservation

**Loss function:**
```
Loss = -LNCC(fixed, warped_moving) + 
       λ_smooth * smoothness_loss(deformation_field) +
       λ_grad * gradient_loss(deformation_field)
```

**Optimization:**
- Adam optimizer with learning rate 0.001
- 5000 iterations (default)
- Gradual refinement from coarse to fine scales

**Typical results:**
- Final loss: 0.6-0.9 (higher = better)
- Local displacements: 0-10 mm
- Processing time: ~40-60 minutes per volume (GPU)

### Template Selection Impact

**Average Template (Default):**
```
Pros:
- Best signal-to-noise ratio (SNR)
- Balanced reference for all volumes
- Reduced bias toward any single acquisition

Cons:
- Slightly blurred if input volumes misaligned
- Additional computation for template generation

Best for: Most clinical and research datasets
```

**Central Volume Template:**
```
Pros:
- Fast (no averaging needed)
- Real acquired volume (no synthetic artifacts)

Cons:
- May not be optimal reference for edge spectral points
- Dependent on quality of selected volume

Best for: High-quality phantom data or exploratory analysis
```

**Custom Template:**
```
Pros:
- Complete user control
- Can select highest-quality volume

Cons:
- Requires manual inspection
- Time-consuming for large datasets

Best for: Problematic datasets with known good reference
```

---

## Troubleshooting Common Issues

### Issue 1: Registration produces blurry results

**Symptoms:**
- Registered volumes appear over-smoothed
- Fine details lost compared to original

**Possible causes:**
1. Over-regularization (too much smoothness penalty)
2. Insufficient registration iterations
3. Poor template quality

**Solutions:**
```bash
# Try reducing smoothness penalty
# Edit src/registration.py, line ~150:
# Change: λ_smooth = 0.01  →  λ_smooth = 0.001

# Increase iterations
# Edit src/registration.py, line ~80:
# Change: num_iterations = 5000  →  num_iterations = 10000

# Try different template strategy
python register_nifti.py input/ output/ --template-strategy central
```

### Issue 2: Registration fails to converge

**Symptoms:**
- Loss values oscillate or increase
- Warning: "Registration did not converge"

**Possible causes:**
1. Learning rate too high
2. Extreme initial misalignment
3. Poor image quality or artifacts

**Solutions:**
```bash
# Reduce learning rate
# Edit src/registration.py, line ~120:
# Change: lr = 0.01  →  lr = 0.001

# Ensure good initial alignment
# Check center alignment output - should be < 10 mm translation

# Visual inspection of input data
python -c "
import nibabel as nib
import matplotlib.pyplot as plt
img = nib.load('input/spectral_point_000.nii.gz')
plt.imshow(img.get_fdata()[6, :, :], cmap='gray')
plt.show()
"
```

### Issue 3: "CUDA out of memory" error

**Symptoms:**
```
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB
```

**Solutions:**
```bash
# Solution 1: Reduce parallel processes
python register_nifti.py input/ output/ --processes 2

# Solution 2: Clear GPU memory between runs
python -c "import torch; torch.cuda.empty_cache()"

# Solution 3: Monitor GPU memory usage
watch -n 1 nvidia-smi

# Solution 4: Use CPU (slower but no memory limit)
# Set environment variable before running
export CUDA_VISIBLE_DEVICES=-1
python register_nifti.py input/ output/
```

### Issue 4: Very slow processing (>12 hours)

**Symptoms:**
- Registration much slower than expected
- GPU utilization low (<30%)

**Diagnostic:**
```bash
# Check if GPU is being used
nvidia-smi

# Should show Python process using GPU memory (2-4 GB)
# If not, check CUDA installation
python -c "import torch; print(torch.cuda.is_available())"
```

**Solutions:**
```bash
# If CUDA not available, install:
pip install torch --index-url https://download.pytorch.org/whl/cu118

# Verify GPU after installation
python -c "import torch; print(torch.cuda.get_device_name(0))"

# If GPU working but still slow:
# - Increase batch size in src/warper.py (if memory allows)
# - Use fewer but faster iterations
# - Consider upgrading GPU hardware
```

---

## Advanced Topics

### Customizing Registration Parameters

For advanced users who need finer control, key parameters can be modified in `src/registration.py`:

```python
# Affine registration parameters (line ~75-100)
AFFINE_CONFIG = {
    'learning_rate': 0.01,      # Increase for faster convergence (0.001-0.1)
    'num_iterations': 1500,     # Increase for better accuracy (1000-5000)
    'window_size': 7,           # LNCC window (5-11, larger = smoother)
}

# Nonlinear registration parameters (line ~200-225)
NONLINEAR_CONFIG = {
    'learning_rate': 0.001,     # Lower than affine (0.0001-0.01)
    'num_iterations': 5000,     # Main convergence parameter (3000-10000)
    'lambda_smooth': 0.01,      # Smoothness weight (0.001-0.1)
    'lambda_grad': 0.05,        # Gradient regularization (0.01-0.1)
}
```

**Effect of key parameters:**

| Parameter | Increase → | Decrease → |
|-----------|------------|------------|
| `learning_rate` | Faster but less stable | Slower but more stable |
| `num_iterations` | Better accuracy, longer time | Faster, less accurate |
| `lambda_smooth` | Smoother deformations | More detailed deformations |
| `window_size` | Spatially smoother matching | More local matching |

### Batch Processing Multiple Datasets

To register multiple phantom datasets efficiently:

```bash
#!/bin/bash
# batch_register.sh

# List of input files
input_files=(
    "data/phantom_01.mat"
    "data/phantom_02.mat"
    "data/phantom_03.mat"
)

# Process each file
for input_file in "${input_files[@]}"; do
    # Extract basename
    basename=$(basename "$input_file" .mat)
    
    # Create output directory
    output_dir="results/${basename}_registered"
    
    # Run registration module
    echo "Processing: $input_file"
    python run_registration_module.py "$input_file" "$output_dir" --processes 4
    
    # Check exit status
    if [ $? -eq 0 ]; then
        echo "✅ Successfully processed: $basename"
    else
        echo "❌ Failed: $basename"
    fi
done

echo "Batch processing complete!"
```

Run with:
```bash
chmod +x batch_register.sh
./batch_register.sh
```

### Integration with Spectral Analysis Pipeline

After registration, the aligned data can be used for downstream spectral analysis:

```python
# Example: Extract and analyze registered spectra
import h5py
import numpy as np
import matplotlib.pyplot as plt

# Load registered data
with h5py.File('phantom_registered.mat', 'r') as f:
    data = np.array(f['data'])  # Shape: (z, y, x, spectral)
    resolution = np.array(f['resolution'])

# Define region of interest (ROI)
z_slice = 6
roi_y = slice(20, 32)  # 12 voxels
roi_x = slice(45, 59)  # 14 voxels

# Extract ROI spectra
roi_spectra = data[z_slice, roi_y, roi_x, :]  # Shape: (12, 14, 31)

# Average over ROI
mean_spectrum = np.mean(roi_spectra, axis=(0, 1))  # Shape: (31,)

# Fit exponential decay model (e.g., T2 relaxation)
def exponential_decay(t, S0, T2):
    return S0 * np.exp(-t / T2)

from scipy.optimize import curve_fit

# Assuming uniform spectral sampling (adjust as needed)
t_values = np.linspace(0, 150, 31)  # 0-150 ms

# Fit
params, _ = curve_fit(exponential_decay, t_values, mean_spectrum)
S0_fit, T2_fit = params

print(f"Fitted parameters:")
print(f"  S0 = {S0_fit:.2f}")
print(f"  T2 = {T2_fit:.2f} ms")

# Plot
plt.figure(figsize=(10, 6))
plt.plot(t_values, mean_spectrum, 'bo', label='Registered data')
plt.plot(t_values, exponential_decay(t_values, *params), 'r-', 
         label=f'Fit: T2 = {T2_fit:.1f} ms')
plt.xlabel('Time (ms)')
plt.ylabel('Signal Intensity')
plt.title('T2 Decay Curve from Registered Data')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('t2_decay_analysis.png', dpi=150)
plt.show()
```

---

## Output Files Summary

After completing this tutorial, you should have the following directory structure:

```
Phantom_Registration_Tutorial/
├── Phantom_data.mat                    # Original input (2.1 MB)
│
├── phantom_nifti_output/               # NIfTI conversion
│   ├── spectral_point_000.nii.gz      # 31 volumes
│   ├── ...
│   ├── spectral_point_030.nii.gz
│   ├── spectral_point_000.png         # 5 preview images
│   ├── ...
│   └── spectral_metadata.txt
│
├── phantom_nifti_deformed/             # Deformed volumes
│   ├── spectral_point_000_deformed.nii.gz
│   ├── ...
│   └── spectral_point_030_deformed.nii.gz
│
├── phantom_deformed.mat                # Deformed data (3.2 MB)
│
├── phantom_nifti_registered/           # Registered volumes
│   ├── spectral_point_000_deformed.reg.nii.gz
│   ├── ...
│   ├── spectral_point_030_deformed.reg.nii.gz
│   └── registration_metadata.txt
│
├── phantom_registered.mat              # Final output (3.2 MB)
│
└── quality_assessment/                 # Analysis results
    ├── registration_comparison.png
    ├── spectral_profile_comparison.png
    └── t2_decay_analysis.png
```

**Disk space usage:**
- Input data: ~2 MB
- Intermediate NIfTI files: ~50-100 MB (compressed)
- Deformation fields (optional): ~200-500 MB
- Final output: ~3-4 MB
- **Total**: ~300-600 MB (can be reduced by deleting intermediate files)

---

## Summary and Next Steps

### What We Learned

In this tutorial, we:

1. ✅ **Prepared phantom spectral data** in MATLAB .mat format
2. ✅ **Converted to NIfTI format** for registration processing
3. ✅ **Applied synthetic deformations** to simulate motion artifacts
4. ✅ **Performed multi-stage registration** using GPU-accelerated methods
5. ✅ **Converted back to .mat format** with preserved metadata
6. ✅ **Assessed registration quality** quantitatively and visually

**Key takeaways:**
- Registration is essential for spectral MRI data quality
- Multi-stage approach (center → affine → nonlinear) provides robust alignment
- GPU acceleration reduces processing time from days to hours
- Quality assessment is critical for validating registration success

### Next Steps

**For phantom data analysis:**
1. **Repeat with different deformation magnitudes** to test robustness
2. **Compare registration methods** (e.g., disable nonlinear stage)
3. **Analyze spectral parameter estimation** accuracy improvement

**For clinical data processing:**
1. **Apply registration to real patient data**
2. **Integrate with existing analysis pipelines**
3. **Optimize parameters for specific acquisition protocols**

**Advanced topics to explore:**
1. **Multi-modal registration** (e.g., aligning diffusion to anatomical images)
2. **Group-wise registration** (simultaneous alignment of all volumes)
3. **Quality metrics** (mutual information, structural similarity)

### Additional Resources

- **DR-CSI Registration Documentation**: [REGISTRATION_WORKFLOW.md](REGISTRATION_WORKFLOW.md)
- **API Reference**: [API_REFERENCE.md](../docs/API_REFERENCE.md)
- **MONAI Tutorials**: https://docs.monai.io/en/stable/tutorials.html
- **Registration Theory**: 
  - Modersitzki, "FAIR: Flexible Algorithms for Image Registration"
  - Sotiras et al., "Deformable Medical Image Registration: A Survey"

---

## Feedback and Support

If you encounter issues or have questions:

1. **Check troubleshooting section** in this tutorial
2. **Review detailed documentation**: [REGISTRATION_WORKFLOW.md](REGISTRATION_WORKFLOW.md)
3. **Report issues**: https://github.com/ajoshiusc/dr-csi-reg/issues
4. **Contact**: ajoshi@usc.edu

**Happy registering! 🚀**
