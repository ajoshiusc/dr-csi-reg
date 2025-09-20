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

# Constants
REQUIRED_SCRIPTS = ['convert_mat_to_nifti.py', 'register_nifti.py', 'convert_nifti_to_mat.py']
SEPARATOR_WIDTH = 50


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"ERROR: Command not found: {cmd[0]}")
        sys.exit(1)


def validate_inputs(input_mat):
    """Validate input file and required scripts exist."""
    if not Path(input_mat).is_file():
        print(f"ERROR: Input file not found: {input_mat}")
        sys.exit(1)

    for script in REQUIRED_SCRIPTS:
        if not Path(script).is_file():
            print(f"ERROR: Required script not found: {script}")
            sys.exit(1)


def setup_output_directory(output_dir, subdirs):
    """Create output directory and clean existing subdirectories."""
    Path(output_dir).mkdir(exist_ok=True)
    
    for subdir in subdirs:
        path = Path(subdir)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


def print_header(input_mat, output_dir, processes):
    """Print startup information."""
    print("=" * SEPARATOR_WIDTH)
    print("DR-CSI Registration Module")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Input: {Path(input_mat).name}")
    print(f"Output: {output_dir}")
    print(f"Processes: {processes}")
    print("=" * SEPARATOR_WIDTH)


def print_success(final_mat):
    """Print success message."""
    print("\n" + "=" * SEPARATOR_WIDTH)
    print("✅ Registration Complete!")
    print(f"Output: {final_mat}")
    print(f"Finished: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * SEPARATOR_WIDTH)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="DR-CSI Registration Module")
    parser.add_argument('input_mat_file', help='Path to input .mat file')
    parser.add_argument('output_directory', help='Directory for all outputs')
    parser.add_argument('--processes', '-p', type=int, default=4, 
                       choices=range(1, 17), help='Parallel processes (default: 4)')
    args = parser.parse_args()

    # Setup paths
    input_mat = Path(args.input_mat_file).resolve()
    output_dir = Path(args.output_directory).resolve()
    nifti_dir = output_dir / 'nifti'
    registration_dir = output_dir / 'registration'
    
    # Create output .mat filename based on input filename
    input_stem = input_mat.stem  # filename without extension
    final_mat = output_dir / f"{input_stem}_registered.mat"

    # Validate inputs and setup directories
    validate_inputs(input_mat)
    setup_output_directory(output_dir, [nifti_dir, registration_dir, final_mat])
    print_header(input_mat, output_dir, args.processes)

    try:
        # Define workflow steps
        steps = [
            ([sys.executable, 'convert_mat_to_nifti.py', str(input_mat), str(nifti_dir)], 
             "Converting .mat to NIfTI"),
            ([sys.executable, 'register_nifti.py', str(nifti_dir), str(registration_dir), 
              '--processes', str(args.processes)], 
             "Registering NIfTI files (⚠️ GPU required, 3-4 hours)"),
            ([sys.executable, 'convert_nifti_to_mat.py', str(registration_dir), 
              str(final_mat), str(input_mat)], 
             "Converting back to .mat")
        ]

        # Execute workflow steps
        for i, (cmd, description) in enumerate(steps, 1):
            print(f"\nStep {i}: {description}")
            run_command(cmd, description)

        print_success(final_mat)

    except KeyboardInterrupt:
        print("\nWorkflow interrupted")
        sys.exit(130)


if __name__ == '__main__':
    main()