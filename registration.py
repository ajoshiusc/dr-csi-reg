#!/home/ajoshi/anaconda3/bin/python
# -*- coding: utf-8 -*-

import nibabel as nib
import numpy as np
import argparse
import sys
import os
from os.path import join
import nilearn.image as ni
import nibabel as nb
import SimpleITK as sitk
from pathlib import Path
from utils import pad_nifti_image, multires_registration, interpolate_zeros
from aligner import Aligner
from warp_utils import apply_warp
from monai.transforms import LoadImage, EnsureChannelFirst
from warper import Warper
from composedeformations import composedeformation
from applydeformation import applydeformation
from invertdeformationfield import invertdeformationfield


def nonlin_register(inputT2, atlas_brain, centered_atlas_nonlinreg, linloss='cc', nonlinloss='cc', le=1500, ne=5000, device='cuda'):
    if not os.path.exists(inputT2):
        print('ERROR: file', inputT2, 'does not exist.')
        sys.exit(2)

    if not os.path.exists(atlas_brain):
        print('ERROR: file', atlas_brain, 'does not exist.')
        sys.exit(2)


    subID = inputT2.split('.')[0]
    subbase = subID + '.rodreg'


    centered_atlas = subbase+".atlas.cent.nii.gz"
    cent_transform_file = subbase+".cent.reg.tfm"
    inv_cent_transform_file = subbase+".cent.reg.inv.tfm"

    centered_atlas_linreg = subbase+".atlas.lin.nii.gz"
    lin_reg_map_file = subbase+".lin_ddf.map.nii.gz"

    nonlin_reg_map_file = subbase+".nonlin_ddf.map.nii.gz"
    inv_nonlin_reg_map_file = subbase+".inv.nonlin_ddf.map.nii.gz"

    composed_ddf_file = subbase+".composed_ddf.map.nii.gz"
    inv_composed_ddf_file = subbase+".inv.composed_ddf.map.nii.gz"
    full_deformed_subject = subbase+".full.deformed.nii.gz"


    fixed_image = sitk.ReadImage(inputT2, sitk.sitkFloat32)
    moving_image = sitk.ReadImage(atlas_brain, sitk.sitkFloat32)
    
    initial_transform = sitk.CenteredTransformInitializer(
        fixed_image,
        moving_image,
        sitk.Euler3DTransform(),
        sitk.CenteredTransformInitializerFilter.GEOMETRY,
    )

    final_transform, _ = multires_registration(fixed_image, moving_image, initial_transform)

    # save the transformation in a file
    sitk.WriteTransform(final_transform, cent_transform_file)

    # invert the transform and also save to a file
    inv_transform = final_transform.GetInverse()
    sitk.WriteTransform(inv_transform, inv_cent_transform_file)

    moved_image = sitk.Resample(moving_image, fixed_image, initial_transform, sitk.sitkLinear, 0.0, moving_image.GetPixelID())

    sitk.WriteImage(moved_image, centered_atlas)

    aligner = Aligner()
    aligner.affine_reg(
        fixed_file=inputT2,
        moving_file=centered_atlas,
        output_file=centered_atlas_linreg,
        ddf_file=lin_reg_map_file,
        loss=linloss,
        device=device,
        max_epochs=le
    )

    disp_field, meta = LoadImage(image_only=False)(lin_reg_map_file)
    disp_field = EnsureChannelFirst()(disp_field)

    nonlin_reg = Warper()
    nonlin_reg.nonlinear_reg(
        target_file=inputT2,
        moving_file=centered_atlas,
        output_file=centered_atlas_nonlinreg,
        ddf_file=nonlin_reg_map_file,
        inv_ddf_file=inv_nonlin_reg_map_file,
        reg_penalty=1,
        nn_input_size=64,
        lr=1e-4,
        max_epochs=ne,
        loss=nonlinloss,
        device=device,
    )

    
    composedeformation(nonlin_reg_map_file, lin_reg_map_file, composed_ddf_file)

    # Invert the composed deformation field this takes about 5-7 min
    invertdeformationfield(composed_ddf_file, inv_composed_ddf_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runs rodreg full registration pipeline.')
    parser.add_argument('-i', type=str, help='Input subject file.', required=True)
    parser.add_argument('-r', type=str, help='Reference image file prefix.', required=True)
    parser.add_argument('-o', type=str, help='Output file name (non-linearly warped image).', required=True)
    parser.add_argument('--linloss', type=str, help='Type of loss function for linear registration.', 
                        default = 'cc', choices=['mse', 'cc', 'mi'], required=False)
    parser.add_argument('--nonlinloss', type=str, help='Type of loss function for non-linear registration.', 
                        default = 'cc', choices=['mse', 'cc', 'mi'], required=False)
    parser.add_argument(
        "--le", type=int, default=1500, help="Maximum interations for linear registration"
    )
    parser.add_argument(
        "--ne", type=int, default=5000, help="Maximum interations for non-linear registration"
    )
    parser.add_argument(
        "--d", "--device", type=str, default="cuda", help="device: cuda, cpu, etc."
    )
        
    args = parser.parse_args()

    nonlin_register(
        inputT2=args.i,
        atlas_brain=args.r,
        centered_atlas_nonlinreg=args.o,
        linloss=args.linloss,
        nonlinloss=args.nonlinloss,
        le=args.le,
        ne=args.ne,
        device=args.d
    )