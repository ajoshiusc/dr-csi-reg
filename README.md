# DR-CSI Registration Module

**Part of the Diffusion-Relaxation Suite**

A robust spectral MRI data nonlinear registration module with. This module provides specialized tools for registering diffusion-relaxation spectral imaging data within the broader Diffusion-Relaxation Suite.

## 🚀 Quick Start - Module Usage

```bash
# 1. Setup environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 2. Run complete workflow (recommended)
python run_registration_module.py data/data_wip_patient2.mat output_results

# OR run individual steps:

# 2a. Convert spectral .mat to NIfTI files
python convert_mat_to_nifti.py data/data_wip_patient2.mat data/output_nifti

# 2b. Register all spectral files (auto-selects central template)
   # With custom template and parallel processing
   python register_nifti.py data/workflow_nifti data/registered_nifti --template data/workflow_nifti/spectral_point_000.nii.gz --processes 4

# 2c. Convert back to .mat with preserved metadata
python convert_nifti_to_mat.py data/registered_output data/final.mat data/data_wip_patient2.mat
```

## 📁 Project Structure

```
dr-csi-reg/
├── 📄 run_registration_module.py      # Complete automated module workflow (recommended)
├── 📄 convert_mat_to_nifti.py        # Wrapper: .mat → NIfTI conversion
├── 📄 convert_nifti_to_mat.py        # Wrapper: NIfTI → .mat conversion
├── 📄 register_nifti.py              # Wrapper: Enhanced registration module  
├── 🗂️ src/                           # Core source code
│   ├── 📄 spectral_mat_to_nifti.py       # .mat to NIfTI converter
│   ├── 📄 spectral_nifti_to_mat.py       # NIfTI to .mat converter (metadata preservation)
│   ├── 📄 nifti_registration_pipeline.py # Registration with race condition protection
│   ├── 📄 registration.py                # Center alignment + PyTorch/MONAI registration
│   ├── 📄 aligner.py, warper.py          # GPU-managed registration components
│   └── 📄 utils.py, *.py                 # Supporting utilities
├── 🗂️ docs/                          # Comprehensive documentation
│   ├── 📄 DOCUMENTATION.md               # Complete usage guide
│   ├── 📄 IMPROVEMENTS_SUMMARY.md        # Recent enhancements summary
│   └── 📄 API_REFERENCE.md, *.md         # Technical references
└── 🗂️ data/                          # Input data and outputs
```

## ⚠️ Important Requirements & Timing

### **GPU Requirement for Registration**
- **Registration step requires NVIDIA GPU** with CUDA support
- Minimum 4GB GPU memory recommended for typical spectral datasets
- Automatic fallback to CPU if CUDA not available (slower)

### **Processing Time Estimates**
- **Conversion (.mat ↔ NIfTI)**: ~30 seconds - 2 minutes
- **Registration**: **3-4 hours** for typical spectral datasets (GPU-accelerated)
- **Full Module Workflow**: Use `python run_registration_module.py <input.mat> <output_dir>` for complete automation
- Complete module processing: Allow 4-5 hours total processing time

### **System Requirements**
- Python 3.11+
- NVIDIA GPU with CUDA support (recommended)
- 4GB+ GPU memory (recommended)
- 16GB+ system RAM
- ~5GB free disk space for outputs

## 📁 Core Scripts

| Script | Purpose |
|--------|---------|
| [`convert_mat_to_nifti.py`](src/spectral_mat_to_nifti.py) | .mat → NIfTI conversion |
| [`convert_nifti_to_mat.py`](src/spectral_nifti_to_mat.py) | NIfTI → .mat conversion |
| [`register_nifti.py`](src/nifti_registration_pipeline.py) | Generic registration |

## 📖 Documentation

