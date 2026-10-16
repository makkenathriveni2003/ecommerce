#!/usr/bin/env bash
# ==============================================================================
# ShopZone Day 25 Capstone - Linux PostgreSQL Backup Shell Script
# Runs via cron or manual execution inside container / AWS EC2 host.
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/shopzone_backup_${TIMESTAMP}.sql.gz"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

mkdir -p "${BACKUP_DIR}"

echo "======================================================================"
echo "          SHOPZONE POSTGRESQL PRODUCTION BACKUP (LINUX/DOCKER)        "
echo "======================================================================"
echo "Timestamp:    ${TIMESTAMP} UTC"
echo "Database:     ${POSTGRES_DB:-shopzone_production}"
echo "Destination:  ${BACKUP_FILE}"
echo "Retention:    ${RETENTION_DAYS} days"

# Execute pg_dump and pipe through gzip
PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dump \
    -h "${PGHOST:-postgres}" \
    -p "${PGPORT:-5432}" \
    -U "${POSTGRES_USER:-shopzone_admin}" \
    -d "${POSTGRES_DB:-shopzone_production}" \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists | gzip -9 > "${BACKUP_FILE}"

echo "[PASS] Database backup archive created successfully."

# Compute SHA256 checksum
sha256sum "${BACKUP_FILE}" > "${CHECKSUM_FILE}"
echo "[PASS] SHA-256 Checksum generated: $(cat "${CHECKSUM_FILE}")"

# Prune backups older than retention days
find "${BACKUP_DIR}" -type f -name "shopzone_backup_*.sql.gz*" -mtime +"${RETENTION_DAYS}" -exec rm -f {} \;
echo "[PASS] Pruned backups older than ${RETENTION_DAYS} days."

echo ">>> BACKUP COMPLETED SUCCESSFULLY <<<"
