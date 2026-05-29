# MySQL Replication & High Availability

## Master-Slave Replication

One master writes, multiple slaves read.

### Setup

```sql
-- Master configuration (my.cnf)
[mysqld]
server-id = 1
log_bin = mysql-bin
binlog_format = ROW

-- Create replication user
CREATE USER 'replicator'@'slave-ip' IDENTIFIED BY 'password';
GRANT REPLICATION SLAVE ON *.* TO 'replicator'@'slave-ip';

-- Show master status (note File and Position)
SHOW MASTER STATUS;
```

```sql
-- Slave configuration (my.cnf)
[mysqld]
server-id = 2
relay_log = mysql-relay-bin
relay_log_index = mysql-relay-bin.index

-- Start replication
CHANGE MASTER TO
  MASTER_HOST='master-ip',
  MASTER_USER='replicator',
  MASTER_PASSWORD='password',
  MASTER_LOG_FILE='mysql-bin.000001',
  MASTER_LOG_POS=1234;

START SLAVE;
SHOW SLAVE STATUS;
```

### Monitoring

```sql
-- Master perspective
SHOW MASTER STATUS;
SHOW BINARY LOGS;
SHOW BINLOG EVENTS;

-- Slave perspective
SHOW SLAVE STATUS;
-- Check: Seconds_Behind_Master (lag)
-- Check: Slave_IO_Running, Slave_SQL_Running (both YES)
```

### Common Issues

**Slave Falls Behind**
```sql
-- Slave slower than master
-- Solution 1: Hardware upgrade
-- Solution 2: Parallel replication
[mysqld]
slave_parallel_workers = 4
slave_parallel_type = LOGICAL_CLOCK
```

**Replication Lag**
```sql
-- Check lag
SHOW SLAVE STATUS\G
-- Seconds_Behind_Master shows seconds of lag

-- Reduce: Faster slave hardware, fewer writes, batch updates
```

**Slave out of sync**
```sql
-- Data diverged from master

-- Check with pt-table-checksum
pt-table-checksum --host=master

-- Fix: Re-snapshot slave from master
-- Or: Skip error
SET GLOBAL SQL_SLAVE_SKIP_COUNTER = 1;
START SLAVE;
```

---

## Master-Master Replication

Both servers write and replicate to each other.

```sql
-- Server A
[mysqld]
server-id = 1
log_bin = mysql-bin
auto_increment_increment = 2
auto_increment_offset = 1

-- Server B
[mysqld]
server-id = 2
log_bin = mysql-bin
auto_increment_increment = 2
auto_increment_offset = 2

-- Both replicate from each other
-- auto_increment: A uses 1,3,5... B uses 2,4,6...
-- Prevents PK conflicts
```

**Advantages:**
- Both read & write capable
- Automatic failover
- Load balancing

**Disadvantages:**
- Conflict resolution needed
- More complex
- Latency issues

**Conflict Handling:**
```sql
-- Last write wins
-- Application logic to merge
-- Conflict tables (track changes)
```

---

## Group Replication (High Availability)

Multi-master with automatic failover.

```sql
-- All servers can write
-- Automatic quorum-based consensus
-- Automatic failover

-- Setup
INSTALL PLUGIN group_replication SONAME 'group_replication.so';

SET GLOBAL group_replication_bootstrap_group_whitelist = "server1,server2,server3";
SET GLOBAL group_replication_group_seeds = "server1:33061,server2:33061,server3:33061";
SET GLOBAL group_replication_local_address = "server1:33061";
SET GLOBAL group_replication_single_primary_mode = ON;

START GROUP_REPLICATION;
```

---

## Failover Strategies

### Manual Failover

```bash
# 1. Identify slowest slave (least lag)
mysql -h slave1 -e "SHOW SLAVE STATUS\G" | grep Seconds_Behind_Master

# 2. Wait for slave to catch up
mysql -h slave1 -e "SELECT MASTER_LOG_FILE, READ_MASTER_LOG_POS FROM performance_schema.replication_connection_status;"

# 3. Promote slave to master
mysql -h slave1 -e "STOP SLAVE; RESET MASTER;"

# 4. Update application connection string
# Point to slave1 (now master)

# 5. Reconfigure old master as slave
mysql -h old-master -e "CHANGE MASTER TO MASTER_HOST='slave1', ..."
```

### Automatic Failover (MHA - MySQL HA)

```bash
# Install MHA Manager
yum install mha4mysql-manager

# Configure MHA
cat > /etc/mha/app.conf << EOF
[server default]
manager_workdir=/var/log/mha
manager_log=/var/log/mha/manager.log
master_binlog_dir=/var/lib/mysql
ssh_user=root

[server1]
hostname=master
candidate_master=1

[server2]
hostname=slave1
candidate_master=1

[server3]
hostname=slave2
EOF

# Start monitoring
nohup masterha_manager --conf=/etc/mha/app.conf --remove_dead_master_conf --ignore_last_failover < /dev/null > /var/log/mha/manager.log 2>&1 &
```

---

## Read Replicas for Scaling

