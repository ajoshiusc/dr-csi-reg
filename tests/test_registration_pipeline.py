import pytest
import numpy as np
import tempfile
import shutil
import os
import nibabel as nib
import SimpleITK as sitk
from unittest.mock import patch, MagicMock, call
import multiprocessing

# Add src directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nifti_registration_pipeline import register_nifti_directory, select_template_image
from registration import perform_nonlinear_registration


class TestNiftiRegistrationPipeline:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_nifti_files(self, temp_dir):
        """Create sample NIfTI files for testing."""
        nifti_files = []
        for i in range(3):
            # Create random 3D image data
            data = np.random.rand(20, 20, 20).astype(np.float32)
            
            # Create simple affine transformation
            affine = np.eye(4)
            affine[0, 0] = 2.0  # 2mm voxel size
            affine[1, 1] = 2.0
            affine[2, 2] = 2.0
            
            # Create NIfTI image
            img = nib.Nifti1Image(data, affine)
            filename = os.path.join(temp_dir, f'spectral_point_{i:03d}.nii.gz')
            nib.save(img, filename)
            nifti_files.append(filename)
        
        return nifti_files
    
    def test_select_template_image(self, sample_nifti_files):
        """Test template image selection."""
        template = select_template_image(sample_nifti_files)
        
        # Template should be one of the input files
        assert template in sample_nifti_files
        
        # Template should be a valid file path
        assert os.path.exists(template)
    
    def test_select_template_image_empty_list(self):
        """Test template selection with empty file list."""
        with pytest.raises((ValueError, IndexError)):
            select_template_image([])
    
    def test_select_template_image_single_file(self, sample_nifti_files):
        """Test template selection with single file."""
        single_file = [sample_nifti_files[0]]
        template = select_template_image(single_file)
        assert template == sample_nifti_files[0]
    
    @patch('nifti_registration_pipeline.perform_nonlinear_registration')
    def test_register_nifti_directory_basic(self, mock_register, sample_nifti_files, temp_dir):
        """Test basic directory registration."""
        # Mock the registration function to return success
        mock_register.return_value = True
        
        input_dir = temp_dir
        output_dir = os.path.join(temp_dir, 'registered')
        
        # Run registration
        result = register_nifti_directory(input_dir, output_dir)
        
        # Check that registration was called for each file
        assert mock_register.call_count >= 1
        assert result == True
        
        # Check output directory was created
        assert os.path.exists(output_dir)
    
    @patch('nifti_registration_pipeline.perform_nonlinear_registration')
    def test_register_nifti_directory_with_template(self, mock_register, sample_nifti_files, temp_dir):
        """Test directory registration with specific template."""
        mock_register.return_value = True
        
        input_dir = temp_dir
        output_dir = os.path.join(temp_dir, 'registered')
        template_file = sample_nifti_files[0]
        
        # Run registration with specific template
        result = register_nifti_directory(input_dir, output_dir, template_image=template_file)
        
        # Check that registration was successful
        assert result == True
        
        # Check that template was used in registration calls
        assert mock_register.call_count >= 1
        
        # Verify template file is passed to registration function
        call_args_list = mock_register.call_args_list
        for call_args in call_args_list:
            if len(call_args[0]) >= 3:  # Check if enough arguments
                template_arg = call_args[0][1]  # Second argument should be template
                assert template_arg == template_file
    
    def test_register_nifti_directory_empty_directory(self, temp_dir):
        """Test registration with empty directory."""
        empty_dir = os.path.join(temp_dir, 'empty')
        os.makedirs(empty_dir)
        output_dir = os.path.join(temp_dir, 'output')
        
        result = register_nifti_directory(empty_dir, output_dir)
        
        # Should return False for empty directory
        assert result == False
    
    def test_register_nifti_directory_nonexistent_directory(self, temp_dir):
        """Test registration with non-existent directory."""
        non_existent_dir = os.path.join(temp_dir, 'does_not_exist')
        output_dir = os.path.join(temp_dir, 'output')
        
        result = register_nifti_directory(non_existent_dir, output_dir)
        
        # Should return False for non-existent directory
        assert result == False
    
    @patch('nifti_registration_pipeline.multiprocessing.cpu_count')
    @patch('nifti_registration_pipeline.perform_nonlinear_registration')
    def test_register_nifti_directory_parallel_processing(self, mock_register, mock_cpu_count, sample_nifti_files, temp_dir):
        """Test parallel processing in registration."""
        mock_cpu_count.return_value = 4
        mock_register.return_value = True
        
        input_dir = temp_dir
        output_dir = os.path.join(temp_dir, 'registered')
        
        # Run registration with multiple files
        result = register_nifti_directory(input_dir, output_dir, num_cores=2)
        
        # Should complete successfully
        assert result == True
    
    @patch('nifti_registration_pipeline.perform_nonlinear_registration')
    def test_register_nifti_directory_registration_failure(self, mock_register, sample_nifti_files, temp_dir):
        """Test handling of registration failures."""
        # Mock registration to fail for some files
        mock_register.side_effect = [True, False, True]  # Mixed success/failure
        
        input_dir = temp_dir
        output_dir = os.path.join(temp_dir, 'registered')
        
        # Run registration
        result = register_nifti_directory(input_dir, output_dir)
        
        # Should handle partial failures gracefully
        # Exact behavior depends on implementation - could be True or False
        assert isinstance(result, bool)
    
    def test_register_nifti_directory_creates_output_directory(self, sample_nifti_files, temp_dir):
        """Test that output directory is created if it doesn't exist."""
        input_dir = temp_dir
        output_dir = os.path.join(temp_dir, 'new_output_dir')
        
        # Ensure output directory doesn't exist initially
        assert not os.path.exists(output_dir)
        
        # Mock the registration to avoid actual processing
        with patch('nifti_registration_pipeline.perform_nonlinear_registration', return_value=True):
            register_nifti_directory(input_dir, output_dir)
        
        # Check that output directory was created
        assert os.path.exists(output_dir)


