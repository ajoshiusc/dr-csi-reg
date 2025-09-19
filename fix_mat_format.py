#!/usr/bin/env python3
"""
Enhanced .mat file loader that handles different formats including HDF5
"""

import sys
import os
import numpy as np

def load_mat_file_robust(filepath):
    """
    Robust .mat file loader that tries multiple approaches
    Returns (success, data_dict, error_message)
    """
    
    print(f"Attempting to load: {filepath}")
    
    # Method 1: Standard scipy.io.loadmat
    try:
        import scipy.io as sio
        print("  Trying standard scipy.io.loadmat...")
        data = sio.loadmat(filepath)
        print("  ✅ Loaded with scipy.io.loadmat")
        return True, data, None
    except Exception as e:
        print(f"  ❌ scipy.io.loadmat failed: {e}")
    
    # Method 2: scipy.io.loadmat with struct_as_record=False
    try:
        import scipy.io as sio
        print("  Trying scipy.io.loadmat with struct_as_record=False...")
        data = sio.loadmat(filepath, struct_as_record=False)
        print("  ✅ Loaded with struct_as_record=False")
        return True, data, None
    except Exception as e:
        print(f"  ❌ struct_as_record=False failed: {e}")
    
    # Method 3: scipy.io.loadmat with squeeze_me=True
    try:
        import scipy.io as sio
        print("  Trying scipy.io.loadmat with squeeze_me=True...")
        data = sio.loadmat(filepath, squeeze_me=True)
        print("  ✅ Loaded with squeeze_me=True")
        return True, data, None
    except Exception as e:
        print(f"  ❌ squeeze_me=True failed: {e}")
    
    # Method 4: h5py for v7.3 MAT files (HDF5 format)
    try:
        import h5py
        print("  Trying h5py for HDF5/v7.3 format...")
        with h5py.File(filepath, 'r') as f:
            data = {}
            def extract_data(name, obj):
                if isinstance(obj, h5py.Dataset):
                    data[name] = obj[()]
                    if hasattr(obj[()], 'dtype') and obj[()].dtype.kind == 'U':
                        # Handle Unicode strings
                        try:
                            data[name] = str(obj[()].astype(str))
                        except:
                            pass
            f.visititems(extract_data)
            print("  ✅ Loaded with h5py")
            return True, data, None
    except ImportError:
        print("  ❌ h5py not available")
    except Exception as e:
        print(f"  ❌ h5py failed: {e}")
    
    # Method 5: scipy.io.loadmat with different parameters  
    try:
        import scipy.io as sio
        print("  Trying scipy.io.loadmat with appendmat=False...")
        data = sio.loadmat(filepath, appendmat=False, squeeze_me=True, struct_as_record=False)
        print("  ✅ Loaded with appendmat=False and other options")
        return True, data, None
    except Exception as e:
        print(f"  ❌ appendmat=False failed: {e}")
    
    return False, None, "All loading methods failed"

def convert_to_compatible_format(input_file, output_file):
    """
    Convert a problematic .mat file to a compatible format
    """
    print(f"\n=== Converting {input_file} to compatible format ===")
    
    # Load the file using robust method
    success, data, error = load_mat_file_robust(input_file)
    
    if not success:
        print(f"❌ Failed to load input file: {error}")
        return False
    
    print(f"✅ Successfully loaded input file")
    print(f"Keys found: {[k for k in data.keys() if not k.startswith('__')]}")
    
    # Check for the main data
    data_field = None
    for key in ['data', 'img', 'image']:
        if key in data:
            data_field = key
            break
    
    if data_field is None:
        print("❌ No recognized data field found (looking for 'data', 'img', or 'image')")
        return False
    
    main_data = data[data_field]
    print(f"Main data shape: {main_data.shape}, dtype: {main_data.dtype}")
    
    # Create compatible format
    compatible_data = {
        'data': main_data.astype(np.float64)  # Ensure compatible data type
    }
    
    # Check for resolution field (with fallback to old format)
    if 'resolution' in data:
        resolution = data['resolution']
    elif 'Resolution' in data:
        resolution = data['Resolution']
    else:
        resolution = None
    
    # Handle resolution
    if resolution is not None:
        print(f"Found resolution: {resolution}, shape: {resolution.shape}")
        if resolution.size >= 3:
            # Use provided resolution (ensure it's in correct format)
            compatible_data['resolution'] = resolution.reshape(1, -1)[:, :3]
        else:
            compatible_data['resolution'] = np.array([[1, 1, 1]], dtype=np.uint8)
    else:
        compatible_data['resolution'] = np.array([[1, 1, 1]], dtype=np.uint8)
    
    # Add transform matrix
    compatible_data['transform'] = np.eye(4)
    
    # Add spatial dimensions
    if main_data.ndim >= 3:
        compatible_data['spatial_dim'] = np.array([[main_data.shape[-3], main_data.shape[-2], main_data.shape[-1]]], dtype=np.uint8)
    else:
        compatible_data['spatial_dim'] = np.array([[1, 1, 1]], dtype=np.uint8)
    
    # Save the compatible version
    try:
        import scipy.io as sio
        sio.savemat(output_file, compatible_data)
        print(f"✅ Saved compatible file: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to save compatible file: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_mat_format.py <input_file> [output_file]")
        print("If output_file not specified, will use input_file_fixed.mat")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_fixed{ext}"
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)
    
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Test loading first
    print("\n=== Testing file loading ===")
    success, data, error = load_mat_file_robust(input_file)
    
    if success:
        print("✅ File can be loaded successfully")
        print(f"Keys: {[k for k in data.keys() if not k.startswith('__')]}")
        
        # Try to convert
        if convert_to_compatible_format(input_file, output_file):
            print(f"\n✅ Conversion completed successfully!")
            print(f"You can now use: {output_file}")
        else:
            print(f"\n❌ Conversion failed")
            sys.exit(1)
    else:
        print(f"❌ Failed to load file: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()