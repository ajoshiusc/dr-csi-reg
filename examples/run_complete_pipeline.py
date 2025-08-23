#!/usr/bin/env python3
"""
Example: Complete spectral MRI processing workflow

This script demonstrates the full pipeline:
1. Convert .mat to NIfTI files
2. Register NIfTI files  
3. Convert back to .mat format

Run this after placing your data file in the data/ directory.
"""

import os
import sys
import subprocess

def run_complete_pipeline():
    """Run the complete spectral MRI processing pipeline
    
    ⚠️ WARNING: Registration requires NVIDIA GPU and takes 3-4 hours!
    """
    
    # Configuration
    data_dir = "data"
    mat_file = os.path.join(data_dir, "data_wip_patient2.mat")
    nifti_output = os.path.join(data_dir, "converted_nifti")
    registration_output = os.path.join(data_dir, "registered_nifti") 
    final_mat = os.path.join(data_dir, "final_reconstructed.mat")
    
    print("=== DR-CSI Spectral MRI Processing Pipeline ===")
    print("⚠️  WARNING: Registration step requires NVIDIA GPU and takes 3-4 hours!")
    print("⚠️  Make sure you have sufficient time and GPU resources before proceeding.")
    print()
    
    # Check if input file exists
    if not os.path.exists(mat_file):
        print(f"❌ Input file not found: {mat_file}")
        print("Please place your .mat file in the data/ directory")
        return
    
    try:
        # Step 1: Convert .mat to NIfTI
        print("Step 1: Converting .mat to NIfTI files...")
        subprocess.run([
            sys.executable, "convert_mat_to_nifti.py",
            mat_file, nifti_output
        ], check=True)
        print("✅ Conversion completed")
        print()
        
        # Step 2: Register NIfTI files
        print("Step 2: Registering NIfTI files...")
        subprocess.run([
            sys.executable, "register_nifti.py", 
            nifti_output, registration_output,
            "--processes", "4"
        ], check=True)
        print("✅ Registration completed")
        print()
        
        # Step 3: Convert back to .mat
        print("Step 3: Converting registered NIfTI back to .mat...")
        subprocess.run([
            sys.executable, "convert_nifti_to_mat.py",
            registration_output, final_mat, mat_file
        ], check=True)
        print("✅ Final conversion completed")
        print()
        
        print("🎉 Complete pipeline finished successfully!")
        print(f"📄 Final output: {final_mat}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Pipeline failed at step: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_complete_pipeline()
