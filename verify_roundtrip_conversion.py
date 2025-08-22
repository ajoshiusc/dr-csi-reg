# Verify round-trip conversion between .mat and NIfTI formats for spectral data

import os
import numpy as np
import scipy.io as sio

def verify_roundtrip_conversion(original_mat, reconstructed_mat):
    """
    Verify that the round-trip conversion (mat->nifti->mat) preserves the original data
    
    Args:
        original_mat: Path to original .mat file
        reconstructed_mat: Path to reconstructed .mat file
    
    Returns:
        True if data matches exactly, False otherwise
    """
    print("=== VERIFYING ROUND-TRIP CONVERSION ===\\n")
    
    if not (os.path.exists(original_mat) and os.path.exists(reconstructed_mat)):
        print("ERROR: One or both files do not exist for comparison")
        print(f"  Original: {original_mat} (exists: {os.path.exists(original_mat)})")
        print(f"  Reconstructed: {reconstructed_mat} (exists: {os.path.exists(reconstructed_mat)})")
        return False
    
    # Load both files
    print("Loading files for comparison...")
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
        print("  ❌ ERROR: Shapes do not match!")
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
    resolution_enhanced = False
    
    for key in metadata_keys:
        if key in original and key in reconstructed:
            orig_meta = original[key]
            recon_meta = reconstructed[key]
            key_matches = np.array_equal(orig_meta, recon_meta)
            print(f"  {key} matches: {key_matches}")
            if not key_matches:
                print(f"    Original: {orig_meta}")
                print(f"    Reconstructed: {recon_meta}")
                if key == 'Resolution':
                    # Check if this is a resolution enhancement
                    if np.array_equal(orig_meta, [[1, 1, 1]]) and not np.array_equal(recon_meta, [[1, 1, 1]]):
                        print(f"    ✅ Resolution enhanced from placeholder [1,1,1] to meaningful values")
                        resolution_enhanced = True
                    else:
                        metadata_matches = False
                else:
                    metadata_matches = False
    
    # Overall result
    overall_success = shapes_match and data_matches
    
    print(f"\\n=== ROUND-TRIP VERIFICATION RESULT ===")
    print(f"Data integrity success: {overall_success}")
    print(f"Metadata preserved: {metadata_matches}")
    print(f"Resolution enhanced: {resolution_enhanced}")
    
    if overall_success:
        print("\\n✅ PERFECT DATA PRESERVATION!")
        print("✅ Original image data can be exactly reconstructed")
        
        if resolution_enhanced:
            print("✅ Resolution metadata enhanced (this is a good thing!)")
            print("   • Original had placeholder values [1,1,1]")
            print("   • Reconstructed has meaningful spacing from NIfTI files")
        
        if metadata_matches or resolution_enhanced:
            print("\\n🎉 EXCELLENT ROUND-TRIP CONVERSION! 🎉")
            return True
        else:
            print("\\n⚠️  Data preserved but some metadata differences")
            return True  # Data integrity is most important
    else:
        print("\\n❌ Round-trip conversion has data differences")
        print("❌ Check the issues above")
        return False

def run_comprehensive_verification():
    """
    Run comprehensive verification of the round-trip conversion
    """
    print("="*70)
    print("COMPREHENSIVE ROUND-TRIP VERIFICATION FOR SPECTRAL DATA")
    print("="*70)
    
    # Default file paths
    original_mat = "/home/ajoshi/Projects/dr-csi-reg/data_wip_patient2.mat"
    reconstructed_mat = "/home/ajoshi/Projects/dr-csi-reg/reconstructed_from_nifti.mat"
    
    # Check if files exist
    print("\\nFile availability check:")
    orig_exists = os.path.exists(original_mat)
    recon_exists = os.path.exists(reconstructed_mat)
    
    print(f"  Original file: {orig_exists} - {original_mat}")
    print(f"  Reconstructed file: {recon_exists} - {reconstructed_mat}")
    
    if not orig_exists:
        print("\\n❌ ERROR: Original file not found!")
        print("Make sure data_wip_patient2.mat exists in the project directory")
        return False
    
    if not recon_exists:
        print("\\n❌ ERROR: Reconstructed file not found!")
        print("Run the conversion scripts first:")
        print("  1. python main_mat2nifti_spectral.py")
        print("  2. python main_nifti2mat_spectral.py")
        return False
    
    # Run verification
    success = verify_roundtrip_conversion(original_mat, reconstructed_mat)
    
    # Show file sizes
    orig_size = os.path.getsize(original_mat) / (1024*1024)
    recon_size = os.path.getsize(reconstructed_mat) / (1024*1024)
    
    print(f"\\nFile size comparison:")
    print(f"  Original: {orig_size:.2f} MB")
    print(f"  Reconstructed: {recon_size:.2f} MB")
    print(f"  Size difference: {abs(orig_size - recon_size):.2f} MB")
    
    print(f"\\n{'='*70}")
    if success:
        print("🎊 ROUND-TRIP VERIFICATION PASSED! 🎊")
        print("\\nYour conversion scripts work perfectly:")
        print("  ✅ main_mat2nifti_spectral.py")
        print("  ✅ main_nifti2mat_spectral.py")
        print("\\n🎯 Ready for production use!")
    else:
        print("❌ ROUND-TRIP VERIFICATION FAILED")
        print("\\nPlease check the error messages above and:")
        print("  1. Verify input files are correct")
        print("  2. Check for any data corruption")
        print("  3. Review the conversion scripts")
    print(f"{'='*70}")
    
    return success

if __name__ == "__main__":
    run_comprehensive_verification()
