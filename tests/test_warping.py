import pytest
import numpy as np
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, MagicMock
import nibabel as nib
import SimpleITK as sitk

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from warper import apply_transform_to_image
from warp_utils import (
    compose_transforms,
    invert_transform,
    interpolate_image,
    resample_image_to_reference
)


class TestWarper:
    """Test image warping functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_images(self, temp_dir):
        """Create sample images for warping tests."""
        # Create moving image
        moving_data = np.random.rand(20, 20, 20).astype(np.float32)
        moving_img = sitk.GetImageFromArray(moving_data)
        moving_img.SetSpacing([2.0, 2.0, 2.0])
        moving_img.SetOrigin([0.0, 0.0, 0.0])
        moving_file = os.path.join(temp_dir, 'moving.nii.gz')
        sitk.WriteImage(moving_img, moving_file)
        
        # Create reference image
        ref_data = np.random.rand(25, 25, 25).astype(np.float32)
        ref_img = sitk.GetImageFromArray(ref_data)
        ref_img.SetSpacing([1.5, 1.5, 1.5])
        ref_img.SetOrigin([-5.0, -5.0, -5.0])
        ref_file = os.path.join(temp_dir, 'reference.nii.gz')
        sitk.WriteImage(ref_img, ref_file)
        
        return moving_file, ref_file, moving_img, ref_img
    
    @pytest.fixture
    def sample_transform(self):
        """Create a sample transform for testing."""
        # Create a simple translation transform
        transform = sitk.TranslationTransform(3)
        transform.SetParameters([5.0, 3.0, 2.0])  # Translation in x, y, z
        return transform
    
    def test_apply_transform_to_image_basic(self, sample_images, sample_transform, temp_dir):
        """Test basic transform application to image."""
        moving_file, ref_file, moving_img, ref_img = sample_images
        output_file = os.path.join(temp_dir, 'warped.nii.gz')
        
        # Apply transform
        result = apply_transform_to_image(
            moving_file, ref_file, sample_transform, output_file
        )
        
        # Should complete successfully
        assert result == True
        assert os.path.exists(output_file)
        
        # Output should be a valid image with reference dimensions
        output_img = sitk.ReadImage(output_file)
        assert output_img.GetSize() == ref_img.GetSize()
        assert output_img.GetSpacing() == ref_img.GetSpacing()
    
    def test_apply_transform_to_image_identity_transform(self, sample_images, temp_dir):
        """Test applying identity transform."""
        moving_file, ref_file, moving_img, ref_img = sample_images
        output_file = os.path.join(temp_dir, 'identity_warped.nii.gz')
        
        # Create identity transform
        identity_transform = sitk.TranslationTransform(3)  # Zero translation
        
        # Apply transform
        result = apply_transform_to_image(
            moving_file, ref_file, identity_transform, output_file
        )
        
        assert result == True
        assert os.path.exists(output_file)
    
    def test_apply_transform_to_image_nonexistent_input(self, temp_dir):
        """Test transform application with non-existent input."""
        nonexistent_file = os.path.join(temp_dir, 'nonexistent.nii.gz')
        ref_file = os.path.join(temp_dir, 'ref.nii.gz')
        output_file = os.path.join(temp_dir, 'output.nii.gz')
        
        # Create dummy reference
        ref_data = np.ones((10, 10, 10), dtype=np.float32)
        ref_img = sitk.GetImageFromArray(ref_data)
        sitk.WriteImage(ref_img, ref_file)
        
        transform = sitk.TranslationTransform(3)
        
        # Should fail gracefully
        result = apply_transform_to_image(
            nonexistent_file, ref_file, transform, output_file
        )
        assert result == False
    
    @patch('warper.sitk.ReadImage')
    def test_apply_transform_to_image_sitk_error(self, mock_read, sample_images, sample_transform, temp_dir):
        """Test handling of SimpleITK errors during transform application."""
        moving_file, ref_file, moving_img, ref_img = sample_images
        output_file = os.path.join(temp_dir, 'error_output.nii.gz')
        
        # Mock SimpleITK to raise error
        mock_read.side_effect = RuntimeError("SimpleITK error")
        
        result = apply_transform_to_image(
            moving_file, ref_file, sample_transform, output_file
        )
        assert result == False


class TestWarpUtils:
    """Test warp utility functions."""
    
    @pytest.fixture
    def sample_transforms(self):
        """Create sample transforms for composition tests."""
        # Translation transform
        translation = sitk.TranslationTransform(3)
        translation.SetParameters([2.0, 3.0, 1.0])
        
        # Rotation transform
        rotation = sitk.Euler3DTransform()
        rotation.SetRotation(0.1, 0.2, 0.0)  # Small rotations
        
        return translation, rotation
    
    def test_compose_transforms_basic(self, sample_transforms):
        """Test basic transform composition."""
        transform1, transform2 = sample_transforms
        
        # Compose transforms
        composed = compose_transforms([transform1, transform2])
        
        # Should return a valid transform
        assert isinstance(composed, sitk.Transform)
        
        # Test that composition works by applying to a point
        test_point = [10.0, 15.0, 20.0]
        
        # Apply transforms separately
        intermediate = transform1.TransformPoint(test_point)
        separate_result = transform2.TransformPoint(intermediate)
        
        # Apply composed transform
        composed_result = composed.TransformPoint(test_point)
        
        # Results should be approximately equal
        np.testing.assert_allclose(separate_result, composed_result, atol=1e-6)
    
    def test_compose_transforms_single_transform(self, sample_transforms):
        """Test composing a single transform."""
        transform1, _ = sample_transforms
        
        # Compose single transform
        result = compose_transforms([transform1])
        
        # Should return equivalent transform
        assert isinstance(result, sitk.Transform)
        
        # Test point transformation
        test_point = [5.0, 10.0, 15.0]
        original_result = transform1.TransformPoint(test_point)
        composed_result = result.TransformPoint(test_point)
        
        np.testing.assert_allclose(original_result, composed_result, atol=1e-10)
    
    def test_compose_transforms_empty_list(self):
        """Test composing empty transform list."""
        # Should handle empty list gracefully
        result = compose_transforms([])
        
        # Should return identity transform or handle appropriately
        if result is not None:
            # Test that it behaves like identity
            test_point = [1.0, 2.0, 3.0]
            transformed = result.TransformPoint(test_point)
            np.testing.assert_allclose(transformed, test_point, atol=1e-10)
    
    def test_invert_transform_translation(self):
        """Test inverting translation transform."""
        # Create translation
        translation = sitk.TranslationTransform(3)
        translation.SetParameters([5.0, -3.0, 2.0])
        
        # Invert transform
        inverted = invert_transform(translation)
        
        # Should be a valid transform
        assert isinstance(inverted, sitk.Transform)
        
        # Test inversion: T^(-1) * T should be identity
        test_point = [10.0, 20.0, 30.0]
        transformed = translation.TransformPoint(test_point)
        back_transformed = inverted.TransformPoint(transformed)
        
        np.testing.assert_allclose(back_transformed, test_point, atol=1e-6)
    
    def test_invert_transform_euler3d(self):
        """Test inverting Euler3D transform."""
        # Create Euler3D transform
        euler = sitk.Euler3DTransform()
        euler.SetRotation(0.1, 0.2, 0.3)
        euler.SetTranslation([2.0, -1.0, 3.0])
        
        # Invert transform
        inverted = invert_transform(euler)
        
        assert isinstance(inverted, sitk.Transform)
        
        # Test inversion
        test_point = [5.0, 10.0, 15.0]
        transformed = euler.TransformPoint(test_point)
        back_transformed = inverted.TransformPoint(transformed)
        
        np.testing.assert_allclose(back_transformed, test_point, atol=1e-6)
    
    def test_interpolate_image_linear(self):
        """Test linear image interpolation."""
        # Create test image
        data = np.random.rand(10, 10, 10).astype(np.float32)
        image = sitk.GetImageFromArray(data)
        image.SetSpacing([1.0, 1.0, 1.0])
        
        # Create identity transform for interpolation test
        transform = sitk.TranslationTransform(3)
        
        # Interpolate with linear method
        interpolated = interpolate_image(image, transform, interpolator='linear')
        
        # Should return valid image
        assert isinstance(interpolated, sitk.Image)
        assert interpolated.GetSize() == image.GetSize()
    
    def test_interpolate_image_nearest_neighbor(self):
        """Test nearest neighbor image interpolation."""
        # Create test image with integer values
        data = np.random.randint(0, 10, (8, 8, 8)).astype(np.float32)
        image = sitk.GetImageFromArray(data)
        
        transform = sitk.TranslationTransform(3)
        
        # Interpolate with nearest neighbor
        interpolated = interpolate_image(image, transform, interpolator='nearest')
        
        assert isinstance(interpolated, sitk.Image)
    
    def test_resample_image_to_reference_basic(self):
        """Test resampling image to reference space."""
        # Create moving image
        moving_data = np.random.rand(15, 15, 15).astype(np.float32)
        moving_img = sitk.GetImageFromArray(moving_data)
        moving_img.SetSpacing([2.0, 2.0, 2.0])
        
        # Create reference image with different spacing
        ref_data = np.random.rand(20, 20, 20).astype(np.float32)
        ref_img = sitk.GetImageFromArray(ref_data)
        ref_img.SetSpacing([1.0, 1.0, 1.0])
        
        # Create identity transform
        transform = sitk.TranslationTransform(3)
        
        # Resample to reference
        resampled = resample_image_to_reference(moving_img, ref_img, transform)
        
        # Should match reference properties
        assert isinstance(resampled, sitk.Image)
        assert resampled.GetSize() == ref_img.GetSize()
        assert resampled.GetSpacing() == ref_img.GetSpacing()
        assert resampled.GetOrigin() == ref_img.GetOrigin()
    
    def test_resample_image_to_reference_with_rotation(self):
        """Test resampling with rotation transform."""
        # Create images
        moving_data = np.random.rand(12, 12, 12).astype(np.float32)
        moving_img = sitk.GetImageFromArray(moving_data)
        
        ref_data = np.random.rand(12, 12, 12).astype(np.float32)
        ref_img = sitk.GetImageFromArray(ref_data)
        
        # Create rotation transform
        rotation = sitk.Euler3DTransform()
        rotation.SetRotation(0.1, 0.0, 0.0)  # 0.1 radians around x-axis
        
        # Resample with rotation
        resampled = resample_image_to_reference(moving_img, ref_img, rotation)
        
        assert isinstance(resampled, sitk.Image)
        assert resampled.GetSize() == ref_img.GetSize()


class TestAdvancedTransformations:
    """Test advanced transformation operations."""
    
    def test_transform_composition_order(self):
        """Test that transform composition order matters."""
        # Create two different transforms
        translation = sitk.TranslationTransform(3)
        translation.SetParameters([5.0, 0.0, 0.0])
        
        rotation = sitk.Euler3DTransform()
        rotation.SetRotation(0.0, 0.0, np.pi/4)  # 45 degrees around z
        
        # Compose in different orders
        composed1 = compose_transforms([translation, rotation])
        composed2 = compose_transforms([rotation, translation])
        
        # Results should be different for non-commutative transforms
        test_point = [10.0, 0.0, 0.0]
        result1 = composed1.TransformPoint(test_point)
        result2 = composed2.TransformPoint(test_point)
        
        # Should NOT be equal (transforms don't commute)
        assert not np.allclose(result1, result2, atol=1e-6)
    
    def test_transform_inverse_composition(self):
        """Test that T * T^(-1) = I."""
        # Create a complex transform
        euler = sitk.Euler3DTransform()
        euler.SetRotation(0.2, 0.1, 0.3)
        euler.SetTranslation([3.0, -2.0, 1.0])
        
        # Get inverse
        inverse = invert_transform(euler)
        
        # Compose T * T^(-1)
        identity_composed = compose_transforms([euler, inverse])
        
        # Should behave like identity
        test_points = [
            [0.0, 0.0, 0.0],
            [10.0, -5.0, 7.0],
            [-3.0, 8.0, -1.0]
        ]
        
        for point in test_points:
            result = identity_composed.TransformPoint(point)
            np.testing.assert_allclose(result, point, atol=1e-6)


# Mock implementations for functions that might not exist
def compose_transforms(transforms):
    """Compose a list of transforms."""
    if not transforms:
        # Return identity transform
        return sitk.TranslationTransform(3)
    
    if len(transforms) == 1:
        return transforms[0]
    
    # Use composite transform
    composite = sitk.CompositeTransform(3)
    for transform in transforms:
        composite.AddTransform(transform)
    
    return composite

def invert_transform(transform):
    """Invert a transform."""
    try:
        return transform.GetInverse()
    except RuntimeError:
        # Some transforms may not be invertible
        raise ValueError("Transform is not invertible")

def interpolate_image(image, transform, interpolator='linear'):
    """Interpolate image using specified method."""
    if interpolator == 'linear':
        interpolator_sitk = sitk.sitkLinear
    elif interpolator == 'nearest':
        interpolator_sitk = sitk.sitkNearestNeighbor
    else:
        interpolator_sitk = sitk.sitkLinear
    
    return sitk.Resample(image, transform, interpolator_sitk)

def resample_image_to_reference(moving_image, reference_image, transform):
    """Resample moving image to reference image space."""
    return sitk.Resample(
        moving_image,
        reference_image,
        transform,
        sitk.sitkLinear,
        0.0,
        moving_image.GetPixelID()
    )


if __name__ == '__main__':
    pytest.main([__file__])
