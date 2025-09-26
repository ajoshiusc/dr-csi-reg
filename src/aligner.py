#!/usr/bin/env python3

from monai.utils import set_determinism
from monai.networks.nets import GlobalNet
from monai.config import USE_COMPILED
from monai.networks.blocks import Warp
from torch.nn import MSELoss
from monai.transforms import LoadImage, Resize, EnsureChannelFirst, ScaleIntensityRangePercentiles
from monai.losses import GlobalMutualInformationLoss, LocalNormalizedCrossCorrelationLoss
from warp_utils import apply_warp
import argparse
import torch
import nibabel as nib

import SimpleITK as sitk


class dscolors:
    red = '\033[91m'
    green = '\033[92m'
    yellow = '\033[93m'
    blue = '\033[94m'
    purple = '\033[95m'
    cyan = '\033[96m'
    clear = '\033[0m'
    bold = '\033[1m'
    ul = '\033[4m'


class Aligner:
    image_loss = MSELoss()
    nn_input_size = 64
    lr = 1e-6
    max_epochs = 5000
    device = 'cuda'

    def __init__(self):
        set_determinism(42)

    def setLoss(self, loss):
        self.loss = loss
        if loss == 'mse':
            self.image_loss = MSELoss()
        elif loss == 'cc':
            self.image_loss = LocalNormalizedCrossCorrelationLoss(kernel_size=7)
        elif loss == 'mi':
            self.image_loss = GlobalMutualInformationLoss()
        else:
            raise AssertionError('Invalid Loss')

    def loadMoving(self, moving_file):
        self.moving, self.moving_meta = LoadImage(image_only=False)(moving_file)
        self.moving = EnsureChannelFirst()(self.moving).to('cpu')

    def loadTarget(self, fixed_file):
        self.target, self.moving_meta = LoadImage(image_only=False)(fixed_file)
        self.target = EnsureChannelFirst()(self.target).to('cpu')

    def performAffine(self):
        SZ = self.nn_input_size
        moving_ds = Resize(spatial_size=[SZ, SZ, SZ])(
            self.moving).to(self.device)
        target_ds = Resize(spatial_size=[SZ, SZ, SZ])(
            self.target).to(self.device)
        moving_ds = ScaleIntensityRangePercentiles(
            lower=0.5, upper=99.5, b_min=0.0, b_max=10, clip=True)(moving_ds)
        target_ds = ScaleIntensityRangePercentiles(
            lower=0.5, upper=99.5, b_min=0.0, b_max=10, clip=True)(target_ds)

    # GlobalNet is a NN with Affine head
        reg = GlobalNet(
            image_size=(SZ, SZ, SZ),
            spatial_dims=3,
            in_channels=2,  # moving and fixed
            num_channel_initial=2,
            depth=2).to(self.device)

        if USE_COMPILED:
            warp_layer = Warp(3, padding_mode="zeros").to(self.device)
        else:
            warp_layer = Warp("bilinear", padding_mode="zeros").to(self.device)

        reg.train()
        optimizerR = torch.optim.Adam(reg.parameters(), lr=1e-6)

        for epoch in range(self.max_epochs):
            optimizerR.zero_grad()
            input_data = torch.cat((moving_ds, target_ds), dim=0)
            input_data = input_data[None, ]
            ddf_ds = reg(input_data)
            image_moved = warp_layer(moving_ds[None, ], ddf_ds)
            vol_loss = self.image_loss(image_moved, target_ds[None, ])
            vol_loss.backward()
            optimizerR.step()
            # Optimize: Print every 10 epochs and use .item() to reduce CPU overhead
            if epoch % 10 == 0 or epoch == self.max_epochs - 1:
                print('epoch_loss:', dscolors.blue, f'{vol_loss.item():.4f}', dscolors.clear,
                      ' for epoch:', dscolors.green, f'{epoch}/{self.max_epochs}', dscolors.clear, '', end='\r')

        size_moving = self.moving[0].shape
        size_target = self.target[0].shape
        ddfx = (Resize(spatial_size=size_target, mode='trilinear')(
            ddf_ds[:, 0])*(size_moving[0]/SZ)).to('cpu')
        ddfy = (Resize(spatial_size=size_target, mode='trilinear')(
            ddf_ds[:, 1])*(size_moving[1]/SZ)).to('cpu')
        ddfz = (Resize(spatial_size=size_target, mode='trilinear')(
            ddf_ds[:, 2])*(size_moving[2]/SZ)).to('cpu')
        self.ddf = torch.cat((ddfx, ddfy, ddfz), dim=0).to('cpu')
        del ddf_ds, ddfx, ddfy, ddfz

    def saveDeformationField(self, ddf_file):
        nib.save(nib.Nifti1Image(torch.permute(
            self.ddf, [1, 2, 3, 0]).detach().cpu().numpy(), self.target.affine), ddf_file)

    def saveWarpedFile(self, output_file):
        # Apply the warp
        image_movedo = apply_warp(
            self.ddf[None, ], self.moving[None, ], self.target[None, ])
        nib.save(nib.Nifti1Image(image_movedo[0, 0].detach(
        ).cpu().numpy(), self.target.affine), output_file)

    def affine_reg(self, fixed_file, moving_file, output_file, ddf_file, loss='mse', nn_input_size=64, lr=1e-6, max_epochs=5000, device='cuda'):
        # Check GPU availability and handle device assignment to avoid race conditions
        import torch
        if device == "cuda" and not torch.cuda.is_available():
            print("⚠️  CUDA not available, falling back to CPU")
            device = "cpu"
        elif device == "cuda":
            # Use current GPU context to avoid conflicts in parallel processing
            gpu_id = torch.cuda.current_device() if torch.cuda.device_count() > 0 else 0
            print(f"🔧 Using GPU {gpu_id} for affine registration")
            torch.cuda.set_device(gpu_id)
            
        self.setLoss(loss)
        self.nn_input_size = nn_input_size
        self.lr = lr,
        self.max_epochs = max_epochs
        self.device = device
        self.loadMoving(moving_file)
        self.loadTarget(fixed_file)
        self.performAffine()
        self.saveWarpedFile(output_file)

        if ddf_file is not None:
            self.saveDeformationField(ddf_file)


