# Read data_wip_patient2.mat file and save as .nii.gz files with correct spectral dimension handling

import os
import numpy as np
import scipy.io as sio
import nibabel as nib
from nilearn import plotting
import SimpleITK as sitk

def process_patient2_spectral_format(mat_file, output_dir, res):
    """
    Process patient2 format data_wip_patient2.mat file
    The data shape is (31, 104, 52, 12) where:
    - 31 is the spectral dimension (number of spectral points)
    - 104, 52, 12 are the spatial dimensions (x, y, z)
    """
    print("Processing patient2 format file with spectral dimension...")
    
    if not os.path.exists(mat_file):
        print(f"ERROR: file {mat_file} does not exist.")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    mat = sio.loadmat(mat_file)
    
    # Extract data
    img_data = mat['data']  # Shape: (31, 104, 52, 12)
    resolution = mat['Resolution'][0] if 'Resolution' in mat else [1, 1, 1]
    
    print(f"Original data shape: {img_data.shape}")
    print(f"Spectral points: {img_data.shape[0]}")
    print(f"Spatial dimensions: {img_data.shape[1:]}")
    print(f"Resolution: {resolution}")
    
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
        
        # Set spacing - assuming res is [x_spacing, y_spacing, z_spacing]
        spacing = [float(res[0]), float(res[1]), float(res[2])]
        img_sitk.SetSpacing(spacing)
        
        # Generate filename for this spectral point
        filename = f"{output_dir}/spectral_point_{spectral_idx:03d}.nii.gz"
        sitk.WriteImage(img_sitk, filename)
        print(f"Saved spectral point {spectral_idx}: {filename}")
    
    # Also create PNG visualizations for the first few spectral points
    print("\\nCreating PNG visualizations for first 5 spectral points...")
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
        f.write("Data from data_wip_patient2.mat (spectral format)\\n")
        f.write(f"Original data shape: {img_data.shape}\\n")
        f.write(f"Spectral dimension: {img_data.shape[0]} (first dimension)\\n")
        f.write(f"Spatial dimensions: {img_data.shape[1:]} (x, y, z)\\n")
        f.write(f"Resolution: {resolution}\\n")
        f.write(f"Number of NIfTI files created: {num_spectral_points}\\n")
        f.write(f"Spacing used: {spacing}\\n")
    
    print(f"Saved metadata: {metadata_file}")
    
    return num_spectral_points

def convert_back_to_spectral_mat(input_dir, output_mat_file):
    """
    Convert the spectral NIfTI files back to a .mat file
    """
    print("Converting spectral NIfTI files back to .mat format...")
    
    # Find all spectral point files
    spectral_files = sorted([f for f in os.listdir(input_dir) 
                           if f.startswith("spectral_point_") and f.endswith(".nii.gz")])
    
    print(f"Found {len(spectral_files)} spectral files")
    
    if not spectral_files:
        print("No spectral files found!")
        return
    
    # Read all spectral volumes
    spectral_volumes = []
    for spec_file in spectral_files:
        spec_path = os.path.join(input_dir, spec_file)
        img_sitk = sitk.ReadImage(spec_path)
        img_array = sitk.GetArrayFromImage(img_sitk)
        
        # Convert back from (z, y, x) to (x, y, z)
        img_array = img_array.transpose(2, 1, 0)
        spectral_volumes.append(img_array)
    
    # Stack all spectral volumes to recreate the original format
    # Shape will be (num_spectral, x, y, z) = (31, 104, 52, 12)
    reconstructed_data = np.stack(spectral_volumes, axis=0)
    
    print(f"Reconstructed data shape: {reconstructed_data.shape}")
    
    # Save to mat file
    sio.savemat(output_mat_file, {
        'data': reconstructed_data,
        'num_spectral_points': len(spectral_files),
        'note': 'Reconstructed spectral data from data_wip_patient2.mat'
    })
    
    print(f"Saved reconstructed spectral data to: {output_mat_file}")
    return output_mat_file

if __name__ == "__main__":
    # Configuration
    mat_file = "/home/ajoshi/Projects/dr-csi-reg/data_wip_patient2.mat"
    output_dir = "/home/ajoshi/Projects/dr-csi-reg/patient2_nifti_spectral_output"
    
    # Default resolution (adjust as needed)
    res = [2.3, 2.3, 5.0]
    
    print("=== Processing Patient2 Data with Spectral Dimension ===")
    print(f"Input file: {mat_file}")
    print(f"Output directory: {output_dir}")
    print(f"Resolution: {res}")
    
    # Process the data
    num_spectral = process_patient2_spectral_format(mat_file, output_dir, res)
    
    # Convert back to mat format for verification
    if num_spectral > 0:
        reconstructed_mat = f"{output_dir}/reconstructed_spectral_data.mat"
        convert_back_to_spectral_mat(output_dir, reconstructed_mat)
    
    print("\\n=== Processing Complete ===")
    print(f"Created {num_spectral} spectral NIfTI files")
    print("Files are saved with naming: spectral_point_000.nii.gz, spectral_point_001.nii.gz, etc.")
