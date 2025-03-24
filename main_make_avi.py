import os
import numpy as np
import scipy.io as sio
import nibabel as nib
from nilearn import plotting
import SimpleITK as sitk
import cv2

subject = "wip_patient2"
res = [2.3, 2.3, 5]
all_te = [63, 80, 105, 130, 160, 200, 300]

data_dir = f"/deneb_disk/data_from_justin_03_11_2025/Data to be shared/{subject}/data"
output_movie_file = f"/deneb_disk/data_from_justin_03_11_2025/Data to be shared/{subject}/data_output/movie2.avi"

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(output_movie_file, fourcc, 10.0, (512, 512))

for te in all_te:
    mat_file = f"{data_dir}/TE{te}.mat"
    mat = sio.loadmat(mat_file)
    b_all = mat["b"][0]

    for i, b in enumerate(b_all):
        nii_file = f"{data_dir}/TE{te}_bval{b}.reg.nii.gz"
        img_sitk = sitk.ReadImage(nii_file)
        img_array = sitk.GetArrayFromImage(img_sitk)
        
        # Save the image as a temporary NIfTI file
        temp_nii_file = f"{data_dir}/temp.nii.gz"
        sitk.WriteImage(img_sitk, temp_nii_file)
        
        nii_img = nib.load(temp_nii_file)
        cut_coords = [coord / 2 for coord in nii_img.shape[:3]]
        cut_coords = np.array(cut_coords) * np.array(nii_img.affine.diagonal()[:3])

        # Generate the plot
        display = plotting.plot_anat(temp_nii_file, display_mode='ortho', cut_coords=cut_coords, draw_cross=False,vmax=1000,vmin=0)
        
        # Save the plot as an image
        temp_img_file = f"{data_dir}/temp.png"
        display.savefig(temp_img_file)
        display.close()
        
        # Read the image using OpenCV
        frame = cv2.imread(temp_img_file)
        
        # Resize the frame to match the video size
        frame = cv2.resize(frame, (512, 512))
        
        # Write the frame to the video
        out.write(frame)

# The FPS is set during the initialization of VideoWriter

# Release the video writer
out.release()

print(f"Movie saved as {output_movie_file}")