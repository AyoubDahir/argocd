#!/bin/bash

# ERPNext GitOps Bootstrap Script

echo "1. Installing Argo CD..."
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "Waiting for Argo CD components to be ready..."
kubectl wait --for=condition=Available deployment/argocd-server -n argocd --timeout=300s

echo "2. Applying Bootstrap Application..."
kubectl apply -f bootstrap.yaml

echo "Done! Argo CD is now syncing your applications."
echo "Get initial admin password:"
echo "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d"
