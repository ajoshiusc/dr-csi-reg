#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append('src')
from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
from nifti_registration_pipeline import register_nifti  
from spectral_nifti_to_mat import convert_spectral_nifti_to_mat

Path("patient2_output/nifti").mkdir(parents=True, exist_ok=True)
Path("patient2_output/registration").mkdir(parents=True, exist_ok=True)
convert_spectral_mat_to_nifti("data/data_wip_patient2.mat", "patient2_output/nifti")
register_nifti("patient2_output/nifti", "patient2_output/registration", processes=1)  # OPTIMIZED: Single process eliminates 99% CPU lock contention
convert_spectral_nifti_to_mat("patient2_output/registration", "patient2_output/data_wip_patient2_registered.mat", "data/data_wip_patient2.mat")