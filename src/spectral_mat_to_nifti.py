# Read spectral .mat file and save as .nii.gz files with correct spectral dimension handling

import os
import numpy as np
import scipy.io as sio
import nibabel as nib
from nilearn import plotting
import SimpleITK as sitk

def convert_spectral_mat_to_nifti(mat_file, output_dir, res=None):
    """
    Convert spectral .mat files to individual NIfTI files with robust format handling
    
    Args:
        mat_file (str): Path to input .mat file
        output_dir (str): Output directory for NIfTI files
        res (list): Optional resolution override [x, y, z]
    
    Returns:
        int: Number of spectral points processed
    """
    if not os.path.exists(mat_file):
        print(f"Error: Input file does not exist: {mat_file}")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Robust .mat file loading
    print("Processing spectral format file...")
    mat = None
    
    # Try multiple loading methods for different .mat formats
    try:
        # Method 1: Standard scipy.io.loadmat
        mat = sio.loadmat(mat_file)
        print("✅ Loaded with standard method")
    except Exception as e1:
        print(f"Standard loading failed: {e1}")
        try:
            # Method 2: matlab_compatible mode
            mat = sio.loadmat(mat_file, matlab_compatible=True)
            print("✅ Loaded with matlab_compatible=True")
        except Exception as e2:
            print(f"MATLAB compatible loading failed: {e2}")
            try:
                # Method 3: squeeze_me=False for different structures
                mat = sio.loadmat(mat_file, squeeze_me=False, struct_as_record=False)
                print("✅ Loaded with squeeze_me=False")
            except Exception as e3:
                print(f"Alternative loading failed: {e3}")
                try:
                    # Method 4: Try HDF5 format (MATLAB v7.3)
                    import h5py
                    print("Trying HDF5 format (MATLAB v7.3)...")
                    mat = {}
                    with h5py.File(mat_file, 'r') as f:
                        for key in f.keys():
                            if not key.startswith('#'):
                                try:
                                    mat[key] = np.array(f[key])
                                except Exception:
                                    try:
                                        mat[key] = f[key][()]
                                    except Exception:
                                        print(f"Warning: Could not load key '{key}'")
                    print("✅ Loaded with HDF5 format")
                except ImportError:
                    print("❌ h5py not available for HDF5 format")
                    raise Exception("All loading methods failed - file format not supported")
                except Exception as e4:
                    print(f"HDF5 loading failed: {e4}")
                    raise Exception("All loading methods failed - file format not supported")
    
    if mat is None:
        raise Exception("Could not load .mat file with any method")
    
    # Extract data with flexible key handling
    img_data = None
    data_keys = [k for k in mat.keys() if not k.startswith('__')]
    print(f"Available keys in .mat file: {data_keys}")
    
    # Try to find the spectral data
    if 'data' in mat:
        img_data = mat['data']
    elif 'Data' in mat:
        img_data = mat['Data']
    elif 'img' in mat:
        img_data = mat['img']
    elif len(data_keys) == 1:
        # If only one data key, assume it's the spectral data
        img_data = mat[data_keys[0]]
        print(f"Using single data key: {data_keys[0]}")
    else:
        # Look for the largest array (likely the spectral data)
        largest_key = None
        largest_size = 0
        for key in data_keys:
            if hasattr(mat[key], 'size') and mat[key].size > largest_size:
                largest_size = mat[key].size
                largest_key = key
        if largest_key:
            img_data = mat[largest_key]
            print(f"Using largest array key: {largest_key}")
    
    if img_data is None:
        raise Exception(f"Could not find spectral data in .mat file. Available keys: {data_keys}")
    
    # Ensure data is numpy array
    img_data = np.array(img_data)
    
    # Handle different data arrangements
    if len(img_data.shape) == 3:
        # Add spectral dimension if missing
        img_data = img_data[np.newaxis, ...]
        print("⚠️  Added spectral dimension to 3D data")
    elif len(img_data.shape) != 4:
        print(f"⚠️  Unexpected data shape: {img_data.shape}")
        if img_data.size == 0:
            raise Exception("Data array is empty")
    
    # Shape should be (spectral, x, y, z)
    print(f"Final data shape: {img_data.shape}")
    
    # Read resolution from mat file, with fallback to parameter or default
    if res is not None:
        resolution = res
        print(f"Using provided resolution override: {resolution}")
    elif 'resolution' in mat:
        resolution = mat['resolution'][0]
        print(f"Using resolution from mat file: {resolution}")
    else:
        resolution = [1, 1, 1]
        print(f"Using default resolution: {resolution}")
    
    # Convert to appropriate spacing format
    if len(resolution) >= 3:
        spacing = [float(resolution[0]), float(resolution[1]), float(resolution[2])]
    else:
        spacing = [2.3, 2.3, 5.0]  # fallback default
        print(f"Warning: Invalid resolution format, using default spacing: {spacing}")
    
    print(f"Original data shape: {img_data.shape}")
    print(f"Spectral points: {img_data.shape[0]}")
    print(f"Spatial dimensions: {img_data.shape[1:]}")
    print(f"Resolution from file: {resolution}")
    print(f"Spacing used: {spacing}")
    
    # The data needs to be reorganized:
    # Original: (spectral, x, y, z) = (31, 104, 52, 12)
    # For NIfTI: we want (x, y, z) for each spectral point
    
    # Create one NIfTI file for each spectral point
    num_spectral_points = img_data.shape[0]  # 31 spectral points
    
    for spectral_idx in range(num_spectral_points):
        # Extract the spatial volume for this spectral point
        # Shape will be (104, 52, 12)
        spatial_volume = img_data[spectral_idx, :, :, :]
        
        # Convert to SimpleITK format
        # SimpleITK expects (z, y, x) ordering, so we need to transpose
        # Current: (x=104, y=52, z=12) -> Need: (z=12, y=52, x=104)
        spatial_volume_sitk = spatial_volume.transpose(2, 1, 0)  # (z, y, x)
        
        img_sitk = sitk.GetImageFromArray(spatial_volume_sitk)
        
        # Set spacing using the resolution from the mat file
        img_sitk.SetSpacing(spacing)
        
        # Generate filename for this spectral point
        filename = f"{output_dir}/spectral_point_{spectral_idx:03d}.nii.gz"
        sitk.WriteImage(img_sitk, filename)
        print(f"Saved spectral point {spectral_idx}: {filename}")
    
    # Also create PNG visualizations for the first few spectral points
    print("\nCreating PNG visualizations for first 5 spectral points...")
    for spectral_idx in range(min(5, num_spectral_points)):
        nii_file = f"{output_dir}/spectral_point_{spectral_idx:03d}.nii.gz"
        png_file = f"{output_dir}/spectral_point_{spectral_idx:03d}.png"
        
        try:
            nii_img = nib.load(nii_file)
            cut_coords = [coord / 2 for coord in nii_img.shape[:3]]
            cut_coords = np.array(cut_coords) * np.array(nii_img.affine.diagonal()[:3])
            plotting.plot_anat(nii_file, display_mode='ortho', 
                             cut_coords=cut_coords, output_file=png_file,
                             title=f"Spectral Point {spectral_idx}")
            print(f"Saved visualization: {png_file}")
        except Exception as e:
            print(f"Warning: Could not create visualization for spectral point {spectral_idx}: {e}")
    
    # Save metadata
    metadata_file = f"{output_dir}/spectral_metadata.txt"
    with open(metadata_file, 'w') as f:
        f.write("Data from spectral format .mat file\n")
        f.write(f"Original data shape: {img_data.shape}\n")
        f.write(f"Spectral dimension: {img_data.shape[0]} (first dimension)\n")
        f.write(f"Spatial dimensions: {img_data.shape[1:]} (x, y, z)\n")
        f.write(f"Resolution: {resolution}\n")
        f.write(f"Number of NIfTI files created: {num_spectral_points}\n")
        f.write(f"Spacing used: {spacing}\n")
    
    print(f"Saved metadata: {metadata_file}")
    
    return num_spectral_points

