# Kubectl Commands Cheat Sheet

Essential kubectl commands for Kubernetes cluster operations.

## Context & Cluster Management

```bash
# View current context
kubectl config current-context
kubectl config get-contexts
kubectl config view

# Switch context
kubectl config use-context <context-name>

# Create context
kubectl config set-context <name> --cluster=<cluster> --user=<user>

# Get cluster info
kubectl cluster-info
kubectl get nodes
kubectl describe node <node-name>
```

## Namespaces

```bash
# List namespaces
kubectl get namespaces
kubectl get ns

# Create namespace
kubectl create namespace <name>
kubectl create ns <name>

# Delete namespace
kubectl delete namespace <name>

# Set default namespace
kubectl config set-context --current --namespace=<namespace>

# Operate in specific namespace
kubectl -n <namespace> get pods
kubectl --namespace=<namespace> get pods
```

## Pods

```bash
# List pods
kubectl get pods
kubectl get pods -A                    # All namespaces
kubectl get pods -o wide              # Detailed view
kubectl get pods --all-namespaces

# Pod details
kubectl describe pod <pod-name>
kubectl get pod <pod-name> -o yaml
kubectl get pod <pod-name> -o json

# Create pod
kubectl run nginx --image=nginx:latest

# Edit pod
kubectl edit pod <pod-name>

# Delete pod
kubectl delete pod <pod-name>
kubectl delete pods --all

# Logs
kubectl logs <pod-name>
kubectl logs <pod-name> -f              # Follow logs
kubectl logs <pod-name> -p              # Previous container logs
kubectl logs <pod-name> -c <container>  # Specific container

# Execute command in pod
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec <pod-name> -- <command>
kubectl exec <pod-name> -c <container> -- <command>

# Port forward
kubectl port-forward <pod-name> 8080:8080

# Copy files
kubectl cp <pod>:/path/to/file ./local-file
kubectl cp ./local-file <pod>:/path/to/file
```

## Deployments

```bash
# List deployments
kubectl get deployments
kubectl get deploy -o wide

# Create deployment
kubectl create deployment nginx --image=nginx:latest
kubectl create deployment nginx --image=nginx:latest --replicas=3

# View deployment
kubectl describe deployment <deployment-name>
kubectl get deployment <deployment-name> -o yaml

# Edit deployment
kubectl edit deployment <deployment-name>

# Scale deployment
kubectl scale deployment <deployment-name> --replicas=5
kubectl scale deploy/<deployment-name> --replicas=3

# Update image
kubectl set image deployment/<deployment-name> <container>=<image>:<version>

# Rollout status
kubectl rollout status deployment/<deployment-name>

# Rollout history
kubectl rollout history deployment/<deployment-name>

# Undo rollout
kubectl rollout undo deployment/<deployment-name>
kubectl rollout undo deployment/<deployment-name> --to-revision=2

# Delete deployment
kubectl delete deployment <deployment-name>
```

## Services

```bash
# List services
kubectl get services
kubectl get svc
kubectl get svc -o wide

# Create service
kubectl expose pod <pod-name> --port=80 --target-port=8080 --type=LoadBalancer
kubectl expose deployment <deployment-name> --port=80 --type=ClusterIP

# View service
kubectl describe service <service-name>
kubectl get service <service-name> -o yaml

# Service endpoints
kubectl get endpoints <service-name>

# Delete service
kubectl delete service <service-name>
```

## StatefulSets

```bash
# List stateful sets
kubectl get statefulsets
kubectl get sts

# View statefulset
kubectl describe statefulset <name>

# Scale statefulset
kubectl scale statefulset <name> --replicas=3

# Update image
kubectl set image statefulset/<name> <container>=<image>:<version>

# Delete statefulset
kubectl delete statefulset <name>
```

## DaemonSets

```bash
# List daemon sets
kubectl get daemonsets
kubectl get ds

# View daemonset
kubectl describe daemonset <name>

# Delete daemonset
kubectl delete daemonset <name>
```

## ConfigMaps & Secrets

```bash
# Create ConfigMap from literal
kubectl create configmap <name> --from-literal=key=value

# Create ConfigMap from file
kubectl create configmap <name> --from-file=config.yaml

# Create ConfigMap from directory
kubectl create configmap <name> --from-file=./config-dir/

# List ConfigMaps
kubectl get configmaps
kubectl get cm

# View ConfigMap
kubectl describe configmap <name>
kubectl get configmap <name> -o yaml

# Create Secret from literal
kubectl create secret generic <name> --from-literal=password=secretpass

# Create Secret from file
kubectl create secret generic <name> --from-file=secret.txt

# List Secrets
kubectl get secrets
kubectl get secret <name> -o yaml

# Delete ConfigMap/Secret
kubectl delete configmap <name>
kubectl delete secret <name>
```

## Ingress

