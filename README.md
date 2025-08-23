# DR-CSI Registration Pipeline

A professional spectral MRI data processing pipeline for converting between .mat and NIfTI formats with registration capabilities.

## 📁 Project Structure

```
dr-csi-reg/
├── 📄 README.md                    # Project overview and quick start
├── 📄 requirements.txt             # Python dependencies
├── 📄 convert_mat_to_nifti.py     # Wrapper: .mat → NIfTI conversion
├── 📄 convert_nifti_to_mat.py     # Wrapper: NIfTI → .mat conversion  
├── 📄 register_nifti.py           # Wrapper: NIfTI registration
├── 🗂️ src/                        # Core source code
│   ├── 📄 spectral_mat_to_nifti.py      # .mat to NIfTI converter
│   ├── 📄 spectral_nifti_to_mat.py      # NIfTI to .mat converter
│   ├── 📄 nifti_registration_pipeline.py # Registration pipeline
│   └── 📄 utils.py, registration.py...   # Supporting modules
├── 🗂️ docs/                       # Documentation  
│   ├── 📄 DOCUMENTATION.md              # Detailed usage guide
│   ├── 📄 API_REFERENCE.md              # Function references
│   └── 📄 *.md                          # Project history docs
├── 🗂️ data/                       # Data files and outputs
├── 🗂️ scripts/                    # Utility scripts and job files
└── 🗂️ examples/                   # Example workflows
    └── 📄 run_complete_pipeline.py      # Complete pipeline example
```

## 🚀 Quick Start

```bash
# 1. Setup environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Convert spectral .mat to NIfTI files
python convert_mat_to_nifti.py data/data_wip_patient2.mat data/output_nifti [--res x y z]

# 3. Register all spectral files (auto-selects central template)
python register_nifti.py data/output_nifti data/registered_output

# 4. Convert back to .mat (optional verification)
python convert_nifti_to_mat.py data/registered_output data/final.mat data/data_wip_patient2.mat

# 5. Run complete pipeline example
python examples/run_complete_pipeline.py
```

## 📁 Core Scripts

| Script | Purpose |
|--------|---------|
| [`convert_mat_to_nifti.py`](src/spectral_mat_to_nifti.py) | .mat → NIfTI conversion |
| [`convert_nifti_to_mat.py`](src/spectral_nifti_to_mat.py) | NIfTI → .mat conversion |
| [`register_nifti.py`](src/nifti_registration_pipeline.py) | Generic registration |

## 📖 Documentation

See [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) for complete usage guide and [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for function references.

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
# Convert spectral data to individual NIfTI files (required arguments)
python convert_mat_to_nifti.py data/data_wip_patient2.mat data/patient2_nifti_spectral_output
# → Creates data/patient2_nifti_spectral_output/ with 31 files

# With custom resolution override
python convert_mat_to_nifti.py data/data_wip_patient2.mat data/custom_output/ --res 2.0 2.0 3.0

# Register all files using central file as template
python register_nifti.py \
    data/patient2_nifti_spectral_output \
    data/patient2_registration_output \
    --processes 4
# → Creates registered .reg.nii.gz files

# Convert back to .mat format
python convert_nifti_to_mat.py data/patient2_nifti_spectral_output data/reconstructed.mat data/data_wip_patient2.mat
```

## 💡 Advanced Usage

**Custom template:**
```bash
python register_nifti.py data/input_dir data/output_dir \
    --template data/custom_template.nii.gz --processes 8
```

**Override resolution:**
```python
# Use wrapper scripts or import directly from src/
import sys; sys.path.append('src')
from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
convert_spectral_mat_to_nifti("data/data.mat", "data/output", res=[2.0, 2.0, 3.0])
```

**Batch processing:**
```python
# Use wrapper scripts or import directly from src/
import sys; sys.path.append('src')  
from nifti_registration_pipeline import register_nifti_directory
results = register_nifti_directory("data/input", None, "data/output", num_processes=12)
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
