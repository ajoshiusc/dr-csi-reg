# Registration script with improved architecture - works with any NIfTI files
# Independent of hardcoded paths, TE values, or b-values

import os
import glob
import argparse
import numpy as np
import nibabel as nib
from registration import perform_nonlinear_registration
from multiprocessing import Pool


def generate_average_template(input_files, output_path):
    """Generate average template from multiple NIfTI files."""
    print(f"Generating average template from {len(input_files)} volumes...")
    
    if not input_files:
        print("ERROR: No input files provided")
        return False
    
    try:
        import nibabel as nib
        import numpy as np
        
        # Load first volume to get dimensions and affine
        first_img = nib.load(input_files[0])
        first_data = first_img.get_fdata()
        first_affine = first_img.affine
        first_header = first_img.header
        
        print(f"Template dimensions: {first_data.shape}")
        
        # Initialize accumulator
        volume_sum = np.zeros_like(first_data, dtype=np.float64)
        valid_count = 0
        
        # Accumulate all volumes
        for i, filepath in enumerate(input_files):
            print(f"  Processing volume {i+1}/{len(input_files)}")
            
            img = nib.load(filepath)
            data = img.get_fdata()
            
            # Check dimensions match
            if data.shape != first_data.shape:
                print(f"  Skipping {filepath} (dimension mismatch)")
                continue
                
            # Add to accumulator
            volume_sum += data.astype(np.float64)
            valid_count += 1
        
        if valid_count == 0:
            print("ERROR: No valid volumes found")
            return False
        
        # Calculate average
        average_volume = volume_sum / valid_count
        print(f"Averaged {valid_count} volumes")
        
        # Convert back to original data type
        if first_data.dtype != np.float64:
            average_volume = average_volume.astype(first_data.dtype)
        
        # Save average template
        avg_img = nib.Nifti1Image(average_volume, first_affine, first_header)
        nib.save(avg_img, output_path)
        print(f"✅ Average template saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate average template: {e}")
        return False


def generate_central_template(input_files, output_path):
    """Generate template using central (middle) volume."""
    if not input_files:
        print("ERROR: No input files provided")
        return False
    
    try:
        import nibabel as nib
        
        # Sort files and select central one
        sorted_files = sorted(input_files)
        central_index = len(sorted_files) // 2
        central_file = sorted_files[central_index]
        
        print(f"Using central volume template: {os.path.basename(central_file)}")
        print(f"  (Volume {central_index + 1} of {len(sorted_files)} sorted files)")
        
        # Copy central file to output
        img = nib.load(central_file)
        nib.save(img, output_path)
        print(f"✅ Central template saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate central template: {e}")
        return False


def register_single_nifti_file(args):
    """
    Process a single file for registration
    
    Args:
        args: Tuple of (input_file, template, output_dir)
        
    Returns:
        Dict with processing results
    """
    input_file, template, output_dir = args
    
    # Generate output filename by adding .reg before the extension
    basename = os.path.basename(input_file)
    if basename.endswith('.nii.gz'):
        output_name = basename.replace('.nii.gz', '.reg.nii.gz')
    elif basename.endswith('.nii'):
        output_name = basename.replace('.nii', '.reg.nii')
    else:
        output_name = basename + '.reg'
    
    output_file = os.path.join(output_dir, output_name)
    
    result = {
        'input_file': input_file,
        'output_file': output_file,
        'success': False,
        'message': ''
    }
    
    # Check if input file exists
    if not os.path.exists(input_file):
        result['message'] = f"Input file does not exist: {input_file}"
        return result
    
    # Check if output already exists (with atomic check to avoid race conditions)
    import fcntl
    import tempfile
    
    try:
        # Try to create a lock file atomically
        lock_file = output_file + '.lock'
        with open(lock_file, 'x') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            if os.path.exists(output_file):
                result['message'] = f"Output file already exists, skipping: {output_file}"
                result['success'] = True
                os.unlink(lock_file)  # Clean up lock file
                return result
    except (FileExistsError, BlockingIOError):
        # Another process is handling this file or file already exists
        result['message'] = f"File being processed by another worker or already exists: {output_file}"
        result['success'] = True
        return result
    
    try:
        # Perform registration
        perform_nonlinear_registration(
            moving=input_file,
            fixed=template,
            output=output_file,
        )
        
        # Verify output was created
        if os.path.exists(output_file):
            result['success'] = True
            result['message'] = f"Successfully registered: {output_file}"
            # Clean up lock file
            lock_file = output_file + '.lock'
            if os.path.exists(lock_file):
                try:
                    os.unlink(lock_file)
                except OSError:
                    pass  # Lock file might already be cleaned up
        else:
            result['message'] = f"Registration failed - output file not created: {output_file}"
            # Clean up lock file on failure
            lock_file = output_file + '.lock'
            if os.path.exists(lock_file):
                try:
                    os.unlink(lock_file)
                except OSError:
                    pass
            
    except Exception as e:
        result['message'] = f"Registration error: {str(e)}"
        # Clean up lock file on exception
        lock_file = output_file + '.lock'
        if os.path.exists(lock_file):
            try:
                os.unlink(lock_file)
            except OSError:
                pass
    
    return result

