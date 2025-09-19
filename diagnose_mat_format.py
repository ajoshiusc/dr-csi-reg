#!/usr/bin/env python3
"""
Diagnostic script to analyze .mat file format issues
"""

import sys
import os
import numpy as np
try:
    import scipy.io as sio
    from scipy.io import whosmat
except ImportError:
    print("❌ scipy not available")
    sys.exit(1)

def analyze_mat_file(filepath):
    """Analyze a .mat file for format issues"""
    print(f"\n=== Analyzing: {os.path.basename(filepath)} ===")
    print(f"Full path: {filepath}")
    
    # Check file existence and basic info
    if not os.path.exists(filepath):
        print("❌ File does not exist")
        return False
    
    file_size = os.path.getsize(filepath)
    print(f"File size: {file_size / (1024*1024):.2f} MB")
    
    try:
        # First, try to get basic info without loading
        print("\n1. Checking file structure...")
        var_info = whosmat(filepath)
        print(f"Variables found: {len(var_info)}")
        for name, shape, dtype in var_info:
            print(f"   {name}: {shape} ({dtype})")
    except Exception as e:
        print(f"❌ Error reading file structure: {e}")
        return False
    
    try:
        # Try to load the file
        print("\n2. Loading file...")
        mat_data = sio.loadmat(filepath)
        print("✅ File loaded successfully")
        
        # Check keys
        data_keys = [k for k in mat_data.keys() if not k.startswith('__')]
        print(f"Data keys: {data_keys}")
        
        # Check for required fields
        required_fields = ['data']
        optional_fields = ['resolution', 'transform', 'spatial_dim']
        
        print("\n3. Checking required fields...")
        for field in required_fields:
            if field in mat_data:
                data = mat_data[field]
                print(f"✅ {field}: shape={data.shape}, dtype={data.dtype}")
                
                # Check for common issues
                if field == 'data':
                    if len(data.shape) != 4:
                        print(f"⚠️  Warning: Expected 4D data, got {len(data.shape)}D")
                    if data.size == 0:
                        print("❌ Error: Data array is empty")
                    if np.any(np.isnan(data)):
                        print("⚠️  Warning: Data contains NaN values")
                    if np.any(np.isinf(data)):
                        print("⚠️  Warning: Data contains infinite values")
                    
                    # Check data range
                    print(f"   Data range: [{np.min(data):.3f}, {np.max(data):.3f}]")
                    print(f"   Data mean: {np.mean(data):.3f}")
                    
            else:
                print(f"❌ Missing required field: {field}")
                return False
        
        print("\n4. Checking optional fields...")
        for field in optional_fields:
            if field in mat_data:
                data = mat_data[field]
                print(f"✅ {field}: shape={data.shape}, dtype={data.dtype}")
                if field == 'resolution':
                    print(f"   Resolution format: {data.shape} - {data}")
            else:
                print(f"⚠️  Optional field missing: {field}")
        
        # Check MATLAB version compatibility
        print("\n5. Checking MATLAB version compatibility...")
        if '__version__' in mat_data:
            print(f"MATLAB version: {mat_data['__version__']}")
        if '__header__' in mat_data:
            header = mat_data['__header__'].decode('utf-8') if isinstance(mat_data['__header__'], bytes) else str(mat_data['__header__'])
            print(f"File header: {header}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Try alternative loading methods
        print("\n6. Trying alternative loading methods...")
        
        try:
            # Try loading with different parameters
            mat_data = sio.loadmat(filepath, matlab_compatible=True)
            print("✅ Loaded with matlab_compatible=True")
            return True
        except Exception as e2:
            print(f"❌ matlab_compatible=True failed: {e2}")
        
        try:
            # Try loading with squeeze_me=False
            mat_data = sio.loadmat(filepath, squeeze_me=False)
            print("✅ Loaded with squeeze_me=False")
            return True
        except Exception as e3:
            print(f"❌ squeeze_me=False failed: {e3}")
        
        try:
            # Try loading specific version
            mat_data = sio.loadmat(filepath, mat_dtype=True)
            print("✅ Loaded with mat_dtype=True")
            return True
        except Exception as e4:
            print(f"❌ mat_dtype=True failed: {e4}")
        
        return False

def suggest_fixes(filepath):
    """Suggest fixes for common .mat file issues"""
    print(f"\n=== Suggested Fixes for {os.path.basename(filepath)} ===")
    
    print("1. Try converting the file in MATLAB:")
    print("   % Load in MATLAB")
    print(f"   data = load('{filepath}');")
    print("   % Save in compatible format")
    print("   save('converted_file.mat', '-struct', 'data', '-v7.3');")
    
    print("\n2. Try using different scipy.io.loadmat parameters:")
    print("   import scipy.io as sio")
    print(f"   data = sio.loadmat('{filepath}', matlab_compatible=True)")
    print("   # or")
    print(f"   data = sio.loadmat('{filepath}', squeeze_me=False, struct_as_record=False)")
    
    print("\n3. If the file is HDF5 format (.mat v7.3):")
    print("   import h5py")
    print(f"   with h5py.File('{filepath}', 'r') as f:")
    print("       data = f['data'][:]")
    
    print("\n4. Check file encoding/corruption:")
    print(f"   file '{filepath}'")
    print(f"   hexdump -C '{filepath}' | head")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_mat_format.py <mat_file1> [mat_file2] ...")
        print("\nThis script will analyze .mat files for format compatibility issues")
        sys.exit(1)
    
    print("========================================")
    print("DR-CSI .mat File Format Diagnostic")
    print("========================================")
    
    success_count = 0
    total_count = len(sys.argv) - 1
    
    for filepath in sys.argv[1:]:
        success = analyze_mat_file(filepath)
        if success:
            success_count += 1
        else:
            suggest_fixes(filepath)
    
    print(f"\n========================================")
    print(f"SUMMARY: {success_count}/{total_count} files analyzed successfully")
    
    if success_count < total_count:
        print("\n⚠️  Some files have format issues. See suggestions above.")
        print("Common solutions:")
        print("1. Re-save files in MATLAB with '-v7' or '-v7.3' format")
        print("2. Use h5py for HDF5-based .mat files")
        print("3. Check for file corruption during transfer")
    else:
        print("✅ All files appear to have compatible formats!")