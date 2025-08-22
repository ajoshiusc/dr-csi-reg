# Convert spectral NIfTI files back to .mat format (reverse of main_mat2nifti_patient2_spectral.py)

import os
import numpy as np
import scipy.io as sio
import nibabel as nib
import SimpleITK as sitk
import glob

def nifti_to_spectral_mat(nifti_dir, output_mat_file, original_mat_file=None):
    """
    Convert spectral NIfTI files back to the original .mat format
    
    Args:
        nifti_dir: Directory containing spectral_point_*.nii.gz files
        output_mat_file: Output .mat file path
        original_mat_file: Optional original .mat file for metadata comparison
    
    Returns:
        True if conversion successful, False otherwise
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
    
    # Load original file metadata if provided
    original_metadata = {}
    if original_mat_file and os.path.exists(original_mat_file):
        original_mat = sio.loadmat(original_mat_file)
        original_metadata = {
            'Resolution': original_mat.get('Resolution', np.array([[1, 1, 1]])),
            'Transform': original_mat.get('Transform', np.eye(4, dtype=np.uint8)),
            'spatial_dim': original_mat.get('spatial_dim', None)
        }
        print(f"Using metadata from original file: {original_mat_file}")
    
    # Read all spectral volumes and reconstruct the 4D array
    spectral_volumes = []
    
    for i, nifti_file in enumerate(nifti_files):
        print(f"Processing {os.path.basename(nifti_file)}...")
        
        # Read using SimpleITK
        img_sitk = sitk.ReadImage(nifti_file)
        img_array = sitk.GetArrayFromImage(img_sitk)
        
        # Convert from SimpleITK (z,y,x) back to original (x,y,z) format
        img_array = img_array.transpose(2, 1, 0)  # (z,y,x) -> (x,y,z)
        
        spectral_volumes.append(img_array)
        
        if i == 0:
            print(f"  Individual volume shape: {img_array.shape}")
            print(f"  Spacing: {img_sitk.GetSpacing()}")
    
    # Stack all spectral volumes to create 4D array
    # Shape should be (num_spectral, x, y, z) = (31, 104, 52, 12)
    reconstructed_data = np.stack(spectral_volumes, axis=0)
    print(f"Reconstructed data shape: {reconstructed_data.shape}")
    
    # Create the output dictionary with the same structure as original
    output_dict = {
        'data': reconstructed_data.astype(np.uint16)  # Match original dtype
    }
    
    # Add metadata if available
    if original_metadata:
        output_dict.update(original_metadata)
    else:
        # Use default metadata
        output_dict.update({
            'Resolution': np.array([[1, 1, 1]], dtype=np.uint8),
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

def verify_roundtrip_conversion(original_mat, reconstructed_mat):
    """
    Verify that the round-trip conversion (mat->nifti->mat) preserves the original data
    
    Args:
        original_mat: Path to original .mat file
        reconstructed_mat: Path to reconstructed .mat file
    
    Returns:
        True if data matches exactly, False otherwise
    """
    print("\\n=== VERIFYING ROUND-TRIP CONVERSION ===")
    
    if not (os.path.exists(original_mat) and os.path.exists(reconstructed_mat)):
        print("ERROR: One or both files do not exist for comparison")
        return False
    
    # Load both files
    original = sio.loadmat(original_mat)
    reconstructed = sio.loadmat(reconstructed_mat)
    
    print(f"Original file: {original_mat}")
    print(f"Reconstructed file: {reconstructed_mat}")
    
    # Compare data arrays
    orig_data = original['data']
    recon_data = reconstructed['data']
    
    print(f"\\nData comparison:")
    print(f"  Original shape: {orig_data.shape}")
    print(f"  Reconstructed shape: {recon_data.shape}")
    print(f"  Original dtype: {orig_data.dtype}")
    print(f"  Reconstructed dtype: {recon_data.dtype}")
    
    # Check if shapes match
    shapes_match = orig_data.shape == recon_data.shape
    print(f"  Shapes match: {shapes_match}")
    
    if not shapes_match:
        print("  ERROR: Shapes do not match!")
        return False
    
    # Check if data matches exactly
    if orig_data.dtype != recon_data.dtype:
        print(f"  Data types differ, converting for comparison...")
        # Convert to same type for comparison
        if orig_data.dtype == np.uint16:
            recon_data = recon_data.astype(np.uint16)
        else:
            orig_data = orig_data.astype(recon_data.dtype)
    
    data_matches = np.array_equal(orig_data, recon_data)
    print(f"  Data matches exactly: {data_matches}")
    
    if not data_matches:
        # Check how close they are
        max_diff = np.max(np.abs(orig_data.astype(float) - recon_data.astype(float)))
        mean_diff = np.mean(np.abs(orig_data.astype(float) - recon_data.astype(float)))
        print(f"  Maximum difference: {max_diff}")
        print(f"  Mean difference: {mean_diff}")
        
        # Check if differences are negligible
        if max_diff < 1e-10:
            print("  Differences are negligible (likely floating point precision)")
            data_matches = True
    
    # Compare metadata
    print(f"\\nMetadata comparison:")
    metadata_keys = ['Resolution', 'Transform', 'spatial_dim']
    metadata_matches = True
    
    for key in metadata_keys:
        if key in original and key in reconstructed:
            orig_meta = original[key]
            recon_meta = reconstructed[key]
            key_matches = np.array_equal(orig_meta, recon_meta)
            print(f"  {key} matches: {key_matches}")
            if not key_matches:
                print(f"    Original: {orig_meta}")
                print(f"    Reconstructed: {recon_meta}")
                metadata_matches = False
    
    # Overall result
    overall_success = shapes_match and data_matches and metadata_matches
    print(f"\\n=== ROUND-TRIP VERIFICATION RESULT ===")
    print(f"SUCCESS: {overall_success}")
    
    if overall_success:
        print("✅ Perfect round-trip conversion!")
        print("✅ Original data can be exactly reconstructed")
    else:
        print("❌ Round-trip conversion has differences")
        print("❌ Check the issues above")
    
    return overall_success

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
    success = nifti_to_spectral_mat(nifti_input_dir, output_mat_file, original_mat_file)
    
    if success:
        print("\\n=== Conversion completed successfully ===")
        
        # Verify round-trip conversion
        roundtrip_success = verify_roundtrip_conversion(original_mat_file, output_mat_file)
        
        if roundtrip_success:
            print("\\n🎉 PERFECT ROUND-TRIP CONVERSION ACHIEVED! 🎉")
            print("The two scripts work perfectly together:")
            print("  1. main_mat2nifti_patient2_spectral.py: .mat → NIfTI")
            print("  2. main_nifti2mat_patient2_spectral.py: NIfTI → .mat")
        else:
            print("\\n⚠️  Round-trip conversion has some differences")
            print("Please check the verification results above")
    else:
        print("\\n❌ Conversion failed. Please check the error messages above.")
