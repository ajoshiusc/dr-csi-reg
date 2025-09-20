#!/usr/bin/env python3
"""
DR-CSI Registration Module Runner
Part of the Diffusion-Relaxation Suite
"""

import argparse
import sys
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\nRunning: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"ERROR: Command not found: {cmd[0]}")
        sys.exit(1)


#!/usr/bin/env python3
"""
DR-CSI Registration Module Runner
Part of the Diffusion-Relaxation Suite
"""

import argparse
import sys
import os
import subprocess
import shutil
from datetime import datetime


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\nRunning: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"ERROR: Command not found: {cmd[0]}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="DR-CSI Registration Module - Complete workflow runner"
    )
    
    parser.add_argument('input_mat_file', help='Path to input .mat file')
    parser.add_argument('output_directory', help='Directory for all outputs')
    parser.add_argument('--processes', '-p', type=int, default=4, 
                       choices=range(1, 17), help='Number of parallel processes (default: 4)')

    args = parser.parse_args()

    # Set up paths
    input_mat = os.path.abspath(args.input_mat_file)
    output_dir = os.path.abspath(args.output_directory)
    nifti_dir = os.path.join(output_dir, 'nifti')
    registration_dir = os.path.join(output_dir, 'registration')
    final_mat = os.path.join(output_dir, 'final_reconstructed.mat')

    # Print startup info
    print("=" * 50)
    print("DR-CSI Registration Module - Full Workflow")
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print(f"Input: {input_mat}")
    print(f"Output: {output_dir}")
    print(f"Processes: {args.processes}")

    # Check input file exists
    if not os.path.isfile(input_mat):
        print(f"ERROR: Input file not found: {input_mat}")
        sys.exit(1)

    # Check required scripts exist
    required_scripts = ['convert_mat_to_nifti.py', 'register_nifti.py', 'convert_nifti_to_mat.py']
    for script in required_scripts:
        if not os.path.isfile(script):
            print(f"ERROR: Required script not found: {script}")
            sys.exit(1)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(nifti_dir):
        shutil.rmtree(nifti_dir)
    if os.path.exists(registration_dir):
        shutil.rmtree(registration_dir)
    if os.path.exists(final_mat):
        os.remove(final_mat)

    try:
        # Step 1: Convert .mat to NIfTI
        print(f"\nStep 1: Converting .mat to NIfTI files...")
        cmd = [sys.executable, 'convert_mat_to_nifti.py', input_mat, nifti_dir]
        run_command(cmd, ".mat to NIfTI conversion")

        # Step 2: Register NIfTI files
        print(f"\nStep 2: Running registration with {args.processes} processes...")
        print("⚠️  WARNING: Requires NVIDIA GPU and takes 3-4 hours!")
        cmd = [sys.executable, 'register_nifti.py', nifti_dir, registration_dir, 
               '--processes', str(args.processes)]
        run_command(cmd, "NIfTI registration")

        # Step 3: Convert back to .mat
        print(f"\nStep 3: Converting back to .mat...")
        cmd = [sys.executable, 'convert_nifti_to_mat.py', registration_dir, final_mat, input_mat]
        run_command(cmd, "NIfTI to .mat conversion")

        # Success
        print("\n" + "=" * 50)
        print("DR-CSI Registration Module - COMPLETE! 🎉")
        print("=" * 50)
        print(f"Final output: {final_mat}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except KeyboardInterrupt:
        print("\nWorkflow interrupted by user")
        sys.exit(130)


if __name__ == '__main__':
    main()


if __name__ == '__main__':
    main()