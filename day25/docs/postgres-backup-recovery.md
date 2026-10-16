# Day 25 Capstone – PostgreSQL Automated Backup & Disaster Recovery Runbook

## 1. Disaster Recovery Objectives (RTO & RPO)

To ensure business continuity for the ShopZone e-commerce platform, our backup and disaster recovery architecture is designed around two core service-level agreements:

- **Recovery Point Objective (RPO) < 24 Hours** (Automated daily snapshots) or **< 5 Minutes** when Write-Ahead Logging (WAL) archiving is active.
- **Recovery Time Objective (RTO) < 15 Minutes**: Full system restoration and database table verification within 15 minutes of an outage.

```
[ PostgreSQL 16 DB ]
         │
         ▼ (Automated Daily Cron at 02:00 UTC)
[ pg_dump --clean --if-exists ]
         │
         ▼ (gzip -9 Compression)
[ shopzone_backup_YYYYMMDD_HHMMSS.sql.gz ]
         │
         ├─► [ sha256sum ] ──────────────► [ *.sha256 Checksum File ]
         ├─► [ Retention Pruning ] ──────► [ Purges backups > 7 days ]
         └─► [ Off-site Replication ] ───► [ AWS S3 Encrypted Bucket ]
```

---

## 2. Automated Backup Implementation

The automated backup workflow is implemented in `day25/scripts/backup_postgres.py` (cross-platform Python) and `day25/scripts/backup_postgres.sh` (Linux container shell script).

### Key Features:
1. **Atomic Snapshots with `pg_dump`**:
   - Uses `--clean --if-exists` to drop existing tables during restore before recreating them, preventing primary key collisions.
   - Uses `--no-owner --no-acl` to ensure the backup can be restored across different database users or cloud environments.
2. **High-Ratio GZip Compression**:
   - Compresses plain SQL by **80%–88%**, minimizing storage footprint and network transfer bandwidth.
3. **Cryptographic Integrity Verification (SHA-256)**:
   - Immediately generates a companion `.sha256` checksum file.
   - Any silent bit-rot on storage drives or malicious tampering is caught before restoration begins.
4. **Automated 7-Day Retention Pruning**:
   - Scans the backup directory on every run and removes backups older than `RETENTION_DAYS=7` to prevent disk bloat.

---

## 3. Step-by-Step Restoration Procedure

Restoration is managed via `day25/scripts/restore_postgres.py` and `day25/scripts/restore_postgres.sh`:

```bash
# Syntax: ./restore_postgres.sh [path_to_backup_archive]
bash day25/scripts/restore_postgres.sh /backups/shopzone_backup_20261016_020000.sql.gz
```

### Execution Flow:
1. **Integrity Validation**: Verifies the archive matches its `.sha256` hash:
   ```bash
   sha256sum -c shopzone_backup_20261016_020000.sql.gz.sha256
   ```
2. **Decompression & Streaming Restore**:
   ```bash
   gunzip -c shopzone_backup_20261016_020000.sql.gz | psql -h postgres -U shopzone_admin -d shopzone_production
   ```
3. **Post-Restoration Smoke Tests**:
   - Executes validation queries checking record counts in `users`, `products`, and `orders`.

---

## 4. Off-Site Cloud Backup to AWS S3

For disaster recovery in the event of an entire data center or EC2 instance loss, backups are replicated off-site to a private Amazon S3 bucket with server-side encryption (SSE-S3 or KMS):

```bash
# Sync local backups directory to encrypted AWS S3 bucket
aws s3 sync /backups s3://shopzone-production-backups-ap-south-1/postgres/ \
    --sse AES256 \
    --storage-class STANDARD_IA
```

---

## 5. Automated Disaster Recovery Drill

The backup and restoration workflow is validated automatically in our CI/CD pipeline via `day25/scripts/test_backup_recovery.py`:

```powershell
python day25/scripts/test_backup_recovery.py
```

Expected Output:
```
========================================================================
      EXECUTING CAPSTONE DATABASE BACKUP & RESTORATION DRILL
========================================================================
--- STEP 1: GENERATING COMPRESSED BACKUP ---
[DRILL PASS] Backup generated: shopzone_backup_20261016_113000.sql.gz
--- STEP 2: VERIFYING SHA-256 CHECKSUM ---
[DRILL PASS] Cryptographic integrity confirmed: e3b0c44298fc1c149afbf4...
--- STEP 3: EXECUTING DATABASE RESTORATION DRILL ---
[DRILL PASS] Restoration executed without corruption.
--- STEP 4: TESTING RETENTION PRUNING LOGIC ---
[DRILL PASS] Retention pruning logic validated.
>>> DISASTER RECOVERY DRILL PASSED: 100% RELIABILITY ACHIEVED <<<
```
