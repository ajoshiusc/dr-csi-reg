#!/bin/bash

# Monitor DR-CSI Workflow Progress
echo "DR-CSI Workflow Monitor"
echo "======================"
echo ""

# Check if tmux session exists
if ! tmux has-session -t dr-csi-workflow 2>/dev/null; then
    echo "❌ Tmux session 'dr-csi-workflow' is not running"
    exit 1
fi

echo "✅ Tmux session 'dr-csi-workflow' is active"
echo ""

# Check workflow log if it exists
if [ -f "workflow_log.txt" ]; then
    echo "📊 Latest workflow progress:"
    echo "----------------------------"
    tail -10 workflow_log.txt
    echo ""
    
    # Check for completion indicators
    if grep -q "Workflow completed successfully" workflow_log.txt; then
        echo "🎉 WORKFLOW COMPLETED SUCCESSFULLY!"
    elif grep -q "Starting registration" workflow_log.txt; then
        echo "🔄 Registration phase in progress..."
        echo "⏱️  This typically takes 3-4 hours with GPU"
    elif grep -q "Successfully converted .mat to NIfTI" workflow_log.txt; then
        echo "✅ MAT to NIfTI conversion completed"
        echo "🔄 Registration phase starting..."
    else
        echo "🔄 Workflow is still initializing..."
    fi
else
    echo "📋 Workflow log not yet created, checking tmux session..."
fi

echo ""
echo "Commands to monitor:"
echo "- View live tmux session: tmux attach-session -t dr-csi-workflow"
echo "- Monitor log file: tail -f workflow_log.txt"
echo "- Check this status: ./monitor_workflow.sh"
