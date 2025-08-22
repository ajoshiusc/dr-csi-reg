# Spectral MRI Data Processing Pipeline

A Python toolkit for converting and processing spectral MRI data between MATLAB (.mat) and NIfTI formats, with advanced registration capabilities.

## 🚀 Quick Start

```bash
# 1. Setup environment
python -m venv .venv
source .venv/bin/activate
pip install scipy nibabel nilearn SimpleITK numpy matplotlib opencv-python

# 2. Convert spectral .mat to NIfTI files
python main_mat2nifti_spectral.py

# 3. Register all spectral files (auto-selects central template)
python main_register2template_enhanced.py input_dir output_dir

# 4. Convert back to .mat (optional verification)
python main_nifti2mat_spectral.py
```

## 📁 Core Scripts

| Script | Purpose |
|--------|---------|
| [`main_mat2nifti_spectral.py`](DOCUMENTATION.md#main_mat2nifti_spectralpy) | .mat → NIfTI conversion |
| [`main_nifti2mat_spectral.py`](DOCUMENTATION.md#main_nifti2mat_spectralpy) | NIfTI → .mat conversion |
| [`main_register2template_enhanced.py`](DOCUMENTATION.md#main_register2template_enhancedpy) | Generic registration |

## 📖 Documentation

See [DOCUMENTATION.md](DOCUMENTATION.md) for complete usage guide, API reference, and examples.

## 🔧 Data Format

**Input .mat structure:**
```python
{
    'data': (31, 104, 52, 12),        # (spectral_points, x, y, z)
    'Resolution': [[1, 1, 1]],        # [x_res, y_res, z_res] in mm
    'spatial_dim': [[104, 52, 12]]    # Spatial dimensions
}
```

**Output:** 31 individual NIfTI files (`spectral_point_000.nii.gz` ... `spectral_point_030.nii.gz`)

## 🏃‍♂️ Example Workflow

```bash
# Convert spectral data to individual NIfTI files
python main_mat2nifti_spectral.py
# → Creates patient2_nifti_spectral_output/ with 31 files

# Register all files using central file as template
python main_register2template_enhanced.py \
    patient2_nifti_spectral_output \
    patient2_registration_output \
    --processes 4
# → Creates registered .reg.nii.gz files
```

## 💡 Advanced Usage

**Custom template:**
```bash
python main_register2template_enhanced.py input_dir output_dir \
    --template custom_template.nii.gz --processes 8
```

**Override resolution:**
```python
from main_mat2nifti_spectral import process_spectral_format
process_spectral_format("data.mat", "output", res=[2.0, 2.0, 3.0])
```

**Batch processing:**
```python
from main_register2template_enhanced import process_directory_registration
results = process_directory_registration("input", None, "output", num_processes=12)
```

## 🎨 Visualizations

The pipeline automatically generates:
- PNG previews of first 5 spectral points
- Orthogonal view visualizations
- Processing metadata and statistics


## 📋 Requirements

- Python 3.11+
- Virtual environment recommended
- ~2GB RAM for typical spectral datasets
- SimpleITK, scipy, nibabel, nilearn, numpy

---

*This pipeline provides a complete solution for spectral MRI data processing with modern Python practices, comprehensive error handling, and perfect data preservation.*