def center_and_resample_images(sub_img, atlas_img, centered_atlas, atlas_labels=None, centered_atlas_labels=None):
    """
    Centers and resamples the given images using a multiresolution registration algorithm.

    Args:
            sub_img (str): Filepath to the subject's preoperative T2-weighted MRI image.
            atlas_img (str): Filepath to the atlas's preoperative T2-weighted MRI image.
            centered_atlas (str): Filepath to save the centered and resampled atlas.
            atlas_labels (str): Filepath to the atlas's segmentation labels.
            centered_atlas_labels (str): Filepath to save the centered and resampled atlas labels.
    Returns:
            None
    """
    fixed_image = sitk.ReadImage(sub_img, sitk.sitkFloat32)
    moving_image = sitk.ReadImage(atlas_img, sitk.sitkFloat32)
    initial_transform = sitk.CenteredTransformInitializer(
        fixed_image,
        moving_image,
        sitk.Euler3DTransform(),
        sitk.CenteredTransformInitializerFilter.GEOMETRY,
    )

    final_transform, _ = multires_registration(
        fixed_image, moving_image, initial_transform)

    moved_image = sitk.Resample(moving_image, fixed_image, final_transform)

    sitk.WriteImage(moved_image, centered_atlas)

    if atlas_labels is not None and centered_atlas_labels is not None:

        print('Moving labels to subject space...')
        moving_image = sitk.ReadImage(atlas_labels, sitk.sitkUInt16)
        moved_image = sitk.Resample(
            moving_image,
            fixed_image,
            transform=final_transform,
            interpolator=sitk.sitkNearestNeighbor,
        )
        sitk.WriteImage(moved_image, centered_atlas_labels)


def multires_registration(fixed_image, moving_image, initial_transform):
    """ 
    Utility function for center_and_resample_images. 
    """
    registration_method = sitk.ImageRegistrationMethod()
    registration_method.SetMetricAsMattesMutualInformation(
        numberOfHistogramBins=50)
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    registration_method.SetMetricSamplingPercentage(0.01)
    registration_method.SetInterpolator(sitk.sitkLinear)
    registration_method.SetOptimizerAsGradientDescent(
        learningRate=1.0, numberOfIterations=100, estimateLearningRate=registration_method.Once)
    registration_method.SetOptimizerScalesFromPhysicalShift()
    registration_method.SetInitialTransform(initial_transform, inPlace=False)
    registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
    registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
    registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    final_transform = registration_method.Execute(fixed_image, moving_image)
    print('Final metric value: {0}'.format(
        registration_method.GetMetricValue()))
    print('Optimizer\'s stopping condition, {0}'.format(
        registration_method.GetOptimizerStopConditionDescription()))
    return (final_transform, registration_method.GetMetricValue())


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Affine registration for mouse brains')

    parser.add_argument('moving_file', type=str, help='moving file name')
    parser.add_argument('fixed_file', type=str, help='fixed file name')
    parser.add_argument('output_file', type=str, help='output file name')
    parser.add_argument('-ddf', '--ddf-file', type=str,
                        help='dense displacement field file name')
    parser.add_argument('--nn_input_size', type=int, default=64,
                        help='size of the neural network input (default: 64)')
    parser.add_argument('--lr', type=float, default=1e-6,
                        help='learning rate (default: 1e-4)')
    parser.add_argument('-e', '--max-epochs', type=int,
                        default=1500, help='maximum interations')
    parser.add_argument('-d', '--device', type=str,
                        default='cuda', help='device: cuda, cpu, etc.')
    parser.add_argument('-l', '--loss', type=str, default='mse',
                        help='loss function: mse, cc or mi')

    args = parser.parse_args()
    # print(args)
    aligner = Aligner()
    aligner.affine_reg(fixed_file=args.fixed_file, moving_file=args.moving_file, output_file=args.output_file, ddf_file=args.ddf_file,
                       loss=args.loss, nn_input_size=args.nn_input_size, lr=args.lr, max_epochs=args.max_epochs, device=args.device)


if __name__ == "__main__":
    main()