if __name__ == "__main__":
    import argparse
    
    def show_usage():
        """Show usage information when script is run without arguments"""
        print("=== Spectral .mat to NIfTI Conversion ===")
        print()
        print("Usage:")
        print("  python spectral_mat_to_nifti.py <input_mat_file> <output_directory>")
        print()
        print("Examples:")
        print("  python spectral_mat_to_nifti.py data_wip_patient2.mat patient2_nifti_spectral_output")
        print("  python spectral_mat_to_nifti.py /path/to/spectral_data.mat /path/to/output/")
        print()
        print("Arguments:")
        print("  input_mat_file     Path to input .mat file containing spectral data")
        print("  output_directory   Directory to save the converted NIfTI files")
        print()
        print("The script will:")
        print("  1. Read spectral data from .mat file")
        print("  2. Extract resolution from .mat file metadata")
        print("  3. Create individual NIfTI files for each spectral point")
        print("  4. Generate PNG visualizations for first 5 spectral points")
        print("  5. Save processing metadata")
        print()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert spectral .mat files to individual NIfTI files')
    parser.add_argument('mat_file', help='Input .mat file containing spectral data')
    parser.add_argument('output_dir', help='Output directory for NIfTI files')
    parser.add_argument('--res', nargs=3, type=float, metavar=('X', 'Y', 'Z'),
                       help='Override resolution [x y z] in mm (default: read from .mat file)')
    
    # Check if no arguments provided
    import sys
    if len(sys.argv) < 3:
        show_usage()
        sys.exit(1)
    
    args = parser.parse_args()
    
    print("=== Processing Spectral Data ===")
    print(f"Input file: {args.mat_file}")
    print(f"Output directory: {args.output_dir}")
    if args.res:
        print(f"Resolution override: {args.res}")
        res = args.res
    else:
        print("Resolution will be read from mat file")
        res = None
    
    # Process the data
    num_spectral = convert_spectral_mat_to_nifti(args.mat_file, args.output_dir, res)
    
    print("\n=== Processing Complete ===")
    if num_spectral and num_spectral > 0:
        print(f"✅ Created {num_spectral} spectral NIfTI files")
        print("✅ Files saved with naming: spectral_point_000.nii.gz, spectral_point_001.nii.gz, etc.")
        print("✅ PNG visualizations created for first 5 spectral points")
        print("✅ Metadata saved to spectral_metadata.txt")
        print("\nTo convert back to .mat format, run:")
        print(f"python spectral_nifti_to_mat.py {args.output_dir} reconstructed.mat {args.mat_file}")
    else:
        print("❌ Processing failed. Check error messages above.")
        sys.exit(1)
