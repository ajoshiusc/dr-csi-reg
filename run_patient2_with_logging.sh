#!/bin/bash
# Patient2 Registration with Comprehensive Logging

set -e  # Exit on any error

# Setup logging
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/patient2_registration_$TIMESTAMP.log"
TIMING_FILE="$LOG_DIR/patient2_timings_$TIMESTAMP.log"

echo "🚀 Starting Patient2 Registration with Logging" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"
echo "Start Time: $(date)" | tee -a "$LOG_FILE"
echo "Input File: data/data_wip_patient2.mat" | tee -a "$LOG_FILE"
echo "Output Directory: patient2_output/" | tee -a "$LOG_FILE"
echo "Log File: $LOG_FILE" | tee -a "$LOG_FILE"
echo "Timing File: $TIMING_FILE" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"

# System info
echo -e "\n📊 System Information:" | tee -a "$LOG_FILE"
echo "Python Version: $(python3 --version)" | tee -a "$LOG_FILE"
echo "CUDA Available: $(python3 -c 'import torch; print(torch.cuda.is_available())')" | tee -a "$LOG_FILE"
echo "GPU: $(python3 -c 'import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU")')" | tee -a "$LOG_FILE"
echo "Working Directory: $(pwd)" | tee -a "$LOG_FILE"

# Check input file
echo -e "\n📁 Input File Check:" | tee -a "$LOG_FILE"
if [ -f "data/data_wip_patient2.mat" ]; then
    echo "✅ Input file exists" | tee -a "$LOG_FILE"
    ls -lh data/data_wip_patient2.mat | tee -a "$LOG_FILE"
else
    echo "❌ Input file not found!" | tee -a "$LOG_FILE"
    exit 1
fi

# Start timing
OVERALL_START=$(date +%s)
echo -e "\n⏱️ Starting Registration Process..." | tee -a "$LOG_FILE"
echo "Overall Start: $(date)" | tee -a "$TIMING_FILE"

# Run registration with full logging
echo -e "\n🔄 Running Registration Module..." | tee -a "$LOG_FILE"
echo "Using 4 parallel processes for faster registration" | tee -a "$LOG_FILE"
python3 run_registration_module.py \
    data/data_wip_patient2.mat \
    patient2_output \
    --processes 4 2>&1 | tee -a "$LOG_FILE"

# End timing
OVERALL_END=$(date +%s)
OVERALL_DURATION=$((OVERALL_END - OVERALL_START))

echo "Overall End: $(date)" | tee -a "$TIMING_FILE"
echo "Overall Duration: ${OVERALL_DURATION} seconds" | tee -a "$TIMING_FILE"

echo -e "\n📈 Registration Summary:" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"
echo "End Time: $(date)" | tee -a "$LOG_FILE"
echo "Total Duration: ${OVERALL_DURATION} seconds ($(($OVERALL_DURATION / 60)) minutes)" | tee -a "$LOG_FILE"

# Check outputs
echo -e "\n📋 Output Summary:" | tee -a "$LOG_FILE"
if [ -d "patient2_output" ]; then
    echo "✅ Output directory created" | tee -a "$LOG_FILE"
    
    if [ -d "patient2_output/nifti" ]; then
        NIFTI_COUNT=$(find patient2_output/nifti -name "*.nii.gz" | wc -l)
        echo "📊 NIfTI files generated: $NIFTI_COUNT" | tee -a "$LOG_FILE"
    fi
    
    if [ -d "patient2_output/registration" ]; then
        REG_COUNT=$(find patient2_output/registration -name "*.reg.nii.gz" | wc -l)
        echo "📊 Registered files: $REG_COUNT" | tee -a "$LOG_FILE"
    fi
    
    if [ -f "patient2_output/final_reconstructed.mat" ]; then
        echo "✅ Final reconstructed MAT file created" | tee -a "$LOG_FILE"
        ls -lh patient2_output/final_reconstructed.mat | tee -a "$LOG_FILE"
    fi
else
    echo "❌ Output directory not found!" | tee -a "$LOG_FILE"
fi

echo "=================================================" | tee -a "$LOG_FILE"
echo "🎉 Patient2 Registration Complete!" | tee -a "$LOG_FILE"
echo "📄 Full log saved to: $LOG_FILE"
echo "⏱️ Timing log saved to: $TIMING_FILE"