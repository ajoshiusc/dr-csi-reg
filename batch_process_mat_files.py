#!/usr/bin/env python3
"""
Simple batch processor for .mat files

Usage: python batch_process_mat_files.py input_folder output_folder
"""

import os
import sys
import glob
import subprocess

def main():
    if len(sys.argv) != 3:
        print("Usage: python batch_process_mat_files.py input_folder output_folder")
        return 1
    
    input_dir = sys.argv[1]
    output_base_dir = sys.argv[2]
    
    # Find all .mat files
    mat_files = glob.glob(os.path.join(input_dir, "*.mat"))
    
    if not mat_files:
        print(f"No .mat files found in {input_dir}")
        return 1
    
    print(f"Found {len(mat_files)} .mat files to process")
    
    # Create output directory
    os.makedirs(output_base_dir, exist_ok=True)
    
    # Process each file
    for i, mat_file in enumerate(mat_files, 1):
        filename = os.path.basename(mat_file)
        base_name = os.path.splitext(filename)[0]
        output_folder = os.path.join(output_base_dir, f"{base_name}_registered")
        
        print(f"[{i}/{len(mat_files)}] Processing {filename}...")
        
        # Run registration module
        cmd = [sys.executable, "run_registration_module.py", mat_file, output_folder]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"  ✅ Success")
        except subprocess.CalledProcessError:
            print(f"  ❌ Failed")
    
    print("Batch processing completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())