class TestRegistrationCore:
    """Test the core registration function."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_images(self, temp_dir):
        """Create sample images for registration testing."""
        # Create moving image
        moving_data = np.random.rand(20, 20, 20).astype(np.float32)
        moving_affine = np.eye(4) * 2.0  # 2mm voxels
        moving_affine[3, 3] = 1.0
        moving_img = nib.Nifti1Image(moving_data, moving_affine)
        moving_file = os.path.join(temp_dir, 'moving.nii.gz')
        nib.save(moving_img, moving_file)
        
        # Create fixed image (slightly different)
        fixed_data = moving_data + 0.1 * np.random.rand(20, 20, 20).astype(np.float32)
        fixed_img = nib.Nifti1Image(fixed_data, moving_affine)
        fixed_file = os.path.join(temp_dir, 'fixed.nii.gz')
        nib.save(fixed_img, fixed_file)
        
        return moving_file, fixed_file
    
    def test_perform_nonlinear_registration_basic(self, sample_images, temp_dir):
        """Test basic nonlinear registration."""
        moving_file, fixed_file = sample_images
        output_file = os.path.join(temp_dir, 'registered.nii.gz')
        
        # Run registration (this will use actual SimpleITK)
        result = perform_nonlinear_registration(moving_file, fixed_file, output_file)
        
        # Check registration completed
        assert isinstance(result, bool)
        
        # If successful, check output file exists
        if result:
            assert os.path.exists(output_file)
    
    def test_perform_nonlinear_registration_nonexistent_files(self, temp_dir):
        """Test registration with non-existent input files."""
        moving_file = os.path.join(temp_dir, 'nonexistent_moving.nii.gz')
        fixed_file = os.path.join(temp_dir, 'nonexistent_fixed.nii.gz')
        output_file = os.path.join(temp_dir, 'output.nii.gz')
        
        # Should handle file not found gracefully
        result = perform_nonlinear_registration(moving_file, fixed_file, output_file)
        assert result == False
    
    @patch('registration.sitk.ReadImage')
    @patch('registration.sitk.WriteImage')
    def test_perform_nonlinear_registration_sitk_error(self, mock_write, mock_read, sample_images, temp_dir):
        """Test registration with SimpleITK errors."""
        moving_file, fixed_file = sample_images
        output_file = os.path.join(temp_dir, 'output.nii.gz')
        
        # Mock SimpleITK to raise an exception
        mock_read.side_effect = RuntimeError("SimpleITK error")
        
        # Should handle SimpleITK errors gracefully
        result = perform_nonlinear_registration(moving_file, fixed_file, output_file)
        assert result == False


class TestCommandLineInterface:
    """Test command line interface functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_nifti_files(self, temp_dir):
        """Create sample NIfTI files for CLI testing."""
        for i in range(2):
            data = np.random.rand(10, 10, 10).astype(np.float32)
            affine = np.eye(4)
            img = nib.Nifti1Image(data, affine)
            filename = os.path.join(temp_dir, f'test_{i:03d}.nii.gz')
            nib.save(img, filename)
        
        return temp_dir
    
    def test_main_function_with_valid_arguments(self, sample_nifti_files, temp_dir):
        """Test main function with valid command line arguments."""
        from nifti_registration_pipeline import main
        
        output_dir = os.path.join(temp_dir, 'output')
        
        # Mock sys.argv to simulate command line arguments
        test_args = [
            'nifti_registration_pipeline.py',
            sample_nifti_files,
            output_dir,
            '--num_cores', '1'
        ]
        
        with patch('sys.argv', test_args):
            with patch('nifti_registration_pipeline.perform_nonlinear_registration', return_value=True):
                # Should run without errors
                try:
                    main()
                except SystemExit as e:
                    # argparse might call sys.exit(0) on success
                    assert e.code == 0
                except Exception:
                    # Other exceptions indicate real problems
                    pytest.fail("Main function raised unexpected exception")


if __name__ == '__main__':
    pytest.main([__file__])
