# Read mat file and save as .nii.gz files

import os
import numpy as np
import scipy.io as sio
import nibabel as nib
from nilearn import plotting
import SimpleITK as sitk

subject = "wip_sub8 (H)"

data_dir = f'/project/ajoshi_27/data/data_from_justin_03_11_2025/Data to be shared/{subject}/data'
data_out_dir = f'/project/ajoshi_27/data/data_from_justin_03_11_2025/Data to be shared/{subject}/data_output'

os.makedirs(data_out_dir)

res = [2.3, 2.3, 5]

# load the list of mat files and get the values of TEs from the file names
all_te = []

for filename in os.listdir(data_dir):
    if filename.endswith('.mat'):
        # extract the TE value from the filename
        te = int(filename.split('TE')[1].split('.')[0])
        all_te.append(te)
all_te = sorted(all_te)
#print all the TE values
print('TE values:', all_te)


# Read back all the NIfTI files and write back to original .mat files with modified prefix
for te in all_te:
    


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
