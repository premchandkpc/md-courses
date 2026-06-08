---
title: Topic 09: Disaster Recovery & Business Continuity
topic: 08-databases
difficulty: intermediate
time: 60
paths:
  - backend-junior
  - data
  - backend-senior
---

# Topic 09: Disaster Recovery & Business Continuity

mins | **Production Critical:** ⭐⭐⭐⭐⭐

---

## Overview

Disaster recovery = when your database goes down (hardware failure, data corruption, human error, ransomware), can you recover in minutes or hours, not days? Most companies ignore this until catastrophe strikes. This guide covers backup strategies, recovery time objectives (RTO), recovery point objectives (RPO), and implementation across PostgreSQL, MySQL, MongoDB, Redis.

**Why this matters:**
- 60% of companies without backup go out of business after data loss
- Ransomware attacks: every hour of downtime = $5,600 average loss per minute (Gartner)
- Interview question: "Our production database just corrupted. What's your recovery plan?"
- Regulatory: GDPR, HIPAA, PCI-DSS require documented backup procedures

**Key metrics:**
- **RTO (Recovery Time Objective):** Max acceptable downtime (e.g., 1 hour)
- **RPO (Recovery Point Objective):** Max acceptable data loss (e.g., 5 minutes)
- **MTBF (Mean Time Between Failures):** How long until disaster (goal: > 1 year)
- **MTTR (Mean Time To Recover):** How long to restore (goal: < 1 hour)

---

## 1. Backup Strategies

### Strategy 1: Full Backups (Simple, Expensive)

Backup entire database periodically.

```
Day 1: Full backup (100GB) → 30 mins
Day 2: Full backup (100GB) → 30 mins
Day 3: Full backup (100GB) → 30 mins

Problem: Massive storage, slow restore
RTO: Good (1 full backup to restore)
RPO: Bad (1 day old data)
```

**PostgreSQL: Full Backup**
```bash
# Single full backup (slow but simple)
pg_dump -U postgres -d mydb > backup.sql

# Restore (reads every SQL statement, slow)
psql -U postgres -d mydb < backup.sql

# Time: 20-60 mins for 100GB database
```

---

### Strategy 2: Incremental Backups (Fast, Complex)

Backup only changes since last backup.

```
Day 1: Full backup (100GB) → 30 mins
Day 2: Incremental (5GB changes) → 5 mins ✅
Day 3: Incremental (3GB changes) → 3 mins ✅

Benefit: Fast backups
Cost: Complex restore (need full + all incrementals)
RTO: Bad (must restore full + all incrementals in order)
RPO: Good (backed up daily)
```

---

### Strategy 3: Continuous Replication (Best for Most)

Maintain replica database, auto-fail to replica if primary dies.

```
Primary (write operations)
    ↓ WAL (Write-Ahead Logs)
Replica (hot standby)

If primary fails → promote replica to primary (minutes)
```

**PostgreSQL Streaming Replication**
```bash
# Primary config (postgresql.conf)
wal_level = replica
max_wal_senders = 3
hot_standby = on

# Replica connects to primary, streams WAL
primary_conninfo = 'host=primary.example.com port=5432'

# Failover: promote replica to primary
pg_ctl promote -D /var/lib/postgresql/14/main
```

**RTO:** 1-5 minutes (detect failure + promote)
**RPO:** Near-zero (synchronous replication can be 0 data loss)

---

### Strategy 4: Binary Backups (PostgreSQL pg_basebackup)

Copy database files directly (faster than SQL dump).

```bash
# Binary backup (streaming, 3x faster than pg_dump)
pg_basebackup -h primary -U replication_user -D /backup/pgsql -Ft -z -P

# Restore: copy files, start server
cp -r /backup/pgsql/* /var/lib/postgresql/14/main/
pg_ctl start

# Time: 15-30 mins for 100GB
```

---

## 2. Real Production Strategy: Hybrid Backup

Combine strategies for reliability + speed.

```
Tier 1: Continuous Replication (RTO: 5 mins, RPO: <1 min)
├─ 2 PostgreSQL standbys (synchronous replication)
├─ Automatic failover (Patroni/etcd monitors health)
└─ 99.95% uptime target

Tier 2: Daily Binary Backup (RTO: 30 mins, RPO: 24 hours)
├─ Full backup every Sunday (pg_basebackup)
├─ Store in S3 (AWS) with versioning
└─ Test restore every month

Tier 3: Point-in-Time Recovery (PITR)
├─ Archive WAL (Write-Ahead Logs) to S3
├─ Recover to any point in past 7 days
└─ Defense against data corruption
```

