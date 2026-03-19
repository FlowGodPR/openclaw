#!/bin/bash
# QUINN Autonomous Core Daemon
# ============================
# Runs as cron job or background daemon for true autonomy.
# 
# Installation:
#   crontab -e
#   */15 * * * * /Volumes/QUINN/context/quinn_s3a/autonomy_daemon.sh >> /Volumes/QUINN/context/quinn_s3a/daemon.log 2>&1
#
# Or run as background:
#   nohup bash /Volumes/QUINN/context/quinn_s3a/autonomy_daemon.sh &

QUINN_USB="/Volumes/QUINN"
CORE_SCRIPT="$QUINN_USB/context/quinn_s3a/autonomous_core.py"
LOG_FILE="$QUINN_USB/context/quinn_s3a/daemon.log"
PID_FILE="$QUINN_USB/context/quinn_s3a/daemon.pid"

# Check if USB is mounted
if [ ! -d "$QUINN_USB" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] QUINN USB not mounted - skipping autonomy cycle" >> "$LOG_FILE"
    exit 0
fi

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] python3 not found - skipping" >> "$LOG_FILE"
    exit 0
fi

# Run autonomous cycle
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting autonomy cycle..." >> "$LOG_FILE"
cd "$QUINN_USB/context/quinn_s3a" && python3 autonomous_core.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cycle complete (exit: $EXIT_CODE)" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"

exit $EXIT_CODE
