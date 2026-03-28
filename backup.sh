#!/bin/bash

# ── CONFIG ─────────────────────────────────────────
BUCKET="homelab-backups"
REGION="af-johannesburg-1"
NAMESPACE="axhdsgiyeysl"
COMPARTMENT_ID=$(grep tenancy ~/.oci/config | cut -d= -f2)
BACKUP_DIR="/tmp/homelab-backup"
DATE=$(date +%Y-%m-%d_%H-%M)
LOG_FILE="/var/log/homelab-backup.log"
OCI="/home/squar3/.local/bin/oci"
# ───────────────────────────────────────────────────

echo "[$DATE] Starting backup..." | tee -a $LOG_FILE

# Create temp backup directory
mkdir -p $BACKUP_DIR

# ── 1. Backup PostgreSQL ───────────────────────────
echo "[$DATE] Backing up PostgreSQL..." | tee -a $LOG_FILE
docker exec homelab-postgres-1 pg_dump -U nextcloud nextcloud \
    > $BACKUP_DIR/postgres_$DATE.sql
gzip $BACKUP_DIR/postgres_$DATE.sql

# ── 2. Backup Vaultwarden ─────────────────────────
echo "[$DATE] Backing up Vaultwarden..." | tee -a $LOG_FILE
docker run --rm \
    --volumes-from homelab-vaultwarden-1 \
    -v $BACKUP_DIR:/backup \
    alpine tar czf /backup/vaultwarden_$DATE.tar.gz /data

# ── 3. Backup Nextcloud config ────────────────────
echo "[$DATE] Backing up Nextcloud config..." | tee -a $LOG_FILE
docker run --rm \
    --volumes-from homelab-nextcloud-1 \
    -v $BACKUP_DIR:/backup \
    alpine tar czf /backup/nextcloud_config_$DATE.tar.gz \
    /var/www/html/config

# ── 4. Backup Docker Compose configs ──────────────
echo "[$DATE] Backing up configs..." | tee -a $LOG_FILE
tar czf $BACKUP_DIR/homelab_configs_$DATE.tar.gz \
    /home/squar3/homelab/docker-compose.yml \
    /home/squar3/homelab/monitoring \
    /home/squar3/homelab/myapi \
    /home/squar3/homelab/.gitignore

# ── 5. Upload to Oracle Object Storage ────────────
echo "[$DATE] Uploading to Oracle Cloud..." | tee -a $LOG_FILE
for FILE in $BACKUP_DIR/*; do
    FILENAME=$(basename $FILE)
   	$OCI os object put \
        	--bucket-name $BUCKET \
        	--file $FILE \
        	--name "backups/$DATE/$FILENAME" \
        	--region $REGION \
		--namespace $NAMESPACE \
        	--force
    echo "[$DATE] Uploaded: $FILENAME" | tee -a $LOG_FILE
done

# ── 6. Cleanup old backups (keep last 7 days) ─────
echo "[$DATE] Cleaning old backups..." | tee -a $LOG_FILE
$OCI os object list \
    --bucket-name $BUCKET \
    --region $REGION \
    --namespace $NAMESPACE \
    --output json 2>/dev/null | \
python3 -c "
import sys, json
from datetime import datetime, timedelta
try:
    data = json.load(sys.stdin)
    items = data.get('data', [])
    cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    old = [i['name'] for i in items if i.get('name','').split('/')[-2] < cutoff]
    for i in old:
        print(i)
except:
    pass
" | while read obj; do
    $OCI os object delete \
        --bucket-name $BUCKET \
        --object-name "$obj" \
        --region $REGION \
        --force 2>/dev/null
done

# ── 7. Cleanup temp files ─────────────────────────
rm -rf $BACKUP_DIR
echo "[$DATE] Backup complete!" | tee -a $LOG_FILE
