#!/usr/bin/env bash
# ==============================================================================
# ShopZone Day 25 Capstone - Linux PostgreSQL Restoration Shell Script
# Restores compressed database backup with checksum verification.
# ==============================================================================

set -euo pipefail

BACKUP_FILE="${1:-}"

if [[ -z "${BACKUP_FILE}" ]]; then
    # Pick the latest backup file in /backups
    BACKUP_FILE=$(find /backups -maxdepth 1 -name "shopzone_backup_*.sql.gz" | sort | tail -n 1)
fi

if [[ -z "${BACKUP_FILE}" || ! -f "${BACKUP_FILE}" ]]; then
    echo "[ERROR] No valid backup archive found at '${BACKUP_FILE}'."
    exit 1
fi

CHECKSUM_FILE="${BACKUP_FILE}.sha256"

echo "======================================================================"
echo "          SHOPZONE POSTGRESQL RESTORATION & DISASTER RECOVERY         "
echo "======================================================================"
echo "Backup File:  ${BACKUP_FILE}"
echo "Database:     ${POSTGRES_DB:-shopzone_production}"
echo "Host:         ${PGHOST:-postgres}:${PGPORT:-5432}"

# 1. Verify Checksum
if [[ -f "${CHECKSUM_FILE}" ]]; then
    echo "[INFO] Verifying SHA-256 cryptographic checksum..."
    sha256sum -c "${CHECKSUM_FILE}"
    echo "[PASS] Checksum verified. Backup is untampered."
else
    echo "[WARN] Checksum file not found. Proceeding with caution..."
fi

# 2. Execute Restoration
echo "[INFO] Restoring database schema and data..."
PGPASSWORD="${POSTGRES_PASSWORD:-}" gunzip -c "${BACKUP_FILE}" | psql \
    -h "${PGHOST:-postgres}" \
    -p "${PGPORT:-5432}" \
    -U "${POSTGRES_USER:-shopzone_admin}" \
    -d "${POSTGRES_DB:-shopzone_production}"

echo ">>> DATABASE RESTORATION COMPLETED SUCCESSFULLY <<<"
