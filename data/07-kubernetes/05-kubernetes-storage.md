# 💾 Kubernetes Storage — Complete Deep Dive

## ToC
- PV | PVC | StorageClass | CSI Architecture | Volume Modes | CSI Drivers | StatefulSet | VolumeSnapshot | Cloning | Expansion | Ephemeral | Data Gravity | Performance

---

## PersistentVolume

```yaml
apiVersion: v1
kind: PersistentVolume
spec:
  capacity:
    storage: 100Gi
  volumeMode: Filesystem
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - node-1
```

| Reclaim | Behavior |
|---------|----------|
| Retain | PV kept after PVC delete |
| Delete | PV + storage auto-deleted |
| Recycle | (deprecated) rm -rf |

| Access Mode | Meaning |
|-------------|---------|
| RWO | Single node read-write |
| ROX | Multi-node read-only |
| RWX | Multi-node read-write |
| RWOP | Single pod read-write |

---

## PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: gp3
---
apiVersion: v1
kind: Pod
spec:
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: app-pvc
  containers:
  - name: app
    volumeMounts:
    - mountPath: /var/lib/data
      name: data
```

**Binding flow:** PVC created -> match PV (or dynamic provision) -> one-to-one bind -> pod uses PVC -> PVC persists after pod -> reclaim on PVC delete

---

## StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

| Binding Mode | Behavior |
|--------------|----------|
| Immediate | Bind on PVC creation |
| WaitForFirstConsumer | Bind after pod scheduled (topology-aware) |

| Provisioner | Type | Access |
|-------------|------|--------|
| ebs.csi.aws.com | EBS | RWO |
| efs.csi.aws.com | EFS | RWX |
| disk.csi.azure.com | Azure Disk | RWO |
| pd.csi.gke.io | GCE PD | RWO/RWX |
| nfs.csi.k8s.io | NFS | RWX |
| rook-ceph.rbd.csi.ceph.com | Ceph | RWO/RWX |

---

## CSI Architecture

```
  +----------------+      +----------------+      +----------------+
  | CSI Controller |      | CSI Node       |      | CSI Identity   |
  | CreateVolume   |      | NodePublish    |      | GetPluginInfo  |
  | DeleteVolume   |      | NodeUnpublish  |      | GetCapabilities|
  | ControllerPub  |      | NodeStage      |      | Probe          |
  | CreateSnapshot |      | NodeUnstage    |      |                |
  | ExpandVolume   |      | GetVolumeStats |      |                |
  +----------------+      +----------------+      +----------------+
```

**3 gRPC services:** Controller (cluster ops), Node (per-node mount), Identity (capabilities)

---

## Volume Modes

```yaml
# Filesystem (default) - formatted FS
spec:
  volumeMode: Filesystem

# Block - raw block device
spec:
  volumeMode: Block
---
apiVersion: v1
kind: Pod
spec:
  containers:
  - volumeDevices:
    - devicePath: /dev/xvda
      name: data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: block-pvc
```

**Block:** for high-performance DB, no FS overhead

---

## CSI Drivers

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
```

**Rook/Ceph HA:**
```yaml
apiVersion: ceph.rook.io/v1
kind: CephCluster
spec:
  mon:
    count: 3
  storage:
    nodes:
    - name: node-1
      devices:
      - name: nvme0n1
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
provisioner: rook-ceph.rbd.csi.ceph.com
parameters:
  pool: replicapool
```

**Longhorn:**
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
provisioner: driver.longhorn.io
parameters:
  numberOfReplicas: "3"
```

---

## StatefulSet volumeClaimTemplates

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  replicas: 3
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes:
      - ReadWriteOnce
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
```

**PVC naming:** `data-postgres-0`, `data-postgres-1`, `data-postgres-2`. Scale down preserves PVCs. Scale up reuses existing PVC by ordinal.

---

## VolumeSnapshot

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: fast-snap
driver: ebs.csi.aws.com
deletionPolicy: Delete
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
spec:
  volumeSnapshotClassName: fast-snap
  source:
    persistentVolumeClaimName: data-postgres-0
---
apiVersion: v1
kind: PersistentVolumeClaim
spec:
  dataSource:
    name: db-snapshot-2024
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

---

## Volume Cloning & Expansion

**Clone:**
```yaml
spec:
  dataSource:
    name: data-postgres-0
    kind: PersistentVolumeClaim
```
Requires: same/compatible SC, same access mode, same/larger size, CSI CLONE_VOLUME.

**Expansion:** `allowVolumeExpansion: true` in SC. Edit PVC size. Online on EBS, Azure Disk, GCE PD, Ceph, Longhorn. Not on NFS/EFS.

---

## Ephemeral Inline Volumes

```yaml
# CSI ephemeral
volumes:
- name: scratch
  csi:
    driver: ebs.csi.aws.com
    volumeAttributes:
      size: "20"

# Generic ephemeral
volumes:
- name: cache
  ephemeral:
    volumeClaimTemplate:
      spec:
        accessModes: [ReadWriteOnce]
        resources:
          requests:
            storage: 10Gi

# ConfigMap as volume
volumes:
- name: config
  configMap:
    name: app-config
```

**Generic ephemeral:** PVC created with pod, deleted with pod.

---

## Data Gravity Patterns

**Local SSDs:**
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

```yaml
apiVersion: v1
kind: PersistentVolume
spec:
  local:
    path: /mnt/disks/ssd1
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - node-1
```

**Rook/Ceph HA:** Replication 3x, failure domain host. Ceph CRUSH map distributes across nodes.

---

## Storage Performance

| Type | Max IOPS | Max Throughput | Latency |
|------|----------|----------------|---------|
| gp3 (EBS) | 16K | 1000 MB/s | 1-5ms |
| io2 (EBS) | 256K | 4000 MB/s | <1ms |
| Premium SSD (Azure) | 20K | 900 MB/s | 1-5ms |
| Local NVMe | 500K | 3000 MB/s | <0.1ms |

**Ephemeral storage limits:**
```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - resources:
      requests:
        ephemeral-storage: "5Gi"
      limits:
        ephemeral-storage: "10Gi"
```

---

## Simplest Mental Model

```
K8s storage = shipping container warehouse

+------------------------------------------------------------------------------+
|  PV = shipping container  |  PVC = label "need 50cu ft"                     |
|  StorageClass = FedEx/UPS  |  CSI = loading dock standard                   |
|  Access = how many doors  |  Snapshot = photo of contents                   |
|  Clone = duplicate container  |  Expansion = swap for bigger                |
|  Ephemeral = cardboard box (dies with pod)                                  |
|                                                                              |
|  Core: PV = cluster resource. PVC = request matched to PV.                  |
|  StorageClass = policy for HOW PV is created. CSI = translator layer.       |
+------------------------------------------------------------------------------+
