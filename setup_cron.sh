#!/bin/bash

# Setup cron job for Open Interest Monitor
echo "Setting up cron job for Open Interest Monitor..."

# Get the current directory
CURRENT_DIR=$(pwd)

# Create the cron job entry (runs every 15 minutes)
CRON_JOB="*/15 * * * * cd $CURRENT_DIR && python3 monitor.py --config tokens_config.json >> monitor_cron.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job added successfully!"
echo "📅 Monitor will run every 15 minutes"
echo "📝 Logs will be saved to monitor_cron.log"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To remove cron job: crontab -r"
echo "To edit cron jobs: crontab -e" 