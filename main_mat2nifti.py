# Read mat file and save as .nii.gz files

import os
import numpy as np
import scipy.io as sio
import nibabel as nib
from nilearn import plotting
import SimpleITK as sitk

#subject = 'Patient1'
#res = [2.3,2.3,5]
#all_te = [65, 80, 105, 130, 160, 200]
subject = "wip_patient2"
res = [2.3, 2.3, 5]
all_te = [63, 80, 105, 130, 160, 200, 300]

data_dir = f'/project/ajoshi_27/data_from_justin_03_11_2025/Data to be shared/{subject}/data'

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



for te in all_te:

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
        img_sitk = sitk.GetImageFromArray(img_data[..., i])
        img_sitk.SetSpacing([res[2], res[0], res[1]]) # Slice is first in sitk
        sitk.WriteImage(img_sitk, f'{data_dir}/TE{te}_bval{b}.nii.gz')
        print(f'{data_dir}/TE{te}_bval{b}.nii.gz saved')


    # save the image as png
    for i, b in enumerate(b_all):
        nii_file = f'{data_dir}/TE{te}_bval{b}.nii.gz'
        png_file = f'TE{te}_bval{b}.png'
        nii_img = nib.load(nii_file)
        cut_coords = [coord / 2 for coord in nii_img.shape[:3]]
        cut_coords = np.array(cut_coords) * np.array(nii_img.affine.diagonal()[:3])
        #cut_coords = [cut_coords[2], cut_coords[1], cut_coords[0]]
        plotting.plot_anat(nii_file, display_mode='ortho', cut_coords=cut_coords, output_file=png_file)
        #display.close()
        print(f'{png_file} saved')


