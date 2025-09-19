"""
DR-CSI Registration Package

Core modules for spectral MRI data conversion and registration.
"""

__version__ = "1.0.0"
__author__ = "USC Laboratory"

# Core module components
from . import spectral_mat_to_nifti
from . import spectral_nifti_to_mat  
from . import nifti_registration_pipeline

# Supporting modules
from . import utils
from . import registration
from . import warper
from . import warp_utils

__all__ = [
    'spectral_mat_to_nifti',
    'spectral_nifti_to_mat',
    'nifti_registration_pipeline',
    'utils',
    'registration', 
    'warper',
    'warp_utils'
]
