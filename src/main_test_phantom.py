from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
import glob
import os
import torch
import nibabel as nib
import numpy as np
from monai.transforms import Rand3DElastic
from monai.utils import InterpolateMode


def apply_nonlinear_deformation_to_nifti_files(nifti_dir, output_dir, sigma_range=[6, 8], magnitude_range=[100, 300]):
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
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all NIFTI files from the directory
    nifti_files = sorted(glob.glob(f"{nifti_dir}/spectral_point_*.nii.gz"))
    print(f"\nFound {len(nifti_files)} NIFTI files to deform")
    
    # Apply random nonlinear deformation to each NIFTI file
    for nifti_file in nifti_files:
        print(f"Processing: {nifti_file}")
        
        # Load NIFTI file
        img = nib.load(nifti_file)
        volume = img.get_fdata()
        affine = img.affine
        
        # Convert to tensor with proper dimensions for MONAI (1, 1, H, W, D)
        volume_tensor = torch.from_numpy(volume).float().unsqueeze(0).unsqueeze(0)
        
        # Apply MONAI's Rand3DElastic for random nonlinear deformation
        elastic_transform = Rand3DElastic(
            sigma_range=sigma_range,
            magnitude_range=magnitude_range,
            prob=1.0,
            mode=InterpolateMode.BILINEAR,
            padding_mode="border"
        )
        
        # Apply deformation
        deformed_tensor = elastic_transform(volume_tensor[0])
        deformed_volume = deformed_tensor.squeeze(0).numpy()
        
        # Create output filename with "_deformed" suffix
        basename = os.path.basename(nifti_file)
        output_file = os.path.join(output_dir, basename.replace(".nii.gz", "_deformed.nii.gz"))
        
        # Save deformed volume to new file
        deformed_img = nib.Nifti1Image(deformed_volume, affine)
        deformed_img.set_sform(affine, code=1)
        deformed_img.set_qform(affine, code=1)
        nib.save(deformed_img, output_file)
        print(f"  ✅ Saved deformed volume to: {output_file}")
    
    print(f"\n✅ Applied nonlinear deformation to all {len(nifti_files)} files\n")
    return output_dir


input_mat = "/home/ajoshi/Downloads/Phantom_data.mat"
output_dir = "phantom_nifti_output"
deformed_dir = "phantom_nifti_deformed"

convert_spectral_mat_to_nifti(input_mat, output_dir)
apply_nonlinear_deformation_to_nifti_files(output_dir, deformed_dir)

# do the registration
from nifti_registration_pipeline import register_nifti

register_nifti(deformed_dir, deformed_dir + "_registered", processes=1)
from spectral_nifti_to_mat import convert_spectral_nifti_to_mat

convert_spectral_nifti_to_mat(deformed_dir + "_registered", "phantom_reconstructed.mat")

# Verify the output
import scipy.io as sio  

reconstructed_data = sio.loadmat("phantom_reconstructed.mat")
print("Reconstructed data keys:", reconstructed_data.keys())
print("Reconstructed data shape:", reconstructed_data['data'].shape)