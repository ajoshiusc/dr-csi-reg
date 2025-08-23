#!/usr/bin/env python3
"""
Wrapper script for nifti_registration_pipeline.py
Allows running from project root: python register_nifti.py
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    script_path = os.path.join(os.path.dirname(__file__), 'src', 'nifti_registration_pipeline.py')
    subprocess.run([sys.executable, script_path] + sys.argv[1:], check=False)
