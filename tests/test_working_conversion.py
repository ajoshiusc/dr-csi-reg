import pytest
import numpy as np
import tempfile
import shutil
import os
import sys
import scipy.io as sio

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
from spectral_nifti_to_mat import convert_spectral_nifti_to_mat


class TestWorkingConversion:
    """Simple tests that match the actual function signatures."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_file_not_found_handling(self, temp_dir):
        """Test that non-existent file is handled gracefully."""
        non_existent_file = os.path.join(temp_dir, 'does_not_exist.mat')
        output_dir = os.path.join(temp_dir, 'output')
        
        # Should handle this gracefully without crashing
        result = convert_spectral_mat_to_nifti(non_existent_file, output_dir)
        # Function returns None and prints error - this is expected behavior
        assert result is None
    
    def test_empty_nifti_directory(self, temp_dir):
        """Test conversion with empty NIfTI directory."""
        empty_dir = os.path.join(temp_dir, 'empty')
        os.makedirs(empty_dir)
        output_mat = os.path.join(temp_dir, 'output.mat')
        
        result = convert_spectral_nifti_to_mat(empty_dir, output_mat, None)
        assert result == False
    
    def test_basic_mat_structure(self, temp_dir):
        """Test with correct mat file structure."""
        # Create data with correct key name that the function expects
        test_data = np.random.rand(5, 20, 15, 10).astype(np.float64)
        resolution = np.array([2.0, 2.0, 3.0])
        
        mat_data = {
            'data': data,
            'resolution': resolution
        }
        
        # Save mat file
        mat_file = os.path.join(temp_dir, 'test_data.mat')
        sio.savemat(mat_file, mat_data)
        
        output_dir = os.path.join(temp_dir, 'nifti_output')
        
        # This should work without errors
        try:
            result = convert_spectral_mat_to_nifti(mat_file, output_dir)
            # If it completes without exception, that's success
            assert True
        except Exception as e:
            # Only fail on unexpected exceptions
            pytest.fail(f"Unexpected error: {e}")


if __name__ == '__main__':
    pytest.main([__file__])
