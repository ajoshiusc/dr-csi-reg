import glob
import os
import torch
import nibabel as nib
import numpy as np

from monai.transforms import Rand3DElastic
from monai.utils import InterpolateMode
from monai.utils import set_determinism
set_determinism(seed=42)

def apply_nonlinear_deformation_to_nifti_files(nifti_dir, output_dir, sigma_range=None, magnitude_range=None):
    """
    Apply random nonlinear deformation to all NIFTI files in a directory and save to a new directory.
    Args:
        nifti_dir (str): Directory containing NIFTI files
        output_dir (str): Directory to save deformed NIFTI files
        sigma_range (list): Controls smoothness of deformation
        magnitude_range (list): Controls magnitude of displacement
    Returns:
        str: Path to the output directory containing deformed files
    """
    if sigma_range is None:
        sigma_range = [6, 8]
    if magnitude_range is None:
        magnitude_range = [100, 300]
    os.makedirs(output_dir, exist_ok=True)
    nifti_files = sorted(glob.glob(f"{nifti_dir}/spectral_point_*.nii.gz"))
    print(f"\nFound {len(nifti_files)} NIFTI files to deform")
    for nifti_file in nifti_files:
        print(f"Processing: {nifti_file}")
        img = nib.load(nifti_file)
        volume = img.get_fdata()
        affine = img.affine
        original_dtype = volume.dtype  # Preserve original dtype
        
        # Convert to tensor - keep original dtype
        volume_tensor = torch.from_numpy(volume).unsqueeze(0).unsqueeze(0)
        
        elastic_transform = Rand3DElastic(
            sigma_range=sigma_range,
            magnitude_range=magnitude_range,
            prob=1.0,
            mode=InterpolateMode.BILINEAR,
            padding_mode="border", 
        )
        deformed_tensor = elastic_transform(volume_tensor[0])
        deformed_volume = deformed_tensor.squeeze(0).numpy()
        
        # Restore original data type (MONAI may have changed it)
        deformed_volume = deformed_volume.astype(original_dtype)
        basename = os.path.basename(nifti_file)
        output_file = os.path.join(output_dir, basename.replace(".nii.gz", "_deformed.nii.gz"))
        deformed_img = nib.Nifti1Image(deformed_volume, affine)
        deformed_img.set_sform(affine, code=1)
        deformed_img.set_qform(affine, code=1)
        nib.save(deformed_img, output_file)
        print(f"  ✅ Saved deformed volume to: {output_file}")
    print(f"\n✅ Applied nonlinear deformation to all {len(nifti_files)} files\n")
    return output_dir