**Implementation Timeline:**
```
2am     : Start binary backup (pg_basebackup)
2:15am  : Compress & upload to S3
3am     : Complete, verify checksum
3:30am  : Archive to Glacier (cheaper long-term)
```

---

## 3. Point-in-Time Recovery (PITR)

Restore database to any moment in the past (if you have WAL logs).

**PostgreSQL PITR Setup**
```bash
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /mnt/backup/wal/%f && cp %p /mnt/backup/wal/%f'
archive_timeout = 300

# Create recovery.conf for restore
recovery_target_timeline = 'latest'
recovery_target_time = '2026-05-30 14:32:00 UTC'
```

**Example: Accidental Delete at 2:32 PM**
```sql
-- 2:32 PM: Oops, DELETE FROM users; -- no WHERE clause
-- 2:40 PM: Realized mistake

-- Recovery:
-- 1. Restore from backup to 2:31 PM
-- 2. Replay WAL logs up to 2:31:59.999 PM
-- 3. Data intact, only lost 1 minute of changes

SELECT COUNT(*) FROM users; -- 500M rows ✅
```

---

## 4. Database-Specific DR Strategies

### PostgreSQL: Replication + WAL Archiving

```yaml
Primary:
  Config:
    wal_level: replica
    max_wal_senders: 3
    hot_standby: on
    archive_mode: on
    
Replica:
  Standby mode: true
  Streaming WAL: true
  
Recovery:
  WAL archive: /mnt/wal-archive (AWS S3)
  PITR: Up to 7 days back
  RTO: 5 mins (promote replica)
  RPO: <1 min (sync replication)
```

**Patroni: Automatic Failover**
```bash
# Install Patroni (manages PG + replication)
pip install patroni[postgresql]

# Config: patroni.yml
scope: my-cluster
name: postgres-1
postgresql:
  data_dir: /var/lib/postgresql/14/main
  connect_address: 10.0.0.1:5432
  bin_dir: /usr/lib/postgresql/14/bin

etcd:
  hosts: ['10.0.0.2:2379', '10.0.0.3:2379']

# Run
patroni /etc/patroni.yml

# If primary dies:
# - etcd detects no heartbeat (after 30 secs)
# - Promotes best replica to primary
# - Other replicas follow new primary
# - DNS updated (or use service discovery)
```

---

### MySQL: Replication + Binlog Backup

```bash
# Primary: Enable binlog
[mysqld]
server-id = 1
log_bin = mysql-bin
binlog_format = ROW

# Replica: Connect to primary
CHANGE MASTER TO
  MASTER_HOST='primary.example.com',
  MASTER_USER='replication',
  MASTER_PASSWORD='password',
  MASTER_LOG_FILE='mysql-bin.000001',
  MASTER_LOG_POS=1234;

START SLAVE;

# Backup: Percona XtraBackup (backup hot database)
xtrabackup --backup --target-dir=/backups/mysql-backup

# Restore: Copy files + start server
xtrabackup --prepare --target-dir=/backups/mysql-backup
sudo systemctl start mysql
```

---

### MongoDB: Backup + Replica Sets

```javascript
// Replica set: 3 nodes (Primary + 2 Secondaries)
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017", priority: 2 },
    { _id: 1, host: "mongo2:27017", priority: 1 },
    { _id: 2, host: "mongo3:27017", priority: 0 } // Hidden backup
  ]
});

// Backup: mongodump
mongodump --out=/backups/mongodb-backup

// Restore: mongorestore
mongorestore --dir=/backups/mongodb-backup

// Point-in-time with oplog:
// MongoDB oplog (operations log) enables PITR
mongodump --oplog --out=/backups/with-oplog

// Restore to specific timestamp
mongorestore --oplogReplay --oplogFile=/backups/oplog.bson
```

---

### Redis: RDB Snapshots + AOF

```bash
# Redis: RDB (periodic snapshots)
# In redis.conf
save 900 1      # Snapshot after 900s if 1 key changed
save 300 10     # Snapshot after 300s if 10 keys changed
save 60 10000   # Snapshot after 60s if 10000 keys changed

# RDB backup (synchronous, blocks writes)
BGSAVE          # Background save, doesn't block

# AOF (append-only file): log every write operation
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Restore: Redis loads RDB + replays AOF
# RDB: fast restore, data loss up to snapshot time
# AOF: slow restore, no data loss

# Combined: RDB for speed + AOF for durability
# Restore order: 1) Load RDB, 2) Replay AOF
```

