#!/bin/bash
APP_DIR="/home/mike--muteithia/IST1025/A3_SACCO"
DB_FILE=$(find $APP_DIR/sacco_management -name "akiba_sacco.db" | head -n 1)

if [ -z "$DB_FILE" ]; then
    echo "Error: Database file not found."
    exit 1
fi

DEST="${APP_DIR}/backups/akiba_sacco_backup_$(date +%Y%m%d_%H%M%S).db"
cp "$DB_FILE" "$DEST"
gzip "$DEST"
find "${APP_DIR}/backups" -type f -name "*.gz" -mtime +30 -exec rm {} \;
echo "Backup successfully generated: ${DEST}.gz"
