#!/usr/bin/env python3
"""
Wrapper script for spectral_mat_to_nifti.py
Allows running from project root: python convert_mat_to_nifti.py
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    script_path = os.path.join(os.path.dirname(__file__), 'src', 'spectral_mat_to_nifti.py')
    subprocess.run([sys.executable, script_path] + sys.argv[1:], check=False)
