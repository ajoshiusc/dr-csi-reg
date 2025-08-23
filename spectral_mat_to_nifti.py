# Read spectral .mat file and save as .nii.gz files with correct spectral dimension handling

import os
import numpy as np
import scipy.io as sio
import nibabel as nib
from nilearn import plotting
import SimpleITK as sitk

def convert_spectral_mat_to_nifti(mat_file, output_dir, res=None):
    """
    Convert spectral format .mat file to individual NIfTI files
    
    The data shape is (N, X, Y, Z) where:
    - N is the spectral dimension (number of spectral points)
    - X, Y, Z are the spatial dimensions
    
    Args:
        mat_file (str): Path to input .mat file
        output_dir (str): Directory to save NIfTI files
        res (list): Optional resolution override [x, y, z]
    
    Returns:
        dict: Conversion results with statistics
    """
    print("Processing spectral format file...")
    
    if not os.path.exists(mat_file):
        print(f"ERROR: file {mat_file} does not exist.")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    mat = sio.loadmat(mat_file)
    
    # Extract data
    img_data = mat['data']  # Shape: (31, 104, 52, 12)
    
    # Read resolution from mat file, with fallback to parameter or default
    if 'Resolution' in mat:
        resolution = mat['Resolution'][0]
        print(f"Using resolution from mat file: {resolution}")
    elif res is not None:
        resolution = res
        print(f"Using provided resolution: {resolution}")
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
    # Configuration
    mat_file = "/home/ajoshi/Projects/dr-csi-reg/data_wip_patient2.mat"
    output_dir = "/home/ajoshi/Projects/dr-csi-reg/patient2_nifti_spectral_output"
    
    # Resolution will be read from the mat file automatically
    # You can optionally override it by passing res parameter
    
    print("=== Processing Spectral Data ===")
    print(f"Input file: {mat_file}")
    print(f"Output directory: {output_dir}")
    print("Resolution will be read from mat file")
    
    # Process the data (resolution will be read from mat file)
    num_spectral = convert_spectral_mat_to_nifti(mat_file, output_dir)
    
    print("\n=== Processing Complete ===")
    if num_spectral and num_spectral > 0:
        print(f"✅ Created {num_spectral} spectral NIfTI files")
        print("✅ Files saved with naming: spectral_point_000.nii.gz, spectral_point_001.nii.gz, etc.")
        print("✅ PNG visualizations created for first 5 spectral points")
        print("✅ Metadata saved to spectral_metadata.txt")
        print("\nTo convert back to .mat format, run:")
        print("python spectral_nifti_to_mat.py")
    else:
        print("❌ Processing failed. Check error messages above.")
