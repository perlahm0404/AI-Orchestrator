#!/bin/bash
# Process all Gmail emails in batches of 500 until all are classified

set -e  # Exit on error

cd /Users/tmac/1_REPOS/AI_Orchestrator
source .venv/bin/activate

# Setup CSV log file with timestamp
timestamp=$(date +%Y%m%d_%H%M%S)
csv_file="email_classification_log_${timestamp}.csv"

echo "========================================================================"
echo "📧 Gmail Bulk Classification - Processing ALL Emails"
echo "========================================================================"
echo ""
echo "Configuration:"
echo "  • Batch size: 500 emails"
echo "  • Rest period: 5 minutes between batches (to avoid throttling)"
echo "  • CSV log: $csv_file"
echo ""
echo "Press Ctrl+C at any time to stop (progress is saved after each batch)."
echo ""

batch_num=1
total_processed=0
emails_in_batch_group=0

while true; do
    echo ""
    echo "========================================================================"
    echo "🔄 BATCH #$batch_num - Processing 500 emails..."
    echo "   Started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================================================"
    echo ""

    # Run classification in auto mode with CSV logging
    aibrain email classify --batch 500 --auto --csv "$csv_file"

    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Classification failed. Stopping."
        echo "📝 Partial results saved in: $csv_file"
        exit 1
    fi

    total_processed=$((total_processed + 500))
    emails_in_batch_group=$((emails_in_batch_group + 500))

    echo ""
    echo "✅ Batch #$batch_num complete!"
    echo "   Completed: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "📊 Progress Summary:"
    echo "   • This batch: 500 emails"
    echo "   • Total processed: $total_processed emails"
    echo "   • Emails since last rest: $emails_in_batch_group"
    echo ""

    # Check status
    echo "Checking for remaining unlabeled emails..."
    status_output=$(aibrain email status 2>&1)
    echo ""
    echo "$status_output"

    # Check if there are still unlabeled emails
    if echo "$status_output" | grep -q "Found unlabeled emails"; then
        echo ""
        echo "⚠️  More unlabeled emails found. Continuing..."

        # Rest for 5 minutes every 500 emails to avoid throttling
        if [ $emails_in_batch_group -ge 500 ]; then
            echo ""
            echo "========================================================================"
            echo "⏸️  RESTING FOR 5 MINUTES (API throttle prevention)"
            echo "========================================================================"
            echo "   • Processed $emails_in_batch_group emails in this group"
            echo "   • Total processed so far: $total_processed emails"
            echo "   • Rest started: $(date '+%Y-%m-%d %H:%M:%S')"
            echo ""
            echo "Countdown:"

            # Countdown timer
            for i in {300..1}; do
                mins=$((i / 60))
                secs=$((i % 60))
                printf "\r   ⏱️  Time remaining: %02d:%02d" $mins $secs
                sleep 1
            done

            echo ""
            echo ""
            echo "✅ Rest complete. Resuming..."
            echo "   • Resumed: $(date '+%Y-%m-%d %H:%M:%S')"

            emails_in_batch_group=0  # Reset counter
        else
            sleep 3  # Brief pause between batches
        fi

        batch_num=$((batch_num + 1))
    else
        echo ""
        echo "========================================================================"
        echo "🎉 ALL EMAILS CLASSIFIED!"
        echo "========================================================================"
        echo ""
        echo "Final statistics:"
        echo "$status_output"
        break
    fi
done

echo ""
echo "========================================================================"
echo "✅ BULK CLASSIFICATION COMPLETE!"
echo "========================================================================"
echo ""
echo "Summary:"
echo "  • Total emails processed: $total_processed"
echo "  • Total batches: $batch_num"
echo "  • CSV log: $csv_file"
echo "  • Completed: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "You can view the detailed log with:"
echo "  open $csv_file"
echo ""
