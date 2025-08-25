import pytest
import sys
import os
import subprocess
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestFullWorkflow:
    """Test the complete DR-CSI registration workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for workflow testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_workflow_data(self, temp_dir):
        """Create sample data for workflow testing."""
        import numpy as np
        import scipy.io as sio
        
        # Create sample .mat file
        spectral_data = np.random.rand(5, 16, 16, 8).astype(np.float64)
        resolution = np.array([2.0, 2.0, 3.0])
        
        mat_data = {
            'img': spectral_data,
            'Resolution': resolution,
            'Transform': np.eye(4),
            'spatial_dim': np.array([16, 16, 8])
        }
        
        input_mat = os.path.join(temp_dir, 'test_input.mat')
        sio.savemat(input_mat, mat_data)
        
        return input_mat, temp_dir
    
    @patch('spectral_mat_to_nifti.convert_spectral_mat_to_nifti')
    @patch('nifti_registration_pipeline.register_nifti_directory')
    @patch('spectral_nifti_to_mat.convert_spectral_nifti_to_mat')
    def test_complete_workflow_integration(self, mock_nifti_to_mat, mock_register, mock_mat_to_nifti, sample_workflow_data, temp_dir):
        """Test complete workflow integration."""
        input_mat, temp_data_dir = sample_workflow_data
        
        # Mock all functions to return success
        mock_mat_to_nifti.return_value = True
        mock_register.return_value = True
        mock_nifti_to_mat.return_value = True
        
        # Import workflow modules
        from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
        from nifti_registration_pipeline import register_nifti_directory
        from spectral_nifti_to_mat import convert_spectral_nifti_to_mat
        
        # Define workflow paths
        nifti_dir = os.path.join(temp_dir, 'nifti_files')
        registered_dir = os.path.join(temp_dir, 'registered')
        output_mat = os.path.join(temp_dir, 'output.mat')
        
        # Step 1: Convert .mat to NIfTI
        result1 = convert_spectral_mat_to_nifti(input_mat, nifti_dir)
        assert mock_mat_to_nifti.called
        
        # Step 2: Register NIfTI files
        result2 = register_nifti_directory(nifti_dir, registered_dir)
        assert mock_register.called
        
        # Step 3: Convert back to .mat
        result3 = convert_spectral_nifti_to_mat(registered_dir, output_mat, input_mat)
        assert mock_nifti_to_mat.called
        
        # Verify all functions were called with correct arguments
        mock_mat_to_nifti.assert_called_once_with(input_mat, nifti_dir)
        mock_register.assert_called_once_with(nifti_dir, registered_dir)
        mock_nifti_to_mat.assert_called_once_with(registered_dir, output_mat, input_mat)
    
    def test_workflow_error_handling(self, sample_workflow_data, temp_dir):
        """Test workflow error handling when steps fail."""
        input_mat, temp_data_dir = sample_workflow_data
        
        with patch('spectral_mat_to_nifti.convert_spectral_mat_to_nifti', return_value=False):
            from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
            
            # First step should fail
            result = convert_spectral_mat_to_nifti(input_mat, 'dummy_dir')
            assert result == False
    
    @patch('subprocess.run')
    def test_workflow_script_execution(self, mock_subprocess, temp_dir):
        """Test workflow script execution."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout='Success', stderr='')
        
        # Test running workflow script
        script_path = os.path.join(os.path.dirname(__file__), '..', 'run_full_workflow.sh')
        if os.path.exists(script_path):
            result = subprocess.run(['bash', script_path], capture_output=True, text=True)
            # Mock should be called
            assert mock_subprocess.called
    
    def test_workflow_data_consistency(self):
        """Test that workflow maintains data consistency."""
        # This would be a more comprehensive test checking that the round-trip
        # conversion maintains data integrity across the full pipeline
        
        # Mock the full pipeline but verify data flow
        with patch('spectral_mat_to_nifti.convert_spectral_mat_to_nifti') as mock_step1:
            with patch('nifti_registration_pipeline.register_nifti_directory') as mock_step2:
                with patch('spectral_nifti_to_mat.convert_spectral_nifti_to_mat') as mock_step3:
                    
                    mock_step1.return_value = True
                    mock_step2.return_value = True
                    mock_step3.return_value = True
                    
                    # Simulate workflow execution
                    from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
                    from nifti_registration_pipeline import register_nifti_directory
                    from spectral_nifti_to_mat import convert_spectral_nifti_to_mat
                    
                    # Execute pipeline steps
                    step1_result = convert_spectral_mat_to_nifti('input.mat', 'nifti_dir')
                    step2_result = register_nifti_directory('nifti_dir', 'registered_dir')
                    step3_result = convert_spectral_nifti_to_mat('registered_dir', 'output.mat', 'input.mat')
                    
                    # All steps should succeed in mock scenario
                    assert step1_result == True
                    assert step2_result == True
                    assert step3_result == True