See [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) for complete usage guide and [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for function references.

## 🔧 Registration Module Details

### **Enhanced Registration Module Workflow**
1. **Center Alignment**: Aligns image centers using SimpleITK transforms
2. **Affine Registration**: PyTorch/MONAI-based robust affine alignment  
3. **Non-linear Registration**: PyTorch/MONAI-based deformable registration
4. **Composition**: Combines transformations for final output

### **Template Selection for Registration**
- **Automatic Selection**: If no template is specified, the system automatically selects the central/middle volume from all spectral files as the reference
- **Selection Logic**: Files are sorted alphabetically, and the middle file is chosen (e.g., for N files, file at index N//2 is selected)
- **Rationale**: The central volume typically provides optimal signal-to-noise ratio and represents a balanced point in the spectral range
- **Custom Override**: You can specify a different template using `--template` option if needed
- **Example**: For spectral files 000-030, volume 015 would be automatically selected as the reference template

### **Parallel Processing Notes**
- Default: `--processes 4` (can be adjusted based on system resources)
- Race condition protection: Atomic file locking prevents collisions
- Thread-safe temporary files: Process-specific naming prevents overwrites

## 🔧 Data Format

**Input .mat structure:**
```python
```python
{
    'data': np.array(...),            # 4D spectral data
    'resolution': [[1, 1, 1]],        # [x_res, y_res, z_res] in mm
    'spatial_dim': [[32, 32, 16]],    # [x_dim, y_dim, z_dim] (optional)
    'transform': np.eye(4),           # Transform matrix (preserved)
}
```

**Processing Flow:**
- **Step 1**: `.mat` → Individual NIfTI files (e.g., `spectral_point_000.nii.gz` ... `spectral_point_030.nii.gz`)
- **Step 2**: Registration → Registered files (e.g., `spectral_point_000.reg.nii.gz` ... `spectral_point_030.reg.nii.gz`) 
- **Step 3**: NIfTI → `.mat` with **ALL original fields preserved** including **original data types** except updated `data`

## 🏃‍♂️ Example Workflows

### **Recommended: Full Automated Module Workflow**
```bash
# Single command to run complete module workflow
python run_registration_module.py data/input.mat results/output_dir
# → Converts .mat → NIfTI → Register → Final .mat
# → Uses parallel processing with race condition protection
# → Preserves all original metadata fields
```

**Usage:**
```bash
# Basic usage (4 parallel processes by default)
python run_registration_module.py <input_mat_file> <output_directory>

# With custom parallel processes
python run_registration_module.py <input_mat_file> <output_directory> --processes <num>

# Examples:
python run_registration_module.py data/patient1.mat results/patient1
python run_registration_module.py /path/to/data.mat /path/to/output --processes 8
```

**Output Structure:**
```
output_directory/
├── nifti/                    # Converted NIfTI files
├── registration/             # Registered NIfTI files  
└── {input_name}_registered.mat   # Final registered .mat file
```

### **Manual Step-by-Step Workflow**
```bash
# Convert spectral data to individual NIfTI files
python convert_mat_to_nifti.py data/data_wip_patient2.mat data/patient2_nifti_output
# → Creates data/patient2_nifti_output/ with multiple spectral files

# Register all files using center alignment + PyTorch/MONAI
python register_nifti.py \
    data/patient2_nifti_output \
    data/patient2_registration_output \
    --processes 4
# → Creates registered .reg.nii.gz files
# → Automatically selects central volume as template (e.g., volume 015 for files 000-030)
# → Uses center alignment (no SimpleITK errors)
# → Takes 3-4 hours for typical datasets

# Convert back to .mat format with metadata preservation
python convert_nifti_to_mat.py \
    data/patient2_registration_output \
    data/reconstructed.mat \
    data/data_wip_patient2.mat
# → Preserves ALL original .mat fields and data types except 'data'
```

### **Custom Resolution Override**
```bash
# Convert with custom voxel spacing
python convert_mat_to_nifti.py data/data_wip_patient2.mat data/custom_output/ --res 2.0 2.0 3.0
```

### **Custom Template Registration**
```bash
# Use specific template file instead of auto-selected central file
python register_nifti.py data/input_dir data/output_dir \
    --template data/custom_template.nii.gz --processes 4

# Example: Force use of first volume as template
python register_nifti.py data/input_dir data/output_dir \
    --template data/input_dir/spectral_point_000.nii.gz --processes 4
```

## 💡 Advanced Usage

### **Full Module Workflow Script (Recommended)**
```bash
# Automated complete module workflow with monitoring
python run_registration_module.py data/input.mat results/output --processes 8

# Monitor progress in another terminal
tail -f results/output/registration_log.txt
```

### **Custom Parameters**
```bash
# Custom parallel processes (adjust based on system resources)
python register_nifti.py data/input data/output --processes 4

# Custom template file
python register_nifti.py data/input data/output --template data/my_template.nii.gz

# Custom file pattern
python register_nifti.py data/input data/output --pattern "spectral_point_0[0-9].nii.gz"
```

### **Programmatic Usage**
```python
# Direct function calls (run from src/ directory)
import os
os.chdir('src')

from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
from nifti_registration_pipeline import register_nifti_directory  
from spectral_nifti_to_mat import convert_spectral_nifti_to_mat

# Step 1: Convert to NIfTI
convert_spectral_mat_to_nifti("../data/input.mat", "../data/nifti", res=[2.0, 2.0, 3.0])

# Step 2: Register files
register_nifti_directory("../data/nifti", None, "../data/registered", num_processes=4)

# Step 3: Convert back with metadata preservation  
convert_spectral_nifti_to_mat("../data/registered", "../data/output.mat", "../data/input.mat")
```

## 🎨 Visualizations

The module automatically generates:
- PNG previews of first 5 spectral points
- Orthogonal view visualizations
- Processing metadata and statistics


## 📋 Requirements

- Python 3.11+
- **NVIDIA GPU with CUDA support** (required for registration)
- 4GB+ GPU memory (recommended)
- 16GB+ system RAM 
- Virtual environment recommended
- Dependencies: SimpleITK, scipy, nibabel, nilearn, numpy, torch, monai

**⚠️ Note:** Registration module requires GPU acceleration and can take 3-4 hours for typical datasets.

---
