
# Imports
from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
from deformation_utils import apply_nonlinear_deformation_to_nifti_files
from nifti_registration_pipeline import register_nifti
from spectral_nifti_to_mat import convert_spectral_nifti_to_mat
import scipy.io as sio

# Input and output paths
input_mat = "/home/ajoshi/Downloads/Phantom_data.mat"  # Path to input .mat file
output_dir = "phantom_nifti_output"  # Directory for converted NIFTI files
deformed_dir = "phantom_nifti_deformed"  # Directory for deformed NIFTI files

# Step 1: Convert spectral .mat file to NIFTI format
print("Converting spectral .mat file to NIFTI format...")
convert_spectral_mat_to_nifti(input_mat, output_dir)

# Step 2: Apply nonlinear deformation to NIFTI files
print("Applying nonlinear deformation to NIFTI files...")
apply_nonlinear_deformation_to_nifti_files(output_dir, deformed_dir)

# Step 3: Register deformed NIFTI files
print("Registering deformed NIFTI files...")
registered_dir = deformed_dir + "_registered"
register_nifti(deformed_dir, registered_dir, processes=1)

# Step 4: Convert registered NIFTI files back to .mat format
print("Converting registered NIFTI files back to .mat format...")
output_mat = "phantom_reconstructed.mat"
convert_spectral_nifti_to_mat(registered_dir, output_mat)

# Step 5: Verify the output .mat file
print("Verifying the output .mat file...")
reconstructed_data = sio.loadmat(output_mat)
print("Reconstructed data keys:", reconstructed_data.keys())
if 'data' in reconstructed_data:
	print("Reconstructed data shape:", reconstructed_data['data'].shape)
else:
	print("'data' key not found in reconstructed .mat file.")