```bash
# List ingress
kubectl get ingress
kubectl get ing

# View ingress
kubectl describe ingress <name>
kubectl get ingress <name> -o yaml

# Create ingress
kubectl create ingress <name> --rule="host.com/path=service:port"

# Edit ingress
kubectl edit ingress <name>

# Delete ingress
kubectl delete ingress <name>
```

## Labels & Selectors

```bash
# List with labels
kubectl get pods --show-labels
kubectl get pods -L app,environment

# Filter by label
kubectl get pods -l app=nginx
kubectl get pods -l environment=production
kubectl get pods -l "app in (nginx,apache)"
kubectl get pods -l app!=nginx

# Add label
kubectl label pod <pod-name> app=nginx
kubectl label pod <pod-name> environment=production --overwrite

# Remove label
kubectl label pod <pod-name> app-

# Label node
kubectl label node <node-name> workload=compute
```

## Resource Management

```bash
# View resource usage
kubectl top nodes
kubectl top pods
kubectl top pod <pod-name>

# View resource limits
kubectl describe node <node-name> | grep -A 5 "Allocated resources"

# Set resource requests/limits
kubectl set resources deployment <name> --requests=cpu=100m,memory=128Mi --limits=cpu=500m,memory=512Mi
```

## Debugging

```bash
# Pod events
kubectl describe pod <pod-name>

# Check pod logs
kubectl logs <pod-name>
kubectl logs <pod-name> --previous  # If crashed

# Get pod details as YAML
kubectl get pod <pod-name> -o yaml

# Exec into pod
kubectl exec -it <pod-name> -- /bin/bash

# Port forward
kubectl port-forward <pod-name> 8080:8080

# Check container status
kubectl get pod <pod-name> -o wide

# Get events
kubectl get events
kubectl get events --sort-by='.lastTimestamp'

# Describe resource
kubectl describe <resource-type> <name>

# API resources
kubectl api-resources

# Troubleshoot node
kubectl describe node <node-name>
kubectl get nodes -o wide
```

## Apply & Manifest Management

```bash
# Apply manifest
kubectl apply -f deployment.yaml
kubectl apply -f ./manifests/

# Preview apply
kubectl apply -f deployment.yaml --dry-run=client
kubectl apply -f deployment.yaml --dry-run=server

# View applied resources
kubectl get all
kubectl get all -o wide

# Delete by manifest
kubectl delete -f deployment.yaml
kubectl delete -f ./manifests/

# Get current manifest
kubectl get deployment <name> -o yaml > deployment.yaml

# Validate manifest
kubectl apply -f deployment.yaml --validate=true
```

## Patch & Edit

```bash
# Patch resource
kubectl patch pod <pod-name> -p '{"metadata":{"labels":{"app":"updated"}}}'
kubectl patch service <svc-name> -p '{"spec":{"type":"LoadBalancer"}}'

# Edit resource interactively
kubectl edit pod <pod-name>
kubectl edit deployment <deployment-name>
```

## Useful Flags

```bash
-n, --namespace=<ns>           # Operate in namespace
-A, --all-namespaces          # All namespaces
-o, --output=<format>         # yaml, json, wide, custom
--watch, -w                    # Watch resource
--dry-run=client              # Preview without applying
-f, --filename=<file>         # Use manifest file
-l, --selector=<label>        # Filter by labels
--sort-by=<field>             # Sort output
--no-headers                  # Hide column headers
-v=<verbosity>                # Increase verbosity (0-9)
```

## Quick Aliases

Add to `.bashrc` or `.zshrc`:

```bash
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kg='kubectl get'
alias kd='kubectl describe'
alias kex='kubectl exec -it'
alias kdel='kubectl delete'
alias ka='kubectl apply -f'
alias kl='kubectl logs -f'
alias kgc='kubectl config get-contexts'
alias ksc='kubectl config set-context --current --namespace'
```

## Common Tasks

```bash
# Get all resources
kubectl get all

# Find pod by label
kubectl get pods -l app=nginx

# Watch pod status
kubectl get pods --watch

# Get pod IP
kubectl get pod <pod-name> -o jsonpath='{.status.podIP}'

# Get service endpoints
kubectl get endpoints <service-name>

# Restart deployment (rolling restart)
kubectl rollout restart deployment/<deployment-name>

# Port forward to service
kubectl port-forward svc/<service-name> 8080:80

# Check node disk pressure
kubectl describe node | grep -E "Pressure|Allocatable"

# Get container events
kubectl describe pod <pod-name>

# Stream logs from multiple pods
kubectl logs -f deployment/<deployment-name> --all-containers=true
```

## Useful Commands

```bash
# Check API versions
kubectl api-versions

# Check API resources
kubectl api-resources

# Check kubectl version
kubectl version

# Get cluster info
kubectl cluster-info

# Dump cluster state
kubectl cluster-info dump

# Get all events
kubectl get events -A --sort-by='.lastTimestamp'

# Find pods consuming resources
kubectl top pods -A --sort-by=memory

# Check pod readiness
kubectl wait --for=condition=Ready pod/<pod-name> --timeout=300s
```
