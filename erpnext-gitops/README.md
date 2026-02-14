# ERPNext GitOps Control Repository

This repository hosts the Argo CD manifests for the ERPNext Microservices deployment.

## Structure
- `apps/`: Argo CD Application manifests (App of Apps pattern).
- `environments/`: Helm values and templates for Dev, Staging, Production.
- `system/`: Infrastructure components.

## Deployment
Managed by Argo CD.
Source of Truth: `https://github.com/AyoubDahir/argocd.git`
