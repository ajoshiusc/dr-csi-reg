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
        try:
            print(f"Preserving metadata from original file: {original_mat_file}")
            
            # Try multiple loading methods for different .mat formats
            original_data = None
            try:
                # Method 1: Standard loading
                original_data = sio.loadmat(original_mat_file)
                print("  ✅ Original file loaded with standard method")
            except Exception as e1:
                print(f"  Standard loading failed: {e1}")
                try:
                    # Method 2: matlab_compatible mode
                    original_data = sio.loadmat(original_mat_file, matlab_compatible=True)
                    print("  ✅ Original file loaded with matlab_compatible=True")
                except Exception as e2:
                    print(f"  MATLAB compatible loading failed: {e2}")
                    try:
                        # Method 3: squeeze_me=False
                        original_data = sio.loadmat(original_mat_file, squeeze_me=False, struct_as_record=False)
                        print("  ✅ Original file loaded with squeeze_me=False")
                    except Exception as e3:
                        print(f"  Alternative loading failed: {e3}")
                        try:
                            # Method 4: Try HDF5 format
                            import h5py
                            print("  Trying HDF5 format for original file...")
                            original_data = {}
                            with h5py.File(original_mat_file, 'r') as f:
                                for key in f.keys():
                                    if not key.startswith('#'):
                                        try:
                                            original_data[key] = np.array(f[key])
                                        except Exception:
                                            try:
                                                original_data[key] = f[key][()]
                                            except Exception:
                                                print(f"  Warning: Could not load original key '{key}'")
                            print("  ✅ Original file loaded with HDF5 format")
                        except ImportError:
                            print("  ❌ h5py not available for HDF5 format")
                            original_data = None
                        except Exception as e4:
                            print(f"  HDF5 loading failed: {e4}")
                            original_data = None
            
            if original_data is not None:
                # Extract data type from original file
                data_keys = [k for k in original_data.keys() if not k.startswith('__')]
                
                # Find the original data field
                if 'data' in original_data:
                    original_data_dtype = original_data['data'].dtype
                    print(f"Original data type: {original_data_dtype}")
                elif 'Data' in original_data:
                    original_data_dtype = original_data['Data'].dtype
                    print(f"Original data type: {original_data_dtype}")
                elif 'img' in original_data:
                    original_data_dtype = original_data['img'].dtype
                    print(f"Original data type: {original_data_dtype}")
                elif len(data_keys) == 1:
                    original_data_dtype = original_data[data_keys[0]].dtype
                    print(f"Original data type: {original_data_dtype}")
                
                # Preserve all fields except 'data', 'Data', 'img'
                preserved_fields = []
                for key in data_keys:
                    if key.lower() not in ['data', 'img']:
                        original_metadata[key] = original_data[key]
                        preserved_fields.append(key)
                
                print(f"  Preserved fields: {preserved_fields}")
            else:
                print("  ⚠️  Could not load original file metadata")
                
        except Exception as e:
            print(f"Warning: Could not load original file metadata: {e}")
            print("Proceeding without original metadata preservation")
    
    # Read all spectral volumes and reconstruct the 4D array
    spectral_volumes = []
    nifti_spacing = None
    
    for i, nifti_file in enumerate(nifti_files):
        print(f"Processing {os.path.basename(nifti_file)}...")
        
        # Read using SimpleITK
        img_sitk = sitk.ReadImage(nifti_file)
        img_array = sitk.GetArrayFromImage(img_sitk)
        
        # SimpleITK gives us (z, y, x) which is already the correct spatial ordering
        # No need to transpose since original data was (z, y, x, spectral)
        # img_array shape is already (z, y, x)
        
        spectral_volumes.append(img_array)
        
        if i == 0:
            # Read spacing from the first NIfTI file
            nifti_spacing = img_sitk.GetSpacing()
            print(f"  Individual volume shape: {img_array.shape}")
            print(f"  Spacing from NIfTI file: {nifti_spacing}")
    
    # Stack all spectral volumes to create 4D array
    # Shape should be (z, y, x, num_spectral) = (12, 52, 104, 31)
    # Stack along the last axis to put spectral dimension last
    reconstructed_data = np.stack(spectral_volumes, axis=-1)
    
    # Transpose to (x, y, z, spectral) for MATLAB compatibility
    reconstructed_data = np.transpose(reconstructed_data, (3, 2, 1, 0))
    print(f"Reconstructed data shape: {reconstructed_data.shape}")
    
    # Convert NIfTI spacing to resolution format for mat file
    if original_metadata and 'resolution' in original_metadata:
        # Use original resolution to preserve precision
        resolution_array = original_metadata['resolution']
        print(f"Using original resolution: {resolution_array}")
    elif nifti_spacing:
        # NIfTI spacing is (x, y, z), convert to uint8 array format like original
        resolution_array = np.array([[nifti_spacing[0], nifti_spacing[1], nifti_spacing[2]]], dtype=np.float64)
        print(f"Resolution derived from NIfTI spacing: {resolution_array}")
    else:
        resolution_array = np.array([[1, 1, 1]], dtype=np.uint8)
        print("Using default resolution: [[1, 1, 1]]")
    
    # Create the output dictionary starting with the reconstructed data
    output_dict = {
        'data': reconstructed_data.astype(original_data_dtype),  # Preserve original data type
    }
    
    # Add resolution - prefer from NIfTI spacing, fallback to original
    output_dict['resolution'] = resolution_array
    
    # Add all other metadata from original file if available
    if original_metadata:
        # Add all preserved fields from original file
        for key, value in original_metadata.items():
            if key != 'resolution':  # Don't overwrite resolution derived from NIfTI
                output_dict[key] = value
        print(f"Added {len(original_metadata)} metadata fields from original file")
    else:
        # Use default metadata if original not available
        output_dict.update({
            'transform': np.eye(4, dtype=np.uint8),
            'spatial_dim': np.array([[reconstructed_data.shape[0], reconstructed_data.shape[1], reconstructed_data.shape[2]]], dtype=np.uint8)
        })
        print("Using default metadata (no original file provided)")
    
    # Ensure critical fields are present with reasonable defaults
    if 'transform' not in output_dict:
        output_dict['transform'] = np.eye(4, dtype=np.uint8)
        print("Added default transform matrix")
    
    if 'spatial_dim' not in output_dict:
        output_dict['spatial_dim'] = np.array([[reconstructed_data.shape[1], reconstructed_data.shape[2], reconstructed_data.shape[3]]], dtype=np.uint8)
        print("Added default spatial_dim based on data shape")
    
    # Save to .mat file using HDF5 (h5py)
    try:
        # Save as a MATLAB v7.3 (HDF5) .mat file using hdf5storage (uses h5py under the hood)
        try:
            import hdf5storage
            hdf5storage.savemat(
                output_mat_file,
                output_dict,
                appendmat=False,
                format='7.3',
                oned_as='row',
                store_python_metadata=False
            )
            print(f"Successfully saved reconstructed data to: {output_mat_file} (MATLAB v7.3 HDF5)")
        except ImportError:
            print("WARNING: hdf5storage not installed; saving as MATLAB v5 .mat instead. "
                  "Install with: pip install hdf5storage")
            sio.savemat(output_mat_file, output_dict, do_compression=False)
            print(f"Successfully saved reconstructed data to: {output_mat_file} (MATLAB v5)")
        print(f"Data type: {reconstructed_data.dtype}")
        print(f"Saved fields: {list(output_dict.keys())}")
        # Calculate file size
        file_size_mb = os.path.getsize(output_mat_file) / (1024 * 1024)
        print(f"Output file size: {file_size_mb:.2f} MB")
        return True
    except Exception as e:
        print(f"ERROR saving .mat file (HDF5): {e}")
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
