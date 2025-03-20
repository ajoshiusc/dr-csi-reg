# Read mat file and save as .nii.gz files

import os
import numpy as np
import scipy.io as sio
import nibabel as nib
from nilearn import plotting

subject = 'Patient1'

res = [2.3,2.3,5]
all_te = [65, 80, 105, 130, 160, 200]

for te in all_te:

    data_dir = f'/deneb_disk/data_from_justin_03_11_2025/Data to be shared/{subject}/data'
    mat_file = f'{data_dir}/TE{te}.mat'

    mat = sio.loadmat(mat_file)

    # print keys
    print(mat.keys())

    #print all the keys
    for key in mat.keys():
        print(key)


    # print the shape of the data in .img
    print('img shape', mat['img'].shape)
    b_all = mat['b'][0]
    print('b shape', b_all.shape)
    print('b values', b_all)


    # create and save multiple 3D nifti images from the 4D data
    img_data = mat['img']
    for i, b in enumerate(b_all):
        nii = nib.Nifti1Image(img_data[..., i], np.eye(4))
        nii.header.set_zooms(res)
        nib.save(nii, f'{data_dir}/TE{te}_bval{b}.nii.gz')
        print(f'{data_dir}/TE{te}_bval{b}.nii.gz saved')


    # save the image as png
    for i, b in enumerate(b_all):
        nii_file = f'{data_dir}/TE{te}_bval{b}.nii.gz'
        png_file = f'TE{te}_bval{b}.png'
        nii_img = nib.load(nii_file)
        cut_coords = [coord / 2 for coord in nii_img.shape[:3]]
        plotting.plot_anat(nii_file, display_mode='ortho', cut_coords=cut_coords, output_file=png_file)
        #display.close()
        print(f'{png_file} saved')


