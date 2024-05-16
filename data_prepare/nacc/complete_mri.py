import os
import nibabel as nib
import numpy as np

# Path to the DICOM folder
dicom_folder = "/home/flik/Downloads/DICOM"

# Get all the nii files in the DICOM folder
nii_files = [f for f in os.listdir(dicom_folder) if f.endswith(".nii")]

# Sort the nii files to ensure they are concatenated in the correct order
nii_files.sort()

# Create an empty list to store the nii data arrays
nii_data_arrays = []

# Loop through each nii file and load the data array
for nii_file in nii_files:
    nii_path = os.path.join(dicom_folder, nii_file)
    nii_img = nib.load(nii_path)
    nii_data = nii_img.get_fdata()
    nii_data_arrays.append(nii_data)

# Concatenate the nii data arrays along the fourth dimension (time axis)
# images represent 3D volumes and concatenate them as a 4D volume
complete_mri_data = np.concatenate(nii_data_arrays, axis=2)

# Save the complete MRI data to a new nii file
complete_mri_img = nib.Nifti1Image(complete_mri_data, nii_img.affine)
nib.save(complete_mri_img, "/home/flik/Downloads/DICOM/complete_mri.nii")
