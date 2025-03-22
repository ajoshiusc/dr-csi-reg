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


def nonlin_register(moving, fixed, output, linloss='cc', nonlinloss='cc', le=1500, ne=5000, device='cuda'):
    if not os.path.exists(fixed):
        print('ERROR: file', fixed, 'does not exist.')
        sys.exit(2)

    if not os.path.exists(moving):
        print('ERROR: file', moving, 'does not exist.')
        sys.exit(2)


    subID = moving.split('.')[0]
    subbase = subID + '.rodreg'

    subbase_dir = subbase + "_dir"
    os.makedirs(subbase_dir, exist_ok=True)

    centered_moving = join(subbase_dir, "moving.cent.nii.gz")
    cent_transform_file = join(subbase_dir, "cent.reg.tfm")
    inv_cent_transform_file = join(subbase_dir, "cent.reg.inv.tfm")

    centered_moving_linreg = join(subbase_dir, "moving.lin.nii.gz")
    lin_reg_map_file = join(subbase_dir, "lin_ddf.map.nii.gz")

    centered_moving_nonlinreg = join(subbase_dir, "moving.nonlin.nii.gz")
    nonlin_reg_map_file = join(subbase_dir, "nonlin_ddf.map.nii.gz")
    inv_nonlin_reg_map_file = join(subbase_dir, "inv.nonlin_ddf.map.nii.gz")

    composed_ddf_file = join(subbase_dir, "composed_ddf.map.nii.gz")
    inv_composed_ddf_file = join(subbase_dir, "inv.composed_ddf.map.nii.gz")

    fixed_image = sitk.ReadImage(fixed, sitk.sitkFloat32)
    moving_image = sitk.ReadImage(moving, sitk.sitkFloat32)
    
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

    sitk.WriteImage(moved_image, centered_moving)

    aligner = Aligner()
    aligner.affine_reg(
        fixed_file=fixed,
        moving_file=centered_moving,
        output_file=centered_moving_linreg,
        ddf_file=lin_reg_map_file,
        loss=linloss,
        device=device,
        max_epochs=le
    )

    disp_field, meta = LoadImage(image_only=False)(lin_reg_map_file)
    disp_field = EnsureChannelFirst()(disp_field)

    nonlin_reg = Warper()
    nonlin_reg.nonlinear_reg(
        target_file=fixed,
        moving_file=centered_moving_linreg,
        output_file=centered_moving_nonlinreg,
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

    # Apply the composed deformation field to the moving image
    applydeformation(centered_moving, composed_ddf_file, output)



    # Invert the composed deformation field this takes about 5-7 min
    invertdeformationfield(composed_ddf_file, inv_composed_ddf_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runs rodreg full registration pipeline')
    parser.add_argument('-m', type=str, help='Input subject file', required=True)
    parser.add_argument('-f', type=str, help='Reference image file ', required=True)
    parser.add_argument('-o', type=str, help='Output file name (non-linearly warped image).', required=True)
    parser.add_argument('--linloss', type=str, help='Type of loss function for linear registration', 
                        default = 'cc', choices=['mse', 'cc', 'mi'], required=False)
    parser.add_argument('--nonlinloss', type=str, help='Type of loss function for non-linear registration', 
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
        fixed=args.f,
        moving=args.m,
        output=args.o,
        linloss=args.linloss,
        nonlinloss=args.nonlinloss,
        le=args.le,
        ne=args.ne,
        device=args.d
    )