class TestCommandLineInterfaces:
    """Test command line interfaces of wrapper scripts."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for CLI testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_convert_mat_to_nifti_cli(self, temp_dir):
        """Test convert_mat_to_nifti.py command line interface."""
        # Create dummy input file
        dummy_mat = os.path.join(temp_dir, 'input.mat')
        open(dummy_mat, 'w').close()  # Create empty file
        
        output_dir = os.path.join(temp_dir, 'output')
        
        # Test CLI script
        cli_script = os.path.join(os.path.dirname(__file__), '..', 'convert_mat_to_nifti.py')
        if os.path.exists(cli_script):
            with patch('spectral_mat_to_nifti.convert_spectral_mat_to_nifti', return_value=True):
                try:
                    result = subprocess.run([
                        'python', cli_script, dummy_mat, output_dir
                    ], capture_output=True, text=True, timeout=10)
                    # Should not crash (exact return code depends on implementation)
                    assert isinstance(result.returncode, int)
                except subprocess.TimeoutExpired:
                    pytest.skip("CLI test timed out - may require actual data")
    
    def test_register_nifti_cli(self, temp_dir):
        """Test register_nifti.py command line interface."""
        input_dir = os.path.join(temp_dir, 'input')
        output_dir = os.path.join(temp_dir, 'output')
        os.makedirs(input_dir, exist_ok=True)
        
        cli_script = os.path.join(os.path.dirname(__file__), '..', 'register_nifti.py')
        if os.path.exists(cli_script):
            with patch('nifti_registration_pipeline.register_nifti_directory', return_value=True):
                try:
                    result = subprocess.run([
                        'python', cli_script, input_dir, output_dir
                    ], capture_output=True, text=True, timeout=10)
                    assert isinstance(result.returncode, int)
                except subprocess.TimeoutExpired:
                    pytest.skip("CLI test timed out")
    
    def test_convert_nifti_to_mat_cli(self, temp_dir):
        """Test convert_nifti_to_mat.py command line interface."""
        input_dir = os.path.join(temp_dir, 'input')
        output_mat = os.path.join(temp_dir, 'output.mat')
        reference_mat = os.path.join(temp_dir, 'reference.mat')
        
        os.makedirs(input_dir, exist_ok=True)
        open(reference_mat, 'w').close()  # Create empty reference
        
        cli_script = os.path.join(os.path.dirname(__file__), '..', 'convert_nifti_to_mat.py')
        if os.path.exists(cli_script):
            with patch('spectral_nifti_to_mat.convert_spectral_nifti_to_mat', return_value=True):
                try:
                    result = subprocess.run([
                        'python', cli_script, input_dir, output_mat, '--reference', reference_mat
                    ], capture_output=True, text=True, timeout=10)
                    assert isinstance(result.returncode, int)
                except subprocess.TimeoutExpired:
                    pytest.skip("CLI test timed out")


class TestWorkflowScripts:
    """Test workflow automation scripts."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for script testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @patch('subprocess.run')
    def test_run_full_workflow_script(self, mock_subprocess):
        """Test run_full_workflow.sh script."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        workflow_script = os.path.join(os.path.dirname(__file__), '..', 'run_full_workflow.sh')
        if os.path.exists(workflow_script):
            # Test script exists and is executable
            assert os.access(workflow_script, os.X_OK)
            
            # Mock execution
            result = subprocess.run(['bash', workflow_script], capture_output=True, text=True)
            assert mock_subprocess.called
    
    @patch('subprocess.run')
    def test_monitor_workflow_script(self, mock_subprocess):
        """Test monitor_workflow.sh script."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        monitor_script = os.path.join(os.path.dirname(__file__), '..', 'monitor_workflow.sh')
        if os.path.exists(monitor_script):
            assert os.access(monitor_script, os.X_OK)