**Hybrid Redis Backup**
```bash
# Backup RDB to external storage
redis-cli BGSAVE
wait until LASTSAVE updates
cp /var/lib/redis/dump.rdb /backups/redis-backup.rdb

# Replicate to secondary Redis instance
# Primary config: slaveof secondary.example.com 6379

# Recovery: If primary fails, promote secondary
redis-cli slaveof NO ONE  # Becomes new primary
```

---

## 5. Backup Verification (Critical!)

**Untested backups are useless.** 90% of companies have backups, 10% can restore them.

### Test Protocol

```bash
# Monthly: Full restore test
1. Restore backup to staging server (same size as prod)
2. Run integrity checks
3. Verify data completeness
4. Check timestamps, sequences
5. Document restore time (update RTO estimate)

# Integrity checks:
PostgreSQL:
  - ANALYZE TABLE users; -- Check structure
  - SELECT COUNT(*) FROM users; -- Row count matches
  - pg_dump -t users | md5sum  -- Compare checksums

MySQL:
  - CHECK TABLE users;
  - SELECT COUNT(*) FROM users;
  - CHECKSUM TABLE users;

MongoDB:
  - db.users.countDocuments() -- Match prod count
  - db.users.validate() -- Check index consistency
  - db.users.stats() -- Storage stats match
```

### Backup Verification Automation

```python
import subprocess
import hashlib
from datetime import datetime

def verify_postgres_backup(backup_file, prod_db):
    """Restore backup, verify contents, report results."""
    
    # 1. Create temp database for restore
    subprocess.run([
        'psql', '-c',
        'DROP DATABASE IF EXISTS test_restore; CREATE DATABASE test_restore;'
    ])
    
    # 2. Restore backup
    start_time = datetime.now()
    subprocess.run(
        f'psql test_restore < {backup_file}',
        shell=True,
        check=True
    )
    restore_time = (datetime.now() - start_time).total_seconds()
    
    # 3. Verify contents
    result = subprocess.run(
        ['psql', '-d', 'test_restore', '-c',
         'SELECT COUNT(*) FROM users;'],
        capture_output=True,
        text=True
    )
    restored_count = int(result.stdout.strip().split('\n')[2])
    
    # 4. Compare with production
    prod_count = get_prod_count('users')
    
    # 5. Report
    status = 'PASS' if restored_count == prod_count else 'FAIL'
    print(f'Backup verification: {status}')
    print(f'  Restore time: {restore_time:.1f}s (RTO target: 300s)')
    print(f'  Rows restored: {restored_count} (prod: {prod_count})')
    
    # 6. Cleanup
    subprocess.run(['psql', '-c', 'DROP DATABASE test_restore;'])
    
    return status == 'PASS'

# Schedule: Run every Sunday at 3am
# Report: Email results + alert if failures
```

---

## 6. Disaster Recovery Plan Template

**Create & maintain for your team:**

```markdown
# Production Database Disaster Recovery Plan

## RTO/RPO Targets
- RTO: 30 minutes (max downtime)
- RPO: 5 minutes (max data loss)
- MTBF: 365+ days
- MTTR: < 30 minutes

## Backup Strategy
1. Continuous replication: Standby replica (RTO: 5 mins)
2. Daily backups: Binary + WAL archive (RTO: 30 mins)
3. PITR: 7-day WAL retention (RPO: any point in past 7 days)

## Failure Scenarios & Recovery

### Scenario 1: Primary Server Hardware Failure
- Detection: 30 seconds (health check fails)
- Action: Promote standby replica to primary
- Communication: Notify team on Slack
- DNS: Update CNAME to new primary (30 sec)
- Recovery time: 2-5 minutes
- Data loss: None (sync replication)

### Scenario 2: Accidental Data Deletion
- Detection: User reports missing data
- Action: Restore from backup to point-in-time
- Verification: Restore to staging, validate
- Communication: Notify users of recovery time
- Recovery time: 30-60 minutes
- Data loss: < 5 minutes

### Scenario 3: Data Corruption / Ransomware
- Detection: Integrity checks fail (monthly test)
- Action: Restore from verified backup pre-attack
- Verification: Full restore test + integrity check
- Communication: Follow incident response plan
- Recovery time: 1-2 hours
- Data loss: Up to last backup (24 hours)

## Roles & Contacts
- Database Lead: Alice (alice@company.com, +1-555-0100)
- On-Call: ops-oncall@company.com
- CTO: Bob (bob@company.com)

## Contact Tree
- If primary fails: Page Database Lead
- If still no recovery after 30 mins: Escalate to CTO
- If data loss > 1 hour: Post incident review mandatory

## Runbooks
- [Promote Replica Failover](./runbooks/promote-replica.md)
- [Restore from Backup](./runbooks/restore-backup.md)
- [PITR Recovery](./runbooks/pitr-recovery.md)
- [Verify Backup](./runbooks/verify-backup.md)

## Training
- Monthly: Disaster recovery drill (1 team member)
- Quarterly: Full team training
- After incident: Post-mortem + lessons learned

## Compliance
- GDPR: Backups encrypted, access logged
- SOC 2: Disaster recovery tested monthly
- Insurance: Policy covers 24-hour backup loss
```

