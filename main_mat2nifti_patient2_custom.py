# Custom mapping version of main_mat2nifti_patient2.py
# Modify the TE and B values below according to your data

import os
import numpy as np
import scipy.io as sio
import nibabel as nib
from nilearn import plotting
import SimpleITK as sitk

# ================================
# CUSTOMIZE THESE VALUES
# ================================

# Option 1: 4 TE values × 3 B values = 12 volumes
TE_VALUES = [65, 80, 105, 130]
B_VALUES = [0, 300, 500]

# Option 2: 3 TE values × 4 B values = 12 volumes
# TE_VALUES = [65, 105, 160]  
# B_VALUES = [0, 300, 500, 1000]

# Option 3: 6 TE values × 2 B values = 12 volumes
# TE_VALUES = [65, 80, 105, 130, 160, 200]
# B_VALUES = [0, 500]

# Option 4: If you know the exact sequence, list all combinations:
# CUSTOM_MAPPING = [
#     ('TE65', 0), ('TE65', 300), ('TE65', 500),
#     ('TE80', 0), ('TE80', 300), ('TE80', 500),
#     # ... continue for all 12 volumes
# ]

# ================================

def process_with_custom_mapping():
    """Process patient2 data with custom TE/B mapping"""
    
    patient2_file = "/home/ajoshi/Projects/dr-csi-reg/data_wip_patient2.mat"
    output_dir = "/home/ajoshi/Projects/dr-csi-reg/patient2_nifti_custom_output"
    
    if not os.path.exists(patient2_file):
        print("Patient2 file not found!")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    mat = sio.loadmat(patient2_file)
    img_data = mat['data']
    resolution = mat['Resolution'][0] if 'Resolution' in mat else [1, 1, 1]
    
    print(f"Processing {img_data.shape[3]} volumes...")
    print(f"TE values: {TE_VALUES}")
    print(f"B values: {B_VALUES}")
    
    # Check if mapping makes sense
    expected_volumes = len(TE_VALUES) * len(B_VALUES)
    actual_volumes = img_data.shape[3]
    
    if expected_volumes != actual_volumes:
        print(f"ERROR: Expected {expected_volumes} volumes but found {actual_volumes}")
        print("Please adjust TE_VALUES and B_VALUES at the top of this script")
        return
    
    # Process volumes
    volume_idx = 0
    for te in TE_VALUES:
        for b in B_VALUES:
            volume = img_data[:, :, :, volume_idx]
            
            # Create SimpleITK image
            img_sitk = sitk.GetImageFromArray(volume)
            img_sitk.SetSpacing([2.3, 2.3, 5.0])  # Adjust spacing as needed
            
            # Save NIfTI file
            nii_file = f'{output_dir}/TE{te}_bval{b}.nii.gz'
            sitk.WriteImage(img_sitk, nii_file)
            print(f'{nii_file} saved')
            
            # Create PNG visualization
            png_file = f'{output_dir}/TE{te}_bval{b}.png'
            try:
                nii_img = nib.load(nii_file)
                cut_coords = [coord / 2 for coord in nii_img.shape[:3]]
                cut_coords = np.array(cut_coords) * np.array(nii_img.affine.diagonal()[:3])
                plotting.plot_anat(nii_file, display_mode='ortho', 
                                 cut_coords=cut_coords, output_file=png_file,
                                 title=f'TE{te}_bval{b}')
                print(f'{png_file} saved')
            except Exception as e:
                print(f'Warning: Could not create PNG for TE{te}_bval{b}: {e}')
            
            volume_idx += 1

if __name__ == "__main__":
    process_with_custom_mapping()
