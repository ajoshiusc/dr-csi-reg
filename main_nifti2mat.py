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


# Read back all the NIfTI files and write back to original .mat files with modified prefix
for te in all_te:
    data_dir = f"/deneb_disk/data_from_justin_03_11_2025/Data to be shared/{subject}/data"
    data_out_dir = f"/deneb_disk/data_from_justin_03_11_2025/Data to be shared/{subject}/data_output"

    mat_file = f"{data_dir}/TE{te}.mat"
    mat = sio.loadmat(mat_file)
    b_all = mat["b"][0]

    img_data = []
    for i, b in enumerate(b_all):
        nii_file = f"{data_dir}/TE{te}_bval{b}.reg.nii.gz"
        img_sitk = sitk.ReadImage(nii_file)
        img_array = sitk.GetArrayFromImage(img_sitk)
        img_data.append(img_array)

    img_data = np.stack(img_data, axis=-1)
    new_mat_file = f"{data_out_dir}/TE{te}.reg.mat"
    sio.savemat(new_mat_file, {"img": img_data, "b": b_all})
    print(f"{new_mat_file} saved")
