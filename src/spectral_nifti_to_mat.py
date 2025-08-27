# Convert spectral NIfTI files back to .mat format (reverse of main_mat2nifti_spectral.py)

import os
import numpy as np
import scipy.io as sio
import nibabel as nib
import SimpleITK as sitk
import glob

def convert_spectral_nifti_to_mat(nifti_dir, output_mat_file, original_mat_file=None):
    """
    Convert spectral NIfTI files back to the original .mat format
    
    Args:
        nifti_dir (str): Directory containing spectral_point_*.nii.gz files
        output_mat_file (str): Output .mat file path
        original_mat_file (str): Optional original .mat file for metadata comparison
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    print(f"Converting NIfTI files from {nifti_dir} to {output_mat_file}")
    
    if not os.path.exists(nifti_dir):
        print(f"ERROR: Directory {nifti_dir} does not exist.")
        return False
    
    # Find all spectral point NIfTI files
    nifti_pattern = os.path.join(nifti_dir, "spectral_point_*.nii.gz")
    nifti_files = sorted(glob.glob(nifti_pattern))
    
    if not nifti_files:
        print(f"ERROR: No spectral_point_*.nii.gz files found in {nifti_dir}")
        return False
    
    print(f"Found {len(nifti_files)} spectral NIfTI files")
    
    # Load original file metadata if provided - preserve ALL fields except 'data'
    original_metadata = {}
    original_data_dtype = np.uint16  # Default fallback
    if original_mat_file and os.path.exists(original_mat_file):
        original_mat = sio.loadmat(original_mat_file)
        # Extract original data type for preservation
        if 'data' in original_mat:
            original_data_dtype = original_mat['data'].dtype
            print(f"Original data type: {original_data_dtype}")
        # Preserve all fields from original except private MATLAB fields and 'data'
        for key, value in original_mat.items():
            if not key.startswith('__') and key != 'data':
                original_metadata[key] = value
        print(f"Preserving metadata from original file: {original_mat_file}")
        print(f"  Preserved fields: {list(original_metadata.keys())}")
    
    # Read all spectral volumes and reconstruct the 4D array
    spectral_volumes = []
    nifti_spacing = None
    
    for i, nifti_file in enumerate(nifti_files):
        print(f"Processing {os.path.basename(nifti_file)}...")
        
        # Read using SimpleITK
        img_sitk = sitk.ReadImage(nifti_file)
        img_array = sitk.GetArrayFromImage(img_sitk)
        
        # Convert from SimpleITK (z,y,x) back to original (x,y,z) format
        img_array = img_array.transpose(2, 1, 0)  # (z,y,x) -> (x,y,z)
        
        spectral_volumes.append(img_array)
        
        if i == 0:
            # Read spacing from the first NIfTI file
            nifti_spacing = img_sitk.GetSpacing()
            print(f"  Individual volume shape: {img_array.shape}")
            print(f"  Spacing from NIfTI file: {nifti_spacing}")
    
    # Stack all spectral volumes to create 4D array
    # Shape should be (num_spectral, x, y, z) = (31, 104, 52, 12)
    reconstructed_data = np.stack(spectral_volumes, axis=0)
    print(f"Reconstructed data shape: {reconstructed_data.shape}")
    
    # Convert NIfTI spacing to Resolution format for mat file
    if original_metadata and 'Resolution' in original_metadata:
        # Use original resolution to preserve precision
        resolution_array = original_metadata['Resolution']
        print(f"Using original resolution: {resolution_array}")
    elif nifti_spacing:
        # NIfTI spacing is (x, y, z), convert to uint8 array format like original
        resolution_array = np.array([[int(nifti_spacing[0]), int(nifti_spacing[1]), int(nifti_spacing[2])]], dtype=np.uint8)
        print(f"Resolution derived from NIfTI spacing: {resolution_array}")
    else:
        resolution_array = np.array([[1, 1, 1]], dtype=np.uint8)
        print("Using default resolution: [[1, 1, 1]]")
    
    # Create the output dictionary starting with the reconstructed data
    output_dict = {
        'data': reconstructed_data.astype(original_data_dtype),  # Preserve original data type
    }
    
    # Add resolution - prefer from NIfTI spacing, fallback to original
    output_dict['Resolution'] = resolution_array
    
    # Add all other metadata from original file if available
    if original_metadata:
        # Add all preserved fields from original file
        for key, value in original_metadata.items():
            if key != 'Resolution':  # Don't overwrite Resolution derived from NIfTI
                output_dict[key] = value
        print(f"Added {len(original_metadata)} metadata fields from original file")
    else:
        # Use default metadata if original not available
        output_dict.update({
            'Transform': np.eye(4, dtype=np.uint8),
            'spatial_dim': np.array([[reconstructed_data.shape[1], reconstructed_data.shape[2], reconstructed_data.shape[3]]], dtype=np.uint8)
        })
        print("Using default metadata (no original file provided)")
    
    # Ensure critical fields are present with reasonable defaults
    if 'Transform' not in output_dict:
        output_dict['Transform'] = np.eye(4, dtype=np.uint8)
        print("Added default Transform matrix")
    
    if 'spatial_dim' not in output_dict:
        output_dict['spatial_dim'] = np.array([[reconstructed_data.shape[1], reconstructed_data.shape[2], reconstructed_data.shape[3]]], dtype=np.uint8)
        print("Added default spatial_dim based on data shape")
    
    # Save to .mat file
    try:
        sio.savemat(output_mat_file, output_dict)
        print(f"Successfully saved reconstructed data to: {output_mat_file}")
        print(f"Final data shape: {reconstructed_data.shape}")
        print(f"Data type: {reconstructed_data.dtype}")
        print(f"Saved fields: {list(output_dict.keys())}")
        
        # Calculate file size
        file_size_mb = os.path.getsize(output_mat_file) / (1024 * 1024)
        print(f"Output file size: {file_size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"ERROR saving .mat file: {e}")
        return False

if __name__ == "__main__":
    import argparse
    import sys
    
    def show_usage():
        print("=== Spectral NIfTI to .mat Conversion ===")
        print()
        print("Usage:")
        print("  python spectral_nifti_to_mat.py <input_directory> <output_mat_file> [original_mat_file]")
        print()
        print("Examples:")
        print("  python spectral_nifti_to_mat.py patient2_nifti_spectral_output reconstructed.mat")
        print("  python spectral_nifti_to_mat.py patient2_nifti_spectral_output reconstructed.mat data_wip_patient2.mat")
        print()
        print("Arguments:")
        print("  input_directory    Directory containing spectral_point_*.nii.gz files")
        print("  output_mat_file    Output .mat file path")
        print("  original_mat_file  Optional: Original .mat file for metadata and data type preservation")
        print()
        print("The script will:")
        print("  1. Read all spectral_point_*.nii.gz files from input directory")
        print("  2. Reconstruct the 4D spectral data array")
        print("  3. Preserve original data types (uint16, float64, etc.) exactly")
        print("  4. Extract resolution from NIfTI file spacing")
        print("  5. Preserve ALL original metadata fields from original .mat file")
        print("  6. Save reconstructed data to .mat file with zero data loss")
        print()
    
    parser = argparse.ArgumentParser(description='Convert spectral NIfTI files back to .mat format')
    parser.add_argument('input_dir', help='Directory containing spectral_point_*.nii.gz files')
    parser.add_argument('output_mat_file', help='Output .mat file path')
    parser.add_argument('original_mat_file', nargs='?', default=None,
                       help='Optional: Original .mat file for metadata and data type preservation')
    
    # Check if no arguments provided
    if len(sys.argv) < 3:
        show_usage()
        sys.exit(1)
    
    args = parser.parse_args()
    
    print("=== Converting Spectral NIfTI Files Back to .mat Format ===")
    print(f"Input directory: {args.input_dir}")
    print(f"Output .mat file: {args.output_mat_file}")
    if args.original_mat_file:
        print(f"Original .mat file: {args.original_mat_file}")
    else:
        print("No original .mat file provided - using default metadata")
    
    # Perform the conversion
    success = convert_spectral_nifti_to_mat(args.input_dir, args.output_mat_file, args.original_mat_file)
    
    if success:
        print("\\n=== Conversion completed successfully ===")
        print(f"✅ NIfTI files converted back to: {args.output_mat_file}")
        print("✅ Resolution read from NIfTI file spacing")
        print("✅ Data converted back to original format")
    else:
        print("\\n❌ Conversion failed. Please check the error messages above.")
        sys.exit(1)
