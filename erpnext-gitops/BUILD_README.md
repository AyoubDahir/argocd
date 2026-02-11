# ERPNext Custom Apps - Full Stack

This repository contains the Dockerfile and CI/CD configuration to build a custom ERPNext image with the following apps:

## Custom Apps Included

From https://github.com/AyoubDahir/fullii.git:

1. **healthcare** - Healthcare management
2. **his** - Hospital Information System
3. **hrms** - Human Resource Management System
4. **insights** - Business intelligence and analytics
5. **rasiin_design** - Design and asset management
6. **rasiin_hr** - HR extensions
7. **frappe_whatsapp** - WhatsApp integration

Plus standard apps:
- **frappe** - Framework (v14)
- **erpnext** - Core ERP (v14)

## Building the Image

### Locally
```bash
docker build -t erpnext-custom:latest .
```

### Via GitHub Actions
Push to `main` branch and the workflow will:
1. Build the Docker image
2. Push to GitHub Container Registry (ghcr.io)
3. Update the GitOps repository
4. Argo CD automatically deploys to dev

## Image Registry

Images are pushed to: `ghcr.io/ayoubdahir/erpnext-custom`

Tags:
- `latest` - Latest build from main branch
- `main-<sha>` - Specific commit SHA

## CI/CD Pipeline

The pipeline consists of two jobs:

### 1. build-and-push
- Builds multi-stage Docker image
- Pushes to GitHub Container Registry
- Uses layer caching for faster builds

### 2. update-gitops
- Clones the argocd repository
- Updates `environments/dev/values.yaml` with new image tag
- Commits and pushes changes
- Argo CD detects the change and deploys

## GitOps Integration

This repository integrates with: https://github.com/AyoubDahir/argocd.git

When a new image is built:
1. GitOps repo is automatically updated
2. Argo CD syncs within 3 minutes
3. New pods are rolled out in the dev namespace
4. Zero-downtime deployment

## Setup Required

### 1. GitHub Secrets
Add to repository secrets (Settings → Secrets):

```
GITOPS_PAT = <GitHub Personal Access Token with repo write access>
```

**To create PAT**:
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token
3. Select scopes: `repo` (full control)
4. Copy token and add as secret

### 2. Enable GitHub Packages
- Go to repository Settings → Actions → General
- Under "Workflow permissions", select "Read and write permissions"

## Local Development

```bash
# Build image
docker build -t erpnext-custom:dev .

# Run locally
docker run -d \
  -p 8000:8000 \
  -e FRAPPE_SITE_NAME=localhost \
  --name erpnext \
  erpnext-custom:dev

# Access at http://localhost:8000
```

## Deployment Flow

```
Code Change → Push to GitHub
     ↓
GitHub Actions builds image
     ↓
Image pushed to ghcr.io
     ↓
GitOps repo updated with new tag
     ↓
Argo CD detects change
     ↓
Kubernetes rolls out new pods
     ↓
ERPNext updated in dev environment
```

## Troubleshooting

### Build fails
- Check Dockerfile syntax
- Verify all apps exist in fullii repo
- Check GitHub Actions logs

### Image not deploying
- Verify GITOPS_PAT secret is set
- Check Argo CD sync status
- Verify image tag in values.yaml

### Apps not working
- Check app dependencies in requirements.txt
- Verify bench build completed successfully
- Check container logs: `kubectl logs -n erpnext-dev <pod-name>`

## Next Steps

1. Add this Dockerfile to fullii repository
2. Set up GitHub Actions workflow
3. Configure PAT secret
4. Push to trigger first build
5. Watch Argo CD deploy automatically

---

**Maintained by**: AyoubDahir  
**GitOps Repo**: https://github.com/AyoubDahir/argocd.git  
**Apps Repo**: https://github.com/AyoubDahir/fullii.git
