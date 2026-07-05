# Helm

Helm is the package manager for Kubernetes. It bundles related Kubernetes manifests (deployments, services, configmaps, etc.) into reusable packages called charts. Helm manages the full lifecycle of a Kubernetes application — install, upgrade, rollback, and delete — using templated YAML files with configurable values. Charts are versioned, stored in repositories, and can depend on other charts.

## Overview

Raw Kubernetes YAML manifests become unwieldy as microservices multiply. Configuring a service for multiple environments (dev, staging, prod) requires copying and modifying manifests, leading to drift and errors. Helm solves this by templating manifests with Go templates and separating configuration into `values.yaml` files. One chart produces customized manifests for any environment by varying values. Helm also tracks releases — each install or upgrade creates a new release revision that can be rolled back.

## Key Characteristics

- **Charts**: A chart is a directory with a standardized structure: `Chart.yaml` (metadata), `values.yaml` (default configuration), `templates/` (Go-templated YAML), `charts/` (subchart dependencies), and `templates/NOTES.txt` (post-install instructions). Charts can be packaged as `.tgz` files and hosted in chart repositories (OCI registries, ChartMuseum, GitHub Pages).
- **Templates**: Go template syntax (`{{ .Values.replicaCount }}`) parameterizes YAML manifests. Helm injects built-in objects: `Values` (user config), `Release` (release metadata), `Chart` (chart metadata), `Files` (chart file access), and `Capabilities` (cluster capabilities). Template functions from Sprig and Helm-specific functions (include, required, tpl, lookup) enable complex logic.
- **Values and Overrides**: Default values in `values.yaml` can be overridden at install/upgrade time using `--values` (file) or `--set` (inline). Multi-environment setups use separate values files: `values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml`. Global values (`.Values.global.*`) propagate to subcharts.
- **Releases**: Each `helm install` creates a release with a revision number (1). Every `helm upgrade` increments the revision (2, 3...). `helm rollback RELEASE REVISION` reverts to a previous revision. Release history is stored in Secrets in the release namespace. Release naming conventions and lifecycle hooks (pre-install, post-install, pre-upgrade, post-upgrade) enable complex workflows.
- **Dependencies**: Charts can depend on other charts (e.g., your app chart depends on a PostgreSQL chart). Dependencies are listed in `Chart.yaml` and managed with `helm dependency update`. Dependency charts are stored in `charts/` or referenced from repositories. This enables composable application stacks defined as a single chart.
- **Hooks**: Lifecycle hooks run operations at specific points: `pre-install` (before resources are created), `post-install` (after all resources are ready), `pre-delete`, `post-delete`, `pre-upgrade`, `post-upgrade`, `pre-rollback`, `post-rollback`. Hooks are Kubernetes Jobs or Pods. Common uses: database migrations (pre-upgrade), pre-flight checks (pre-install), and cleanup (post-delete).
- **Chart Testing**: `helm test` runs validation jobs defined in the chart templates against a release. Tests verify that the application is functioning correctly after deployment. Combined with linting (`helm lint`) and packaging (`helm package`), charts can be validated in CI before publishing.

## Why It Matters

Helm transforms Kubernetes from a low-level infrastructure API into an application platform. A single `helm install myapp ./chart` deploys a complete microservice with all dependencies. Charts are versioned artifacts that flow through CI/CD, ensuring consistent deployments across environments. The values pattern separates configuration from code, enabling environment-specific tuning without manifest duplication.

## Related Concepts

- [Kubernetes](02-Kubernetes.md) — Helm packages Kubernetes resources
- [Docker](01-Docker.md) — Charts deploy Docker containers
- [Rolling Update](10-Rolling-Update.md) — Helm upgrades can use rolling update strategies
- [Blue-Green](08-BlueGreen.md) — Helm can manage blue-green deployments with hooks

---

## Mental Model

Helm is like IKEA furniture with an instruction booklet. The chart is the booklet (deployment, service, configmap templates), and the values.yaml is your customization choices (wood color, drawer size). One booklet lets you build the same cabinet in different configurations for different rooms (environments). If you make a mistake during assembly, you can roll back to a previous step (helm rollback). Helm dependency management is like buying a wardrobe that includes drawer organizers from a different product line.
