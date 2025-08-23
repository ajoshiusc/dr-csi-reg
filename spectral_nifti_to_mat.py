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
    
    # Load original file metadata if provided (for Transform and spatial_dim only)
    original_metadata = {}
    if original_mat_file and os.path.exists(original_mat_file):
        original_mat = sio.loadmat(original_mat_file)
        original_metadata = {
            'Transform': original_mat.get('Transform', np.eye(4, dtype=np.uint8)),
            'spatial_dim': original_mat.get('spatial_dim', None)
        }
        print(f"Using Transform and spatial_dim from original file: {original_mat_file}")
    
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
    if nifti_spacing:
        # NIfTI spacing is (x, y, z), convert to uint8 array format like original
        resolution_array = np.array([[int(nifti_spacing[0]), int(nifti_spacing[1]), int(nifti_spacing[2])]], dtype=np.uint8)
        print(f"Resolution derived from NIfTI spacing: {resolution_array}")
    else:
        resolution_array = np.array([[1, 1, 1]], dtype=np.uint8)
        print("Using default resolution: [[1, 1, 1]]")
    
    # Create the output dictionary with the same structure as original
    output_dict = {
        'data': reconstructed_data.astype(np.uint16),  # Match original dtype
        'Resolution': resolution_array  # Use resolution from NIfTI files
    }
    
    # Add other metadata if available
    if original_metadata:
        output_dict.update(original_metadata)
    else:
        # Use default metadata if original not available
        output_dict.update({
            'Transform': np.eye(4, dtype=np.uint8),
            'spatial_dim': np.array([[reconstructed_data.shape[1], reconstructed_data.shape[2], reconstructed_data.shape[3]]], dtype=np.uint8)
        })
    
    # Save to .mat file
    try:
        sio.savemat(output_mat_file, output_dict)
        print(f"Successfully saved reconstructed data to: {output_mat_file}")
        print(f"Final data shape: {reconstructed_data.shape}")
        print(f"Data type: {reconstructed_data.dtype}")
        
        # Calculate file size
        file_size_mb = os.path.getsize(output_mat_file) / (1024 * 1024)
        print(f"Output file size: {file_size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"ERROR saving .mat file: {e}")
        return False

if __name__ == "__main__":
    # Configuration
    nifti_input_dir = "/home/ajoshi/Projects/dr-csi-reg/patient2_nifti_spectral_output"
    output_mat_file = "/home/ajoshi/Projects/dr-csi-reg/reconstructed_from_nifti.mat"
    original_mat_file = "/home/ajoshi/Projects/dr-csi-reg/data_wip_patient2.mat"
    
    print("=== Converting Spectral NIfTI Files Back to .mat Format ===")
    print(f"Input directory: {nifti_input_dir}")
    print(f"Output .mat file: {output_mat_file}")
    print(f"Original .mat file: {original_mat_file}")
    
    # Perform the conversion
    success = convert_spectral_nifti_to_mat(nifti_input_dir, output_mat_file, original_mat_file)
    
    if success:
        print("\\n=== Conversion completed successfully ===")
        print(f"✅ NIfTI files converted back to: {output_mat_file}")
        print("✅ Resolution read from NIfTI file spacing")
        print("✅ Data converted back to original format")
        print("\\nTo verify round-trip conversion, run:")
        print("python verify_roundtrip_conversion.py")
    else:
        print("\\n❌ Conversion failed. Please check the error messages above.")