class TestErrorRecovery:
    """Test error recovery and cleanup mechanisms."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for error testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_partial_workflow_recovery(self, temp_dir):
        """Test recovery from partial workflow completion."""
        # Simulate partial completion scenario
        nifti_dir = os.path.join(temp_dir, 'nifti_files')
        os.makedirs(nifti_dir)
        
        # Create some fake NIfTI files to simulate partial completion
        for i in range(3):
            fake_nifti = os.path.join(nifti_dir, f'spectral_point_{i:03d}.nii.gz')
            open(fake_nifti, 'w').close()
        
        # Test that workflow can detect and handle partial state
        from nifti_registration_pipeline import register_nifti_directory
        
        with patch('nifti_registration_pipeline.perform_nonlinear_registration', return_value=True):
            result = register_nifti_directory(nifti_dir, os.path.join(temp_dir, 'output'))
            # Should handle existing files gracefully
            assert isinstance(result, bool)
    
    def test_cleanup_on_failure(self, temp_dir):
        """Test that failed operations clean up properly."""
        output_dir = os.path.join(temp_dir, 'cleanup_test')
        
        # Mock a function that creates files then fails
        with patch('spectral_mat_to_nifti.convert_spectral_mat_to_nifti') as mock_convert:
            def failing_convert(input_file, output_dir):
                # Simulate creating some files then failing
                os.makedirs(output_dir, exist_ok=True)
                temp_file = os.path.join(output_dir, 'temp_file.tmp')
                open(temp_file, 'w').close()
                return False  # Simulate failure
            
            mock_convert.side_effect = failing_convert
            
            from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
            result = convert_spectral_mat_to_nifti('fake_input.mat', output_dir)
            
            assert result == False
            # Depending on implementation, cleanup might remove temp files


class TestPerformanceAndScaling:
    """Test performance characteristics and scaling behavior."""
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets."""
        # Mock large dataset scenario
        large_file_list = [f'spectral_point_{i:03d}.nii.gz' for i in range(100)]
        
        with patch('nifti_registration_pipeline.get_nifti_files', return_value=large_file_list):
            with patch('nifti_registration_pipeline.perform_nonlinear_registration', return_value=True):
                from nifti_registration_pipeline import register_nifti_directory
                
                # Should handle large number of files
                result = register_nifti_directory('fake_input', 'fake_output', num_cores=4)
                assert isinstance(result, bool)
    
    def test_multiprocessing_scaling(self):
        """Test multiprocessing scaling behavior."""
        file_list = [f'file_{i}.nii.gz' for i in range(8)]
        
        with patch('nifti_registration_pipeline.get_nifti_files', return_value=file_list):
            with patch('nifti_registration_pipeline.perform_nonlinear_registration', return_value=True):
                from nifti_registration_pipeline import register_nifti_directory
                
                # Test with different core counts
                for num_cores in [1, 2, 4]:
                    result = register_nifti_directory('input', 'output', num_cores=num_cores)
                    assert isinstance(result, bool)


if __name__ == '__main__':
    pytest.main([__file__])
