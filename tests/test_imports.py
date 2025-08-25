import pytest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Try to import all modules to check for import errors
def test_import_spectral_mat_to_nifti():
    """Test importing spectral_mat_to_nifti module."""
    try:
        import spectral_mat_to_nifti
        assert hasattr(spectral_mat_to_nifti, 'convert_spectral_mat_to_nifti')
    except ImportError as e:
        pytest.fail(f"Failed to import spectral_mat_to_nifti: {e}")

def test_import_nifti_registration_pipeline():
    """Test importing nifti_registration_pipeline module."""
    try:
        import nifti_registration_pipeline
        assert hasattr(nifti_registration_pipeline, 'register_nifti_directory')
    except ImportError as e:
        pytest.fail(f"Failed to import nifti_registration_pipeline: {e}")

def test_import_spectral_nifti_to_mat():
    """Test importing spectral_nifti_to_mat module."""
    try:
        import spectral_nifti_to_mat
        assert hasattr(spectral_nifti_to_mat, 'convert_spectral_nifti_to_mat')
    except ImportError as e:
        pytest.fail(f"Failed to import spectral_nifti_to_mat: {e}")

def test_import_registration():
    """Test importing registration module."""
    try:
        import registration
        assert hasattr(registration, 'perform_nonlinear_registration')
    except ImportError as e:
        pytest.fail(f"Failed to import registration: {e}")

def test_import_utils():
    """Test importing utils module."""
    try:
        import utils
        # Utils module may have various utility functions
        # Just check that it imports successfully
        assert utils is not None
    except ImportError as e:
        pytest.fail(f"Failed to import utils: {e}")

def test_import_optional_modules():
    """Test importing optional modules that may not exist."""
    optional_modules = ['warper', 'warp_utils', 'aligner', 'networks']
    
    for module_name in optional_modules:
        try:
            module = __import__(module_name)
            print(f"Successfully imported optional module: {module_name}")
        except ImportError:
            print(f"Optional module {module_name} not available (this is OK)")

def test_python_version():
    """Test that we're running on a supported Python version."""
    assert sys.version_info >= (3, 8), f"Python 3.8+ required, got {sys.version_info}"

def test_required_packages():
    """Test that required packages are available."""
    required_packages = [
        'numpy',
        'scipy',
        'nibabel',
        'SimpleITK',
        'matplotlib'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        pytest.fail(f"Missing required packages: {missing_packages}")

def test_optional_packages():
    """Test availability of optional packages."""
    optional_packages = [
        'torch',
        'monai',
        'opencv-python'  # This would be 'cv2' when imported
    ]
    
    # Map package names to import names
    import_names = {
        'opencv-python': 'cv2'
    }
    
    for package in optional_packages:
        import_name = import_names.get(package, package)
        try:
            __import__(import_name)
            print(f"Optional package {package} is available")
        except ImportError:
            print(f"Optional package {package} is not available (this may be OK)")

if __name__ == '__main__':
    pytest.main([__file__])
