#!/bin/bash
# clean_logs.sh - Pragmatic log cleanup script

DAYS=${1:-7}
TARGET_PATH=${2:-"./logs"}

if [ ! -d "$TARGET_PATH" ]; then
    echo "Error: Directory $TARGET_PATH does not exist."
    exit 1
fi

echo "Cleaning logs in $TARGET_PATH older than $DAYS days..."
find "$TARGET_PATH" -type f -name "*.log" -mtime +$DAYS -print -delete

echo "Cleanup complete."
