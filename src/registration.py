#!/home/ajoshi/anaconda3/bin/python
# -*- coding: utf-8 -*-

import argparse
import os
from os.path import join
import SimpleITK as sitk
from aligner import Aligner
from monai.transforms import LoadImage, EnsureChannelFirst
from warper import Warper
from composedeformations import composedeformation
from applydeformation import applydeformation
from invertdeformationfield import invertdeformationfield


def create_center_aligned_transform(fixed_image, moving_image):
    """
    Create a transform that aligns the centers of two images.
    This provides better initialization for registration.
    
    Args:
        fixed_image: SimpleITK image (template)
        moving_image: SimpleITK image (to be aligned)
    
    Returns:
        SimpleITK Euler3DTransform with center-to-center translation
    """
    # Get physical centers of both images
    fixed_center = [
        fixed_image.GetOrigin()[i] + fixed_image.GetSpacing()[i] * fixed_image.GetSize()[i] / 2.0
        for i in range(3)
    ]
    
    moving_center = [
        moving_image.GetOrigin()[i] + moving_image.GetSpacing()[i] * moving_image.GetSize()[i] / 2.0
        for i in range(3)
    ]
    
    # Calculate translation needed to align centers
    translation = [fixed_center[i] - moving_center[i] for i in range(3)]
    
    # Create Euler3D transform with center alignment
    transform = sitk.Euler3DTransform()
    transform.SetTranslation(translation)
    
    print(f"Fixed image center: {fixed_center}")
    print(f"Moving image center: {moving_center}")
    print(f"Center alignment translation: {translation}")
    
    return transform


def perform_nonlinear_registration(moving, fixed, output, linloss='cc', nonlinloss='cc', le=1500, ne=5000, device='cuda'):
    """
    Perform nonlinear registration between two medical images
    
    Args:
        moving (str): Path to moving image
        fixed (str): Path to fixed/template image  
        output (str): Path for output registered image
        linloss (str): Linear loss function (default: 'cc')
        nonlinloss (str): Nonlinear loss function (default: 'cc')
        le (int): Linear epochs (default: 1500)
        ne (int): Nonlinear epochs (default: 5000)
        device (str): Computing device (default: 'cuda')
    
    Returns:
        bool: True if registration successful, False otherwise
    """
    try:
        if not os.path.exists(fixed):
            print('ERROR: file', fixed, 'does not exist.')
            return False

        if not os.path.exists(moving):
            print('ERROR: file', moving, 'does not exist.')
            return False

        subID = moving.split('.')[0]
        # Add process ID to avoid race conditions in parallel processing
        import threading
        thread_id = threading.get_ident()
        subbase = f"{subID}.rodreg.{thread_id}"

        subbase_dir = subbase + "_dir"
        os.makedirs(subbase_dir, exist_ok=True)

        centered_moving = join(subbase_dir, "moving.cent.nii.gz")
        centered_moving_linreg = join(subbase_dir, "moving.lin.nii.gz")
        lin_reg_map_file = join(subbase_dir, "lin_ddf.map.nii.gz")

        # Temporary file for nonlinear output (not used in final result)
        centered_moving_nonlinreg = join(subbase_dir, "moving.nonlin.temp.nii.gz")
        nonlin_reg_map_file = join(subbase_dir, "nonlin_ddf.map.nii.gz")
        inv_nonlin_reg_map_file = join(subbase_dir, "inv.nonlin_ddf.map.nii.gz")

        composed_ddf_file = join(subbase_dir, "composed_ddf.map.nii.gz")
        inv_composed_ddf_file = join(subbase_dir, "inv.composed_ddf.map.nii.gz")

        fixed_image = sitk.ReadImage(fixed, sitk.sitkFloat32)
        moving_image = sitk.ReadImage(moving, sitk.sitkFloat32)
        
        # Create center-to-center alignment transform for better initialization
        initial_transform = create_center_aligned_transform(fixed_image, moving_image)
        print(f"Initial center alignment translation: {initial_transform.GetParameters()[:3]}")
        
        # Skip rigid registration and use center alignment directly
        # The affine and nonlinear steps will handle the registration
        print("🔧 Skipping rigid registration - using center alignment for initialization")
        final_transform = initial_transform
        
        # Apply center alignment to get better initialized moving image
        moved_image = sitk.Resample(moving_image, fixed_image, final_transform, sitk.sitkLinear, 0.0, moving_image.GetPixelID())

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

        disp_field, _ = LoadImage(image_only=False)(lin_reg_map_file)
        disp_field = EnsureChannelFirst()(disp_field)

        nonlin_reg = Warper()
        nonlin_reg.nonlinear_reg(
            target_file=fixed,
            moving_file=centered_moving_linreg,
            output_file=centered_moving_nonlinreg,  # Temporary file (not used in final result)
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
        
        print(f"✅ Registration completed successfully: {output}")
        return True
    
    except (OSError, IOError, RuntimeError) as e:
        print(f"❌ Registration failed with error: {str(e)}")
        return False


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

    perform_nonlinear_registration(
        fixed=args.f,
        moving=args.m,
        output=args.o,
        linloss=args.linloss,
        nonlinloss=args.nonlinloss,
        le=args.le,
        ne=args.ne,
        device=args.d
    )