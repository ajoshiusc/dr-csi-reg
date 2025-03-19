# Read mat file and save as .nii.gz files

import os
import numpy as np
import scipy.io as sio
import nibabel as nib
from nilearn import plotting

subject = 'Patient1'

res = [2.3,2.3,5]
te = 105
data_dir = f'/deneb_disk/data_from_justin_03_11_2025/Data to be shared/{subject}/data'
mat_file = f'{data_dir}/TE{te}.mat'

mat = sio.loadmat(mat_file)

# print keys
print(mat.keys())

#print all the keys
for key in mat.keys():
    print(key)


# print the shape of the data in .img
print(mat['img'].shape)

# create and save multiple 3D nifti images from the 4D data
img_data = mat['img']
for i in range(img_data.shape[-1]):
    nii = nib.Nifti1Image(img_data[..., i], np.eye(4))
    nii.header.set_zooms(res)
    nib.save(nii, f'{data_dir}/TE{te}_vol{i+1}.nii.gz')
    print(f'{data_dir}/TE{te}_vol{i+1}.nii.gz saved')


# save the image as png
for i in range(img_data.shape[-1]):
    nii_file = f'{data_dir}/TE{te}_vol{i+1}.nii.gz'
    png_file = f'{data_dir}/TE{te}_vol{i+1}.png'
    plotting.plot_anat(nii_file, output_file=png_file)
    print(f'{png_file} saved')


