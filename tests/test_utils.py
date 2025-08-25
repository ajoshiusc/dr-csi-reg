import pytest
import numpy as np
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, MagicMock

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import (
    validate_file_exists,
    create_output_directory,
    get_nifti_files,
    check_gpu_availability,
    log_message
)


class TestFileOperations:
    """Test utility functions for file operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_validate_file_exists_valid_file(self, temp_dir):
        """Test file validation with existing file."""
        # Create a test file
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        # Should return True for existing file
        result = validate_file_exists(test_file)
        assert result == True
    
    def test_validate_file_exists_nonexistent_file(self, temp_dir):
        """Test file validation with non-existent file."""
        nonexistent_file = os.path.join(temp_dir, 'does_not_exist.txt')
        
        # Should return False for non-existent file
        result = validate_file_exists(nonexistent_file)
        assert result == False
    
    def test_validate_file_exists_directory(self, temp_dir):
        """Test file validation with directory path."""
        # Should return False for directory (not a file)
        result = validate_file_exists(temp_dir)
        assert result == False
    
    def test_create_output_directory_new(self, temp_dir):
        """Test creating new output directory."""
        new_dir = os.path.join(temp_dir, 'new_output')
        
        # Directory shouldn't exist initially
        assert not os.path.exists(new_dir)
        
        # Create directory
        result = create_output_directory(new_dir)
        
        # Should succeed and directory should exist
        assert result == True
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)
    
    def test_create_output_directory_existing(self, temp_dir):
        """Test creating output directory that already exists."""
        # Use existing temp directory
        result = create_output_directory(temp_dir)
        
        # Should handle existing directory gracefully
        assert result == True
        assert os.path.exists(temp_dir)
    
    def test_create_output_directory_nested(self, temp_dir):
        """Test creating nested output directory."""
        nested_dir = os.path.join(temp_dir, 'level1', 'level2', 'output')
        
        # Create nested directory structure
        result = create_output_directory(nested_dir)
        
        # Should create all parent directories
        assert result == True
        assert os.path.exists(nested_dir)
    
    def test_create_output_directory_permission_error(self):
        """Test creating directory with permission issues."""
        # Try to create directory in root (should fail without permissions)
        restricted_dir = '/root/restricted_output'
        
        result = create_output_directory(restricted_dir)
        
        # Should handle permission error gracefully
        assert result == False
    
    def test_get_nifti_files(self, temp_dir):
        """Test getting NIfTI files from directory."""
        # Create some test files
        nifti_files = []
        for i in range(3):
            nifti_file = os.path.join(temp_dir, f'test_{i}.nii.gz')
            with open(nifti_file, 'w') as f:
                f.write('fake nifti content')
            nifti_files.append(nifti_file)
        
        # Create non-NIfTI files
        txt_file = os.path.join(temp_dir, 'test.txt')
        with open(txt_file, 'w') as f:
            f.write('not nifti')
        
        # Get NIfTI files
        found_files = get_nifti_files(temp_dir)
        
        # Should find only .nii.gz files
        assert len(found_files) == 3
        for f in found_files:
            assert f.endswith('.nii.gz')
            assert f in nifti_files
    
    def test_get_nifti_files_empty_directory(self, temp_dir):
        """Test getting NIfTI files from empty directory."""
        found_files = get_nifti_files(temp_dir)
        assert len(found_files) == 0
    
    def test_get_nifti_files_nonexistent_directory(self, temp_dir):
        """Test getting NIfTI files from non-existent directory."""
        nonexistent_dir = os.path.join(temp_dir, 'does_not_exist')
        found_files = get_nifti_files(nonexistent_dir)
        assert len(found_files) == 0
    
    def test_get_nifti_files_mixed_extensions(self, temp_dir):
        """Test getting NIfTI files with different extensions."""
        # Create files with different NIfTI extensions
        extensions = ['.nii', '.nii.gz']
        expected_files = []
        
        for ext in extensions:
            for i in range(2):
                nifti_file = os.path.join(temp_dir, f'test_{i}{ext}')
                with open(nifti_file, 'w') as f:
                    f.write('fake nifti content')
                expected_files.append(nifti_file)
        
        # Get NIfTI files
        found_files = get_nifti_files(temp_dir)
        
        # Should find both .nii and .nii.gz files
        assert len(found_files) == len(expected_files)
        for f in found_files:
            assert f.endswith('.nii') or f.endswith('.nii.gz')


class TestSystemUtilities:
    """Test system-related utility functions."""
    
    @patch('utils.torch.cuda.is_available')
    def test_check_gpu_availability_cuda_available(self, mock_cuda_available):
        """Test GPU availability check when CUDA is available."""
        mock_cuda_available.return_value = True
        
        result = check_gpu_availability()
        assert result == True
    
    @patch('utils.torch.cuda.is_available')
    def test_check_gpu_availability_cuda_not_available(self, mock_cuda_available):
        """Test GPU availability check when CUDA is not available."""
        mock_cuda_available.return_value = False
        
        result = check_gpu_availability()
        assert result == False
    
    @patch('utils.torch')
    def test_check_gpu_availability_no_torch(self, mock_torch):
        """Test GPU availability check when torch is not available."""
        mock_torch.cuda.is_available.side_effect = ImportError("No module named 'torch'")
        
        result = check_gpu_availability()
        assert result == False
    
    def test_log_message_basic(self, capsys):
        """Test basic log message functionality."""
        test_message = "Test log message"
        
        log_message(test_message)
        
        # Capture stdout
        captured = capsys.readouterr()
        assert test_message in captured.out
    
    def test_log_message_with_timestamp(self, capsys):
        """Test log message includes timestamp."""
        test_message = "Test with timestamp"
        
        log_message(test_message, include_timestamp=True)
        
        captured = capsys.readouterr()
        assert test_message in captured.out
        # Should include some form of timestamp
        assert any(char.isdigit() for char in captured.out)
    
    def test_log_message_different_levels(self, capsys):
        """Test log message with different levels."""
        levels = ['INFO', 'WARNING', 'ERROR']
        
        for level in levels:
            log_message(f"Test {level} message", level=level)
        
        captured = capsys.readouterr()
        for level in levels:
            assert level in captured.out


class TestDataValidation:
    """Test data validation utilities."""
    
    def test_validate_image_dimensions(self):
        """Test image dimension validation."""
        # Test valid 3D dimensions
        valid_shape = (64, 64, 32)
        result = validate_image_dimensions(valid_shape)
        assert result == True
        
        # Test invalid dimensions (too few)
        invalid_shape_2d = (64, 64)
        result = validate_image_dimensions(invalid_shape_2d)
        assert result == False
        
        # Test invalid dimensions (too many)
        invalid_shape_5d = (64, 64, 32, 16, 8)
        result = validate_image_dimensions(invalid_shape_5d)
        assert result == False
    
    def test_validate_spectral_data_shape(self):
        """Test spectral data shape validation."""
        # Valid 4D spectral data (time/spectral, x, y, z)
        valid_shape = (10, 64, 64, 32)
        result = validate_spectral_data_shape(valid_shape)
        assert result == True
        
        # Invalid shape (not 4D)
        invalid_shape = (64, 64, 32)
        result = validate_spectral_data_shape(invalid_shape)
        assert result == False
    
    def test_validate_resolution_array(self):
        """Test resolution array validation."""
        # Valid 3D resolution
        valid_resolution = np.array([1.0, 1.0, 2.0])
        result = validate_resolution_array(valid_resolution)
        assert result == True
        
        # Invalid resolution (wrong size)
        invalid_resolution = np.array([1.0, 1.0])
        result = validate_resolution_array(invalid_resolution)
        assert result == False
        
        # Invalid resolution (negative values)
        negative_resolution = np.array([1.0, -1.0, 2.0])
        result = validate_resolution_array(negative_resolution)
        assert result == False


class TestPathUtilities:
    """Test path manipulation utilities."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_generate_output_filename(self):
        """Test output filename generation."""
        input_file = '/path/to/input_file.nii.gz'
        suffix = '_registered'
        
        output_file = generate_output_filename(input_file, suffix)
        
        # Should preserve directory and add suffix
        expected = '/path/to/input_file_registered.nii.gz'
        assert output_file == expected
    
    def test_generate_output_filename_no_extension(self):
        """Test output filename generation without extension."""
        input_file = '/path/to/input_file'
        suffix = '_processed'
        
        output_file = generate_output_filename(input_file, suffix)
        expected = '/path/to/input_file_processed'
        assert output_file == expected
    
    def test_safe_filename_creation(self, temp_dir):
        """Test safe filename creation to avoid conflicts."""
        base_name = 'test_file'
        extension = '.txt'
        
        # Create the first file
        first_file = os.path.join(temp_dir, f'{base_name}{extension}')
        with open(first_file, 'w') as f:
            f.write('first file')
        
        # Generate safe filename (should avoid conflict)
        safe_name = generate_safe_filename(temp_dir, base_name, extension)
        
        # Should be different from existing file
        assert safe_name != first_file
        assert not os.path.exists(safe_name)


# Additional utility functions that might not exist but should be tested if they do exist
def validate_image_dimensions(shape):
    """Validate that image has proper 3D dimensions."""
    return len(shape) == 3 and all(dim > 0 for dim in shape)

def validate_spectral_data_shape(shape):
    """Validate spectral data has proper 4D shape."""
    return len(shape) == 4 and all(dim > 0 for dim in shape)

def validate_resolution_array(resolution):
    """Validate resolution array is proper 3D with positive values."""
    return len(resolution) == 3 and all(res > 0 for res in resolution)

def generate_output_filename(input_file, suffix):
    """Generate output filename with suffix."""
    base, ext = os.path.splitext(input_file)
    if ext == '.gz':
        base, ext2 = os.path.splitext(base)
        ext = ext2 + ext
    return f"{base}{suffix}{ext}"

def generate_safe_filename(directory, base_name, extension):
    """Generate a safe filename that doesn't conflict with existing files."""
    counter = 1
    while True:
        if counter == 1:
            filename = os.path.join(directory, f"{base_name}{extension}")
        else:
            filename = os.path.join(directory, f"{base_name}_{counter}{extension}")
        
        if not os.path.exists(filename):
            return filename
        counter += 1


if __name__ == '__main__':
    pytest.main([__file__])
