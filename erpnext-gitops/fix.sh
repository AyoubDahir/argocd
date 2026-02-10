#!/bin/bash
set -e

echo "🔧 Checking directory structure..."
if [ -d "/opt/erpnext-gitops/erpnext-gitops" ]; then
    echo "Found nested directory! Fixing..."
    sudo mv /opt/erpnext-gitops /opt/erpnext-gitops-temp
    sudo mv /opt/erpnext-gitops-temp/erpnext-gitops /opt/erpnext-gitops
    sudo rm -rf /opt/erpnext-gitops-temp
    echo "✅ Directory structure fixed!"
else
    echo "✅ Directory structure is correct."
fi

echo "🔄 Restarting Git daemon..."
sudo pkill git-daemon || true
sudo git daemon --reuseaddr --base-path=/opt --export-all --enable=receive-pack --detach
echo "✅ Git daemon restarted"

echo "🔄 Recreating dev application..."
sudo kubectl delete application erpnext-dev -n argocd --ignore-not-found=true
sleep 2
sudo kubectl apply -f /opt/erpnext-gitops/apps/dev.yaml
echo "✅ Application recreated"

echo "⏳ Waiting for pods..."
sleep 10
sudo kubectl get pods -n erpnext-dev
