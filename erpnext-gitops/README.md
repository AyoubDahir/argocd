# ERPNext GitOps Repository

This repository manages the deployment of ERPNext across multiple environments (Dev, Staging, Production) using Argo CD.

## Repository Structure
- **apps/**: Argo CD Application manifests for each environment.
- **environments/**: Helm configuration and environment-specific values.
- **workflows/**: CI/CD pipeline examples.

## Getting Started

### 1. Bootstrap Cluster
Run the setup script to install Argo CD and apply the bootstrap application:
```bash
./setup.sh
```

### 2. Manual Sync
Access the Argo CD UI to visualize the application state and manually sync if auto-sync is disabled.
