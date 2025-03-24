# Read mat file and save as .nii.gz files

import os
import numpy as np
import scipy.io as sio
import nibabel as nib
from nilearn import plotting
import SimpleITK as sitk

subject = "Patient1"

res = [2.3, 2.3, 5]
all_te = [65, 80, 105, 130, 160, 200]

data_dir = f"/deneb_disk/data_from_justin_03_11_2025/Data to be shared/{subject}/data"
data_out_dir = f"/deneb_disk/data_from_justin_03_11_2025/Data to be shared/{subject}/data_output"

all_img_data = []
all_b_values = []

# Read all the .mat files and extract image data
for te in all_te:
    mat_file = f"{data_dir}/TE{te}.mat"
    mat = sio.loadmat(mat_file)
    b_all = mat["b"][0]

    for i, b in enumerate(b_all):
        nii_file = f"{data_dir}/TE{te}_bval{b}.reg.nii.gz"
        img_sitk = sitk.ReadImage(nii_file)
        img_array = sitk.GetArrayFromImage(img_sitk)
        all_img_data.append(img_array)
        all_b_values.append(b)

# Convert the list to a 4D numpy array
all_img_data = np.stack(all_img_data, axis=-1)

# Save the concatenated image data to a single .mat file
output_mat_file = f"{data_out_dir}/all_data.mat"
sio.savemat(output_mat_file, {"img": all_img_data, "b": all_b_values, "te": all_te})
print(f"{output_mat_file} saved")