---

## 7. Common Mistakes & Fixes

### Mistake 1: No Offsite Backup

```
❌ BAD: All backups on same server
Primary → Backup (same data center)
If data center burns → all data lost

✅ GOOD: Backups in multiple regions
Primary (us-east-1a)
  ↓ Replica (us-east-1b)
  ↓ Backup (us-west-2) ← Different region
  ↓ Glacier archive (multi-region)
```

---

### Mistake 2: Untested Restore Procedure

```
❌ BAD: "We have backups"
Backup exists but no one ever tested restore
When disaster strikes: Realize backup is corrupt/incomplete

✅ GOOD: Monthly restore test
1. Restore backup to staging (same specs as prod)
2. Run full integrity check
3. Time restoration (document RTO)
4. Document any issues
5. Email results to team

Tool: Automated restore test (above Python example)
```

---

### Mistake 3: Backup Takes Too Long

```
❌ BAD: Full SQL dump (slow)
pg_dump on 500GB database = 2+ hours
If disaster at 2am backup, RPO = 24 hours

✅ GOOD: Binary backup + incremental
Binary backup: 15 mins (3x faster)
Incremental: 5 mins daily
RPO: 24 hours, but restore faster

Or: Continuous replication (RPO: seconds)
```

---

## Interview Prep Questions

1. **"Our production database just crashed. What's your recovery plan?"**
   - Answer: 1) Check if standby replica exists (failover if yes). 2) Estimate RTO/RPO. 3) Restore from backup to staging first. 4) Verify integrity. 5) Promote to production.

2. **"What's the difference between RTO and RPO?"**
   - Answer: RTO = how long until we're back online. RPO = how much data we lose. We might accept 1-hour downtime (RTO) but need <5-minute data loss (RPO).

3. **"How would you achieve zero-loss recovery?"**
   - Answer: Synchronous replication (primary waits for replica to acknowledge before committing). Slower writes, but no data loss on failover.

4. **"What would you backup: database or just code?"**
   - Answer: Database (data is irreplaceable). Code is in git. But also backup configuration, secrets, SSL certs, DNS records.

5. **"How do you verify a backup works?"**
   - Answer: Restore to staging monthly, run full integrity checks, time the restore to validate RTO.

---

## Checklist: Production-Ready DR

- [ ] Backup strategy documented (full vs incremental vs replication)
- [ ] RTO/RPO targets defined
- [ ] Replication configured (standby/replica instance running)
- [ ] Backups automated (cron job or service)
- [ ] Backup storage offsite (AWS S3, GCS, Backblaze)
- [ ] WAL archiving enabled (PITR support)
- [ ] Restore procedure documented
- [ ] Monthly restore test scheduled (staging)
- [ ] Monitoring + alerting (backup failures, replication lag)
- [ ] Team trained on failover (annual drill)
- [ ] Incident response plan (escalation path)
- [ ] Compliance requirements met (encryption, access logs)

---

## See Also

### Phase 7.1 Related Topics

- [Database Replication](./10-database-replication.md) — Replication as core DR strategy
- [Database Sharding](./11-database-sharding.md) — Backup considerations with shards
- [Connection Pooling](./08-connection-pooling.md) — Pool behavior during failover

### Additional Resources

- Patroni: Automatic PostgreSQL failover
- Percona XtraBackup: MySQL/MariaDB backups
- MongoDB Community Backup: Ops Manager
- Redis Sentinel: Automatic failover
- AWS RDS Automated Backups: Managed solution
- Velero: Kubernetes persistent data backup