Distribute reads across multiple servers.

```
Master (Writes)
   ↓
   └→ Slave 1 (Read: Analytics)
   ├→ Slave 2 (Read: API)
   └→ Slave 3 (Read: Reports)
```

### Application Level

```python
# Connection strategy
class Database:
    def __init__(self):
        self.master = MySQLConnection('master-ip')
        self.slaves = [
            MySQLConnection('slave1-ip'),
            MySQLConnection('slave2-ip'),
            MySQLConnection('slave3-ip')
        ]
    
    def write(self, sql, params):
        # Always use master
        return self.master.execute(sql, params)
    
    def read(self, sql, params):
        # Round-robin slaves
        slave = random.choice(self.slaves)
        return slave.execute(sql, params)

db = Database()
db.write("INSERT INTO users ...", data)  # Master
users = db.read("SELECT * FROM users", [])  # Slave
```

### Replication Lag Handling

```python
def read_with_fallback(sql, params):
    try:
        # Try slave first
        slave = random.choice(slaves)
        if slave.replication_lag < 5:  # Less than 5 seconds
            return slave.execute(sql, params)
    except:
        pass
    
    # Fall back to master if slave too slow
    return master.execute(sql, params)
```

---

## Backup & Recovery

### Binary Logs

```bash
# Enable binary logging (already set for replication)
# Files: mysql-bin.000001, mysql-bin.000002, etc.

# View binlog
mysqlbinlog mysql-bin.000001 | head -50

# Backup binlogs
cp /var/lib/mysql/mysql-bin.* /backup/
```

### Full Backup

```bash
# Using mysqldump
mysqldump --all-databases --master-data > full_backup.sql

# Or backup files directly
cp -r /var/lib/mysql /backup/mysql-$(date +%Y%m%d)
```

### Point-in-Time Recovery

```bash
# Binlog contains all changes with timestamps
# Restore to specific time
mysqlbinlog --start-date="2026-05-29 10:00:00" \
            --stop-date="2026-05-29 12:00:00" \
            mysql-bin.* | mysql

# Or by position
mysqlbinlog --start-position=100 \
            --stop-position=500 \
            mysql-bin.000001 | mysql
```

---

## Real-World Architecture

### Standard Setup (2-tier)

```
Load Balancer
   ↓
Master (writes)
   ↓
Slaves (reads)
```

```
Application
   ├→ Write operations → Master
   └→ Read operations → Slave pool (round-robin)
```

### Enterprise Setup (3-tier)

```
Load Balancer (HAProxy)
   ├→ Master (Writes)
   ├→ Replica 1 (Reads)
   ├→ Replica 2 (Reads)
   └→ Replica 3 (Reads)

Monitoring (Nagios, Prometheus)
Backup (daily, offsite)
Binlog archival (years)
```

---

## Monitoring & Alerts

### Key Metrics

```sql
-- Replication lag
SELECT TIMESTAMPDIFF(SECOND, ts, NOW()) as lag_seconds
FROM replication_heartbeat;

-- Binary log size
SELECT FILE_SIZE FROM INFORMATION_SCHEMA.FILES
WHERE FILE_TYPE = 'DATAFILE' AND FILE_NAME LIKE '%mysql-bin%';

-- Slave status
SHOW SLAVE STATUS\G
-- Monitor: Seconds_Behind_Master, Slave_IO_Running, Slave_SQL_Running
```

### Prometheus Alerts

```yaml
- alert: MysqlReplicationLag
  expr: mysql_global_status_replication_lag_seconds > 60
  for: 5m
  annotations:
    summary: "MySQL slave lagging by {{ $value }} seconds"

- alert: MysqlSlaveDown
  expr: mysql_slave_status_slave_io_running == 0
  for: 1m
  annotations:
    summary: "MySQL slave IO thread down"
```

---

## Disaster Recovery Plan

| Scenario | Solution | RTO | RPO |
|----------|----------|-----|-----|
| Slave fails | Promote another slave | 5 min | 0 |
| Master fails | Failover to slave | 10 min | 1 sec |
| Data corruption | PITR from binlog | 30 min | 1 sec |
| Site failure | Restore backup | 1 hour | 1 day |

**RTO:** Recovery Time Objective (how fast to recover)  
**RPO:** Recovery Point Objective (how much data loss acceptable)

---

## Summary

- **Replication**: Async master-slave, slaves read-only
- **Lag**: Monitor Seconds_Behind_Master
- **Failover**: Manual or automatic (MHA)
- **Scaling**: Reads to slaves, writes to master
- **Backup**: Binlogs for PITR, full backups
- **HA**: Master-master, group replication, load balancing
- **Monitoring**: Lag, IO thread status, binlog size

Next: [[../03-advanced/01-sharding.md|Sharding & Scaling]]

---

**See Also:**
- [[01-transactions-locks.md|Transactions & Locking]]
- [[../../postgres/02-advanced/01-replication.md|PostgreSQL Replication]]
- [[../../dynamodb/06-scaling/01-global-tables.md|DynamoDB Global Tables]]
