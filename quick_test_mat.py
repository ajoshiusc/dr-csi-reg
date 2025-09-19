#!/usr/bin/env python3
"""
Quick test script for your specific HPC .mat files
"""

import sys
import os

# Test files from your error message
test_files = [
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub8.mat",
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_sub6.mat", 
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_wip_patient2.mat",
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_sub1.mat",
    "/deneb_disk/dr_csi_data/software compatible prostate data/data_patient1.mat"
]

def quick_test(filepath):
    """Quick test of a single file"""
    print(f"\n=== Testing: {os.path.basename(filepath)} ===")
    
    # Check file existence
    if not os.path.exists(filepath):
        print("❌ File does not exist")
        return False
    
    print(f"✅ File exists (size: {os.path.getsize(filepath) / (1024*1024):.1f} MB)")
    
    # Test scipy.io loading
    try:
        import scipy.io as sio
        data = sio.loadmat(filepath)
        print("✅ Standard scipy.io.loadmat works")
        
        # Check keys
        keys = [k for k in data.keys() if not k.startswith('__')]
        print(f"   Keys: {keys}")
        
        # Check data field
        if 'data' in data:
            shape = data['data'].shape
            dtype = data['data'].dtype
            print(f"   Data: shape={shape}, dtype={dtype}")
            return True
        else:
            print("   ⚠️  No 'data' field found")
            if keys:
                # Try first available key
                first_key = keys[0]
                shape = data[first_key].shape if hasattr(data[first_key], 'shape') else 'unknown'
                dtype = data[first_key].dtype if hasattr(data[first_key], 'dtype') else 'unknown'
                print(f"   First key '{first_key}': shape={shape}, dtype={dtype}")
            return False
            
    except Exception as e:
        print(f"❌ scipy.io.loadmat failed: {e}")
        
        # Try HDF5
        try:
            import h5py
            with h5py.File(filepath, 'r') as f:
                keys = list(f.keys())
                print(f"✅ HDF5 format detected, keys: {keys}")
                return True
        except ImportError:
            print("❌ h5py not available to test HDF5 format")
        except Exception as e2:
            print(f"❌ HDF5 loading also failed: {e2}")
        
        return False

if __name__ == "__main__":
    print("========================================")
    print("Quick HPC .mat File Format Test")
    print("========================================")
    
    if len(sys.argv) > 1:
        # Test specific files from command line
        for filepath in sys.argv[1:]:
            quick_test(filepath)
    else:
        # Test the predefined files
        working_files = []
        broken_files = []
        
        for filepath in test_files:
            if quick_test(filepath):
                working_files.append(filepath)
            else:
                broken_files.append(filepath)
        
        print(f"\n========================================")
        print(f"SUMMARY")
        print(f"========================================")
        print(f"Working files: {len(working_files)}")
        print(f"Problem files: {len(broken_files)}")
        
        if working_files:
            print("\n✅ Working files:")
            for f in working_files:
                print(f"   {os.path.basename(f)}")
        
        if broken_files:
            print("\n❌ Problem files:")
            for f in broken_files:
                print(f"   {os.path.basename(f)}")
            
            print("\n🔧 Suggested fixes for problem files:")
            print("1. Convert in MATLAB: save('file.mat', '-v7') or save('file.mat', '-v7.3')")
            print("2. Install h5py: pip install h5py")
            print("3. Use fix_mat_format.py to convert to compatible format")
        
        if not working_files and not broken_files:
            print("❌ No files found - check file paths")