def register_nifti_directory(input_dir, template, output_dir, 
                                 file_pattern="*.nii.gz", num_processes=4, template_strategy="average"):
    """
    Process registration for all NIfTI files in a directory
    
    Args:
        input_dir: Directory containing input NIfTI files
        template: Template file for registration (if None, generates based on strategy)
        output_dir: Output directory for registered files
        file_pattern: Pattern to match input files (default: "*.nii.gz")
        num_processes: Number of parallel processes
        template_strategy: Strategy for auto-template generation ("average", "central", "specified")
        
    Returns:
        Dict with processing results
    """
    print(f"Processing registration for files in {input_dir}...")
    
    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory {input_dir} does not exist.")
        return None

    # Auto-generate template if not provided
    if template is None:
        if template_strategy == "specified":
            print("ERROR: Template strategy 'specified' requires --template option to be provided")
            return None
            
        print(f"No template specified, generating {template_strategy} template from input directory...")
        
        # Find all matching NIfTI files for template generation
        template_pattern = os.path.join(input_dir, file_pattern)
        template_candidates = glob.glob(template_pattern)
        template_candidates = [f for f in template_candidates if not f.endswith('.reg.nii.gz')]
        
        if not template_candidates:
            print(f"ERROR: No files found for template generation in {input_dir}")
            return None
        
        # Generate template based on strategy
        template = os.path.join(output_dir, f"auto_generated_template_{template_strategy}.nii.gz")
        os.makedirs(output_dir, exist_ok=True)
        
        if template_strategy == "average":
            success = generate_average_template(template_candidates, template)
        elif template_strategy == "central":
            success = generate_central_template(template_candidates, template)
        else:
            print(f"ERROR: Unsupported template strategy: {template_strategy}")
            return None
            
        if not success:
            print(f"ERROR: Failed to generate {template_strategy} template")
            return None
            
        print(f"Generated {template_strategy} template: {template}")
        
    if not os.path.exists(template):
        print(f"ERROR: Template file {template} does not exist.")
        return None    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all matching NIfTI files
    input_pattern = os.path.join(input_dir, file_pattern)
    input_files = glob.glob(input_pattern)
    
    if not input_files:
        print(f"ERROR: No files found matching pattern: {input_pattern}")
        return None
    
    # Filter out already processed files (those ending with .reg.nii.gz)
    input_files = [f for f in input_files if not f.endswith('.reg.nii.gz')]
    
    print(f"Found {len(input_files)} input files to process")
    print(f"Template: {template}")
    print(f"Using {num_processes} parallel processes")
    
    # Prepare arguments for parallel processing
    process_args = [
        (input_file, template, output_dir)
        for input_file in input_files
    ]
    
    # Process files in parallel
    results = {
        'input_dir': input_dir,
        'template': template,
        'output_dir': output_dir,
        'file_pattern': file_pattern,
        'total_files': len(process_args),
        'successful': 0,
        'skipped': 0,
        'failed': 0,
        'errors': [],
        'file_results': []
    }
    
    with Pool(num_processes) as pool:
        file_results = pool.map(register_single_nifti_file, process_args)
    
    # Analyze results
    for result in file_results:
        results['file_results'].append(result)
        if result['success']:
            if "already exists" in result['message']:
                results['skipped'] += 1
            else:
                results['successful'] += 1
                print(f"✅ {result['message']}")
        else:
            results['failed'] += 1
            results['errors'].append(result['message'])
            print(f"❌ {result['message']}")
    
    # Save metadata
    metadata_file = os.path.join(output_dir, 'registration_metadata.txt')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        f.write("Registration Processing Results\n")
        f.write(f"Input directory: {input_dir}\n")
        f.write(f"Template: {template}\n")
        f.write(f"Output directory: {output_dir}\n")
        f.write(f"File pattern: {file_pattern}\n")
        f.write(f"Total files processed: {results['total_files']}\n")
        f.write(f"Successful registrations: {results['successful']}\n")
        f.write(f"Skipped (already existed): {results['skipped']}\n")
        f.write(f"Failed registrations: {results['failed']}\n")
        f.write(f"Parallel processes used: {num_processes}\n")
        
        if results['errors']:
            f.write("\nErrors encountered:\n")
            for error in results['errors']:
                f.write(f"  - {error}\n")
        
        f.write("\nDetailed Results:\n")
        for result in file_results:
            status = "SUCCESS" if result['success'] else "FAILED"
            filename = os.path.basename(result['input_file'])
            f.write(f"  {filename}: {status} - {result['message']}\n")
    
    print(f"Saved metadata: {metadata_file}")
    return results

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Register NIfTI files to a template')
    parser.add_argument('input_dir', help='Directory containing input NIfTI files')
    parser.add_argument('output_dir', help='Output directory for registered files')
    parser.add_argument('--template', default=None,
                       help='Template NIfTI file for registration (if not specified, auto-generates based on strategy)')
    parser.add_argument('--template-strategy', choices=['average', 'central', 'specified'], default='average',
                       help='Template generation strategy when --template not specified (default: average). Use "specified" with --template option.')
    parser.add_argument('--pattern', default='*.nii.gz', 
                       help='File pattern to match (default: *.nii.gz)')
    parser.add_argument('--processes', type=int, default=4,
                       help='Number of parallel processes (default: 4)')
    
    args = parser.parse_args()
    
    print("=== Generic NIfTI Registration Processing ===")
    print(f"Input directory: {args.input_dir}")
    if args.template:
        print(f"Template file: {args.template}")
    else:
        print(f"Template strategy: {args.template_strategy} (auto-generated)")
    print(f"Output directory: {args.output_dir}")
    print(f"File pattern: {args.pattern}")
    print(f"Parallel processes: {args.processes}")
    
    # Verify template exists (if specified)
    if args.template and not os.path.exists(args.template):
        print(f"ERROR: Template file does not exist: {args.template}")
        return 1
    
    # Verify input directory exists
    if not os.path.exists(args.input_dir):
        print(f"ERROR: Input directory does not exist: {args.input_dir}")
        return 1
    
    # Process registration
    results = register_nifti_directory(
        input_dir=args.input_dir,
        template=args.template,
        output_dir=args.output_dir,
        file_pattern=args.pattern,
        num_processes=args.processes,
        template_strategy=args.template_strategy
    )
    
    if not results:
        print("❌ Registration processing failed")
        return 1
    
    # Print summary
    print(f"\n{'='*60}")
    print("REGISTRATION PROCESSING SUMMARY")
    print('='*60)
    print(f"✅ Successful: {results['successful']}")
    print(f"⏭️  Skipped: {results['skipped']}")  
    print(f"❌ Failed: {results['failed']}")
    print(f"📊 Total: {results['total_files']}")
    
    if results['errors']:
        print(f"\n⚠️  Errors encountered ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"   - {error}")
    
    print(f"\n📁 Output files saved to: {args.output_dir}")
    print(f"📄 Detailed results saved to: {os.path.join(args.output_dir, 'registration_metadata.txt')}")
    
    return 0

def example_usage():
    """Show example usage when run without arguments"""
    print("=== Generic NIfTI Registration Script ===")
    print("\nThis script registers all NIfTI files in a directory to a template.")
    print("It works with any NIfTI files, not just specific TE/b-value formats.")
    print("\nUsage:")
    print("  python nifti_registration_pipeline.py <input_dir> <output_dir> [options]")
    print("\nExamples:")
    print("  # Auto-generate average template (default, recommended):")
    print("  python nifti_registration_pipeline.py \\")
    print("    /path/to/nifti/files \\")
    print("    /path/to/output")
    print("")
    print("  # Use central volume template:")
    print("  python nifti_registration_pipeline.py \\")
    print("    /path/to/nifti/files \\")
    print("    /path/to/output \\")
    print("    --template-strategy central")
    print("")
    print("  # Specify custom template:")
    print("  python nifti_registration_pipeline.py \\")
    print("    /path/to/nifti/files \\")
    print("    /path/to/output \\")
    print("    --template /path/to/template.nii.gz")
    print("\nOptional arguments:")
    print("  --template FILE          Template NIfTI file (overrides template-strategy)")
    print("  --template-strategy STR  Template generation strategy: average (default), central")
    print("  --pattern PATTERN        File pattern to match (default: *.nii.gz)")
    print("  --processes NUM          Number of parallel processes (default: 4)")
    print("\nThe script will:")
    print("  1. Find all NIfTI files matching the pattern")
    print("  2. Generate template using specified strategy (default: average)")
    print("  3. Register each file to the template in parallel")
    print("  4. Save registered files with '.reg' suffix")
    print("  5. Generate a detailed processing report")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        example_usage()
        sys.exit(1)
    
    sys.exit(main())
