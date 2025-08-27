import pytest
import numpy as np
import tempfile
import shutil
import os
import nibabel as nib
import SimpleITK as sitk
from unittest.mock import patch, MagicMock

# Add src directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from registration import (
    perform_nonlinear_registration,
    create_center_aligned_transform
)


class TestRegistrationCore:
    """Test core registration functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_sitk_images(self):
        """Create sample SimpleITK images for testing."""
        # Create fixed image
        fixed_array = np.random.rand(20, 20, 20).astype(np.float32)
        fixed_image = sitk.GetImageFromArray(fixed_array)
        fixed_image.SetSpacing([2.0, 2.0, 2.0])
        fixed_image.SetOrigin([0.0, 0.0, 0.0])
        
        # Create moving image (slightly shifted)
        moving_array = np.roll(fixed_array, shift=2, axis=0)  # Shift for registration challenge
        moving_image = sitk.GetImageFromArray(moving_array)
        moving_image.SetSpacing([2.0, 2.0, 2.0])
        moving_image.SetOrigin([4.0, 0.0, 0.0])  # Offset origin
        
        return fixed_image, moving_image
    
    @pytest.fixture
    def sample_nifti_files(self, temp_dir, sample_sitk_images):
        """Create sample NIfTI files from SimpleITK images."""
        fixed_image, moving_image = sample_sitk_images
        
        # Save as NIfTI files
        fixed_file = os.path.join(temp_dir, 'fixed.nii.gz')
        moving_file = os.path.join(temp_dir, 'moving.nii.gz')
        
        sitk.WriteImage(fixed_image, fixed_file)
        sitk.WriteImage(moving_image, moving_file)
        
        return moving_file, fixed_file
    
    def test_create_initial_transform(self, sample_sitk_images):
        """Test creation of initial transform."""
        fixed_image, moving_image = sample_sitk_images
        
        # Test identity transform creation
        transform = create_initial_transform(fixed_image, moving_image)
        
        # Should return a valid SimpleITK transform
        assert isinstance(transform, sitk.Transform)
        
        # For Euler3DTransform, should have 6 parameters (3 rotation + 3 translation)
        if isinstance(transform, sitk.Euler3DTransform):
            assert transform.GetNumberOfParameters() == 6
        
        # Transform should be invertible
        assert transform.IsLinear()
    
    def test_setup_registration_method(self, sample_sitk_images):
        """Test registration method setup."""
        fixed_image, moving_image = sample_sitk_images
        initial_transform = create_initial_transform(fixed_image, moving_image)
        
        registration_method = setup_registration_method(
            fixed_image, moving_image, initial_transform
        )
        
        # Should return a valid registration method
        assert isinstance(registration_method, sitk.ImageRegistrationMethod)
        
        # Check that metric was set
        metric_name = registration_method.GetMetricAsString()
        assert len(metric_name) > 0
        
        # Check that optimizer was set
        optimizer_name = registration_method.GetOptimizerAsString()
        assert len(optimizer_name) > 0
    
    def test_perform_nonlinear_registration_success(self, sample_nifti_files, temp_dir):
        """Test successful nonlinear registration."""
        moving_file, fixed_file = sample_nifti_files
        output_file = os.path.join(temp_dir, 'registered.nii.gz')
        
        # Perform registration
        result = perform_nonlinear_registration(moving_file, fixed_file, output_file)
        
        # Should complete successfully
        assert result == True
        
        # Output file should exist
        assert os.path.exists(output_file)
        
        # Output should be a valid NIfTI file
        output_img = sitk.ReadImage(output_file)
        assert output_img.GetSize() == sitk.ReadImage(fixed_file).GetSize()
    
    def test_perform_nonlinear_registration_file_not_found(self, temp_dir):
        """Test registration with non-existent input files."""
        moving_file = os.path.join(temp_dir, 'nonexistent_moving.nii.gz')
        fixed_file = os.path.join(temp_dir, 'nonexistent_fixed.nii.gz')
        output_file = os.path.join(temp_dir, 'output.nii.gz')
        
        # Should fail gracefully
        result = perform_nonlinear_registration(moving_file, fixed_file, output_file)
        assert result == False
        
        # Output file should not be created
        assert not os.path.exists(output_file)
    
    def test_perform_nonlinear_registration_invalid_output_path(self, sample_nifti_files):
        """Test registration with invalid output path."""
        moving_file, fixed_file = sample_nifti_files
        output_file = '/invalid/path/output.nii.gz'  # Invalid path
        
        # Should fail gracefully
        result = perform_nonlinear_registration(moving_file, fixed_file, output_file)
        assert result == False
    
    @patch('registration.sitk.ReadImage')
    def test_perform_nonlinear_registration_sitk_read_error(self, mock_read_image, sample_nifti_files, temp_dir):
        """Test registration with SimpleITK read error."""
        moving_file, fixed_file = sample_nifti_files
        output_file = os.path.join(temp_dir, 'output.nii.gz')
        
        # Mock SimpleITK to raise exception on read
        mock_read_image.side_effect = RuntimeError("Failed to read image")
        
        # Should fail gracefully
        result = perform_nonlinear_registration(moving_file, fixed_file, output_file)
        assert result == False
    
    @patch('registration.sitk.WriteImage')
    def test_perform_nonlinear_registration_sitk_write_error(self, mock_write_image, sample_nifti_files, temp_dir):
        """Test registration with SimpleITK write error."""
        moving_file, fixed_file = sample_nifti_files
        output_file = os.path.join(temp_dir, 'output.nii.gz')
        
        # Mock WriteImage to raise exception
        mock_write_image.side_effect = RuntimeError("Failed to write image")
        
        # Should fail gracefully
        result = perform_nonlinear_registration(moving_file, fixed_file, output_file)
        assert result == False
    
    def test_perform_nonlinear_registration_identical_images(self, temp_dir):
        """Test registration with identical fixed and moving images."""
        # Create identical images
        data = np.random.rand(15, 15, 15).astype(np.float32)
        image = sitk.GetImageFromArray(data)
        image.SetSpacing([1.0, 1.0, 1.0])
        
        # Save as both moving and fixed
        moving_file = os.path.join(temp_dir, 'identical_moving.nii.gz')
        fixed_file = os.path.join(temp_dir, 'identical_fixed.nii.gz')
        sitk.WriteImage(image, moving_file)
        sitk.WriteImage(image, fixed_file)
        
        output_file = os.path.join(temp_dir, 'registered_identical.nii.gz')
        
        # Should still work (though registration may be trivial)
        result = perform_nonlinear_registration(moving_file, fixed_file, output_file)
        assert result == True
        assert os.path.exists(output_file)


class TestTransformOperations:
    """Test transform-related operations."""
    
    def test_create_initial_transform_euler3d(self):
        """Test that initial transform is Euler3DTransform."""
        # Create simple test images
        fixed_array = np.ones((10, 10, 10), dtype=np.float32)
        moving_array = np.ones((10, 10, 10), dtype=np.float32)
        
        fixed_image = sitk.GetImageFromArray(fixed_array)
        moving_image = sitk.GetImageFromArray(moving_array)
        
        # Create initial transform
        transform = create_initial_transform(fixed_image, moving_image)
        
        # Should be Euler3DTransform (identity)
        assert isinstance(transform, sitk.Euler3DTransform)
        
        # Parameters should be zeros (identity)
        params = transform.GetParameters()
        np.testing.assert_allclose(params, np.zeros(6), atol=1e-10)
    
    def test_create_initial_transform_different_sizes(self):
        """Test initial transform with different image sizes."""
        # Create images of different sizes
        fixed_array = np.random.rand(20, 20, 20).astype(np.float32)
        moving_array = np.random.rand(15, 15, 15).astype(np.float32)
        
        fixed_image = sitk.GetImageFromArray(fixed_array)
        moving_image = sitk.GetImageFromArray(moving_array)
        
        # Should still create valid transform
        transform = create_initial_transform(fixed_image, moving_image)
        assert isinstance(transform, sitk.Transform)
        assert transform.IsLinear()


class TestRegistrationMethod:
    """Test registration method configuration."""
    
    @pytest.fixture
    def sample_images_and_transform(self):
        """Create sample images and initial transform."""
        fixed_array = np.random.rand(12, 12, 12).astype(np.float32)
        moving_array = np.random.rand(12, 12, 12).astype(np.float32)
        
        fixed_image = sitk.GetImageFromArray(fixed_array)
        moving_image = sitk.GetImageFromArray(moving_array)
        
        # Set proper spacing and origin
        for img in [fixed_image, moving_image]:
            img.SetSpacing([1.0, 1.0, 1.0])
            img.SetOrigin([0.0, 0.0, 0.0])
        
        initial_transform = create_initial_transform(fixed_image, moving_image)
        
        return fixed_image, moving_image, initial_transform
    
    def test_setup_registration_method_parameters(self, sample_images_and_transform):
        """Test registration method parameter configuration."""
        fixed_image, moving_image, initial_transform = sample_images_and_transform
        
        registration_method = setup_registration_method(
            fixed_image, moving_image, initial_transform
        )
        
        # Should have multi-resolution setup
        shrink_factors = registration_method.GetShrinkFactorsPerLevel()
        smoothing_sigmas = registration_method.GetSmoothingSigmasPerLevel()
        
        assert len(shrink_factors) > 0
        assert len(smoothing_sigmas) > 0
        assert len(shrink_factors) == len(smoothing_sigmas)
    
    def test_setup_registration_method_metric(self, sample_images_and_transform):
        """Test registration method metric setup."""
        fixed_image, moving_image, initial_transform = sample_images_and_transform
        
        registration_method = setup_registration_method(
            fixed_image, moving_image, initial_transform
        )
        
        # Should have a metric configured
        metric_name = registration_method.GetMetricAsString()
        assert 'Correlation' in metric_name or 'MutualInformation' in metric_name or 'MeanSquares' in metric_name
    
    def test_setup_registration_method_optimizer(self, sample_images_and_transform):
        """Test registration method optimizer setup."""
        fixed_image, moving_image, initial_transform = sample_images_and_transform
        
        registration_method = setup_registration_method(
            fixed_image, moving_image, initial_transform
        )
        
        # Should have an optimizer configured
        optimizer_name = registration_method.GetOptimizerAsString()
        assert len(optimizer_name) > 0
        
        # Should have reasonable stopping criteria
        max_iterations = registration_method.GetOptimizerMaximumStepSizePerLevel()
        assert len(max_iterations) > 0


if __name__ == '__main__':
    pytest.main([__file__])
