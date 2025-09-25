#!/usr/bin/env python3
"""Profiled version of patient2 registration to analyze CPU usage"""

import sys
import cProfile
import pstats
import io
from pathlib import Path

# Add src to path
sys.path.append('src')
from spectral_mat_to_nifti import convert_spectral_mat_to_nifti
from nifti_registration_pipeline import register_nifti  
from spectral_nifti_to_mat import convert_spectral_nifti_to_mat


def main_registration():
    """Main registration workflow for profiling"""
    Path("patient2_output/nifti").mkdir(parents=True, exist_ok=True)
    Path("patient2_output/registration").mkdir(parents=True, exist_ok=True)
    
    print("🔍 Step 1: Converting MAT to NIfTI...")
    convert_spectral_mat_to_nifti("data/data_wip_patient2.mat", "patient2_output/nifti")
    
    print("🔍 Step 2: Registering NIfTI files...")
    register_nifti("patient2_output/nifti", "patient2_output/registration", processes=4)
    
    print("🔍 Step 3: Converting back to MAT...")
    convert_spectral_nifti_to_mat("patient2_output/registration", "patient2_output/data_wip_patient2_registered.mat", "data/data_wip_patient2.mat")


def profile_registration():
    """Profile the registration process"""
    print("🚀 Starting Profiled Registration")
    print("=" * 50)
    
    # Create profiler
    profiler = cProfile.Profile()
    
    try:
        # Run with profiling
        profiler.enable()
        main_registration()
        profiler.disable()
        
        print("✅ Registration completed successfully!")
        
    except KeyboardInterrupt:
        profiler.disable()
        print("\n⏹️ Registration interrupted by user")
    except Exception as e:
        profiler.disable()
        print(f"\n❌ Registration failed: {e}")
    
    # Analyze results
    print("\n📊 CPU Profiling Results:")
    print("=" * 50)
    
    # Create string buffer for stats
    stats_buffer = io.StringIO()
    stats = pstats.Stats(profiler, stream=stats_buffer)
    
    # Sort by cumulative time and show top functions
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
    
    # Get the stats string
    stats_output = stats_buffer.getvalue()
    print(stats_output)
    
    # Save detailed stats to file
    with open('patient2_profiling_results.txt', 'w') as f:
        f.write("Patient2 Registration CPU Profiling Results\n")
        f.write("=" * 50 + "\n")
        f.write(stats_output)
        
        # Also get stats sorted by total time
        f.write("\n\nSorted by Total Time:\n")
        f.write("-" * 30 + "\n")
        
        stats_buffer2 = io.StringIO()
        stats2 = pstats.Stats(profiler, stream=stats_buffer2)
        stats2.sort_stats('tottime')
        stats2.print_stats(20)
        f.write(stats_buffer2.getvalue())
    
    print(f"\n📄 Detailed profiling results saved to: patient2_profiling_results.txt")
    
    # Show GPU/CPU analysis
    analyze_cpu_vs_gpu_usage(stats)


def analyze_cpu_vs_gpu_usage(stats):
    """Analyze CPU vs GPU usage patterns"""
    print("\n🔍 CPU vs GPU Usage Analysis:")
    print("-" * 40)
    
    # Get stats as dictionary for analysis
    stats_dict = stats.get_stats()
    
    # Categories to look for
    cpu_intensive = []
    gpu_operations = []
    multiprocessing_overhead = []
    
    for func_key, func_stats in stats_dict.items():
        filename, line_num, func_name = func_key
        cumtime = func_stats[3]  # cumulative time
        
        # Categorize functions
        if any(keyword in filename.lower() for keyword in ['multiprocessing', 'pool', 'worker', 'process']):
            multiprocessing_overhead.append((func_name, cumtime, filename))
        elif any(keyword in func_name.lower() for keyword in ['cuda', 'gpu', 'torch', 'monai']):
            gpu_operations.append((func_name, cumtime, filename))
        elif cumtime > 0.1:  # Functions taking >0.1s
            cpu_intensive.append((func_name, cumtime, filename))
    
    print(f"🔥 Top CPU-Intensive Functions ({len(cpu_intensive)}):")
    for func_name, cumtime, filename in sorted(cpu_intensive, key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {cumtime:6.2f}s - {func_name} ({Path(filename).name})")
    
    print(f"\n🚀 GPU Operations ({len(gpu_operations)}):")
    for func_name, cumtime, filename in sorted(gpu_operations, key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {cumtime:6.2f}s - {func_name} ({Path(filename).name})")
    
    print(f"\n⚙️ Multiprocessing Overhead ({len(multiprocessing_overhead)}):")
    for func_name, cumtime, filename in sorted(multiprocessing_overhead, key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {cumtime:6.2f}s - {func_name} ({Path(filename).name})")


if __name__ == "__main__":
    profile_registration()