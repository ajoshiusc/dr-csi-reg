#!/usr/bin/env python3
"""
Template Generation Module
Part of the Diffusion-Relaxation Suite

Generates registration templates using different strategies:
1. Average volume (default) - Creates mean of all spectral volumes
2. Central volume - Uses middle volume from sorted files
3. Specified volume - Uses user-specified volume index
"""

import os
import glob
import argparse
import numpy as np
import nibabel as nib
from pathlib import Path


def load_nifti_volume(filepath):
    """Load a NIfTI volume and return data and affine matrix."""
    try:
        img = nib.load(filepath)
        return img.get_fdata(), img.affine, img.header
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None, None, None


def save_nifti_volume(data, affine, header, output_path):
    """Save data as NIfTI volume."""
    try:
        img = nib.Nifti1Image(data, affine, header)
        nib.save(img, output_path)
        return True
    except Exception as e:
        print(f"Error saving {output_path}: {e}")
        return False


def generate_average_template(input_files, output_path):
    """
    Generate average template from multiple NIfTI files.
    
    Args:
        input_files: List of input NIfTI file paths
        output_path: Output path for average template
        
    Returns:
        bool: Success status
    """
    print(f"Generating average template from {len(input_files)} volumes...")
    
    if not input_files:
        print("ERROR: No input files provided")
        return False
    
    # Load first volume to get dimensions and affine
    first_data, first_affine, first_header = load_nifti_volume(input_files[0])
    if first_data is None:
        return False
    
    print(f"Template dimensions: {first_data.shape}")
    print(f"Data type: {first_data.dtype}")
    
    # Initialize accumulator
    volume_sum = np.zeros_like(first_data, dtype=np.float64)
    valid_count = 0
    
    # Accumulate all volumes
    for i, filepath in enumerate(input_files):
        print(f"Processing volume {i+1}/{len(input_files)}: {Path(filepath).name}")
        
        data, affine, header = load_nifti_volume(filepath)
        if data is None:
            print(f"  Skipping {filepath} (failed to load)")
            continue
            
        # Check dimensions match
        if data.shape != first_data.shape:
            print(f"  Skipping {filepath} (dimension mismatch: {data.shape} vs {first_data.shape})")
            continue
            
        # Add to accumulator
        volume_sum += data.astype(np.float64)
        valid_count += 1
    
    if valid_count == 0:
        print("ERROR: No valid volumes found")
        return False
    
    # Calculate average
    average_volume = volume_sum / valid_count
    print(f"Averaged {valid_count} volumes")
    print(f"Average intensity range: [{np.min(average_volume):.3f}, {np.max(average_volume):.3f}]")
    
    # Convert back to original data type
    if first_data.dtype != np.float64:
        average_volume = average_volume.astype(first_data.dtype)
    
    # Save average template
    success = save_nifti_volume(average_volume, first_affine, first_header, output_path)
    if success:
        print(f"✅ Average template saved: {output_path}")
    else:
        print(f"❌ Failed to save template: {output_path}")
    
    return success


def generate_central_template(input_files, output_path):
    """
    Generate template using central (middle) volume.
    
    Args:
        input_files: List of input NIfTI file paths
        output_path: Output path for central template
        
    Returns:
        bool: Success status
    """
    if not input_files:
        print("ERROR: No input files provided")
        return False
    
    # Sort files and select central one
    sorted_files = sorted(input_files)
    central_index = len(sorted_files) // 2
    central_file = sorted_files[central_index]
    
    print(f"Using central volume template: {Path(central_file).name}")
    print(f"  (Volume {central_index + 1} of {len(sorted_files)} sorted files)")
    
    # Copy central file to output
    try:
        img = nib.load(central_file)
        nib.save(img, output_path)
        print(f"✅ Central template saved: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to copy central template: {e}")
        return False


def generate_specified_template(input_files, volume_index, output_path):
    """
    Generate template using specified volume index.
    
    Args:
        input_files: List of input NIfTI file paths
        volume_index: Index of volume to use (0-based)
        output_path: Output path for specified template
        
    Returns:
        bool: Success status
    """
    if not input_files:
        print("ERROR: No input files provided")
        return False
    
    sorted_files = sorted(input_files)
    
    if volume_index < 0 or volume_index >= len(sorted_files):
        print(f"ERROR: Volume index {volume_index} out of range [0, {len(sorted_files)-1}]")
        return False
    
    specified_file = sorted_files[volume_index]
    
    print(f"Using specified volume template: {Path(specified_file).name}")
    print(f"  (Volume {volume_index + 1} of {len(sorted_files)} files)")
    
    # Copy specified file to output
    try:
        img = nib.load(specified_file)
        nib.save(img, output_path)
        print(f"✅ Specified template saved: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to copy specified template: {e}")
        return False


def find_input_files(input_dir, pattern="*.nii.gz"):
    """Find input NIfTI files in directory."""
    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory not found: {input_dir}")
        return []
    
    # Find all matching files
    search_pattern = os.path.join(input_dir, pattern)
    all_files = glob.glob(search_pattern)
    
    # Filter out registered files and template files
    input_files = [
        f for f in all_files 
        if not f.endswith('.reg.nii.gz') 
        and not 'template' in os.path.basename(f).lower()
    ]
    
    if not input_files:
        print(f"ERROR: No input files found matching pattern: {search_pattern}")
        return []
    
    print(f"Found {len(input_files)} input files")
    return input_files


def main():
    parser = argparse.ArgumentParser(
        description="Generate registration templates from spectral volumes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Template Generation Strategies:
  average     - Generate mean of all volumes (default, recommended)
  central     - Use middle volume from sorted files
  specified   - Use specific volume by index

Examples:
  # Generate average template (default)
  python generate_template.py input_dir output_template.nii.gz
  
  # Generate central volume template
  python generate_template.py input_dir output_template.nii.gz --strategy central
  
  # Use specific volume (e.g., volume 10)
  python generate_template.py input_dir output_template.nii.gz --strategy specified --volume-index 10
  
  # Custom file pattern
  python generate_template.py input_dir output_template.nii.gz --pattern "spectral_*.nii.gz"
        """
    )
    
    parser.add_argument('input_dir', help='Directory containing input NIfTI files')
    parser.add_argument('output_template', help='Output template file path')
    parser.add_argument('--strategy', choices=['average', 'central', 'specified'], 
                       default='average', help='Template generation strategy (default: average)')
    parser.add_argument('--volume-index', type=int, default=0,
                       help='Volume index for specified strategy (0-based, default: 0)')
    parser.add_argument('--pattern', default='*.nii.gz',
                       help='File pattern to match (default: *.nii.gz)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show verbose output')
    
    args = parser.parse_args()
    
    # Print header
    print("=" * 60)
    print("Template Generation Module")
    print("Part of the Diffusion-Relaxation Suite")
    print("=" * 60)
    print(f"Input directory: {args.input_dir}")
    print(f"Output template: {args.output_template}")
    print(f"Strategy: {args.strategy}")
    if args.strategy == 'specified':
        print(f"Volume index: {args.volume_index}")
    print(f"File pattern: {args.pattern}")
    print("=" * 60)
    
    # Find input files
    input_files = find_input_files(args.input_dir, args.pattern)
    if not input_files:
        return 1
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output_template), exist_ok=True)
    
    # Generate template based on strategy
    success = False
    
    if args.strategy == 'average':
        success = generate_average_template(input_files, args.output_template)
    elif args.strategy == 'central':
        success = generate_central_template(input_files, args.output_template)
    elif args.strategy == 'specified':
        success = generate_specified_template(input_files, args.volume_index, args.output_template)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Template generation completed successfully!")
        print(f"Template saved: {args.output_template}")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ Template generation failed!")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    exit(main())