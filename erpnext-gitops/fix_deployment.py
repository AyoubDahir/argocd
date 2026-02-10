#!/usr/bin/env python3
"""
Fix ERPNext deployment issue - correct Git daemon path and verify pods
"""
import paramiko
import time
import sys

SERVER_IP = "173.208.208.91"
USERNAME = "administrator"
PASSWORD = None  # Will prompt

def execute_command(ssh, command, description="", show=True):
    """Execute command and return output"""
    if show:
        print(f"\n{'='*60}")
        print(f"🔧 {description}")
        print(f"{'='*60}")
        print(f"Command: {command}")
    
    stdin, stdout, stderr = ssh.exec_command(f"sudo -S {command}", get_pty=True)
    if PASSWORD:
        stdin.write(f"{PASSWORD}\n")
        stdin.flush()
    
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if show:
        if output:
            print(output)
        if error and 'sudo' not in error.lower():
            print(f"Error: {error}", file=sys.stderr)
    
    return output, error

def main():
    global PASSWORD
    
    # Get password
    import getpass
    PASSWORD = getpass.getpass(f"Password for {USERNAME}@{SERVER_IP}: ")
    
    # Connect
    print(f"\n🔗 Connecting to {SERVER_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(SERVER_IP, username=USERNAME, password=PASSWORD)
        print("✅ Connected!")
        
        # Step 1: Check current directory structure
        print("\n" + "="*60)
        print("📁 Step 1: Checking directory structure")
        print("="*60)
        
        out, _ = execute_command(ssh, "ls -la /opt/", "List /opt directory", show=True)
        out, _ = execute_command(ssh, "ls -la /opt/erpnext-gitops/", "List /opt/erpnext-gitops", show=True)
        
        # Step 2: Fix the nested directory issue
        print("\n" + "="*60)
        print("📁 Step 2: Fixing nested directory")
        print("="*60)
        
        execute_command(ssh, "test -d /opt/erpnext-gitops/erpnext-gitops && echo 'NESTED_EXISTS' || echo 'NOT_NESTED'", "Check if nested", show=True)
        
        # Move contents up if nested
        execute_command(ssh, """
if [ -d /opt/erpnext-gitops/erpnext-gitops ]; then
    echo "Moving nested directory contents..."
    mv /opt/erpnext-gitops /opt/erpnext-gitops-backup
    mv /opt/erpnext-gitops-backup/erpnext-gitops /opt/erpnext-gitops
    rm -rf /opt/erpnext-gitops-backup
    echo "✅ Fixed nested directory"
else
    echo "✅ Directory structure is correct"
fi
        """, "Fix nested directory structure", show=True)
        
        # Step 3: Verify templates exist
        print("\n" + "="*60)
        print("📄 Step 3: Verifying templates")
        print("="*60)
        
        execute_command(ssh, "ls -la /opt/erpnext-gitops/environments/dev/templates/", "Check templates", show=True)
        
        # Step 4: Restart Git daemon with correct path
        print("\n" + "="*60)
        print("🔄 Step 4: Restarting Git daemon")
        print("="*60)
        
        execute_command(ssh, "pkill git-daemon", "Kill existing daemon", show=False)
        time.sleep(1)
        execute_command(ssh, "git daemon --reuseaddr --base-path=/opt --export-all --enable=receive-pack --detach", "Start Git daemon", show=True)
        
        # Step 5: Recreate ArgoCD application
        print("\n" + "="*60)
        print("🔄 Step 5: Recreating ArgoCD application")
        print("="*60)
        
        execute_command(ssh, "kubectl delete application erpnext-dev -n argocd --ignore-not-found=true", "Delete old app", show=True)
        time.sleep(2)
        execute_command(ssh, "kubectl apply -f /opt/erpnext-gitops/apps/dev.yaml", "Create new app", show=True)
        
        # Step 6: Wait for sync and check pods
        print("\n" + "="*60)
        print("⏳ Step 6: Waiting for ArgoCD to sync (30 seconds)...")
        print("="*60)
        
        for i in range(30, 0, -5):
            print(f"⏱️  {i} seconds remaining...")
            time.sleep(5)
        
        # Step 7: Check deployment status
        print("\n" + "="*60)
        print("📊 Step 7: Checking deployment status")
        print("="*60)
        
        execute_command(ssh, "kubectl get applications -n argocd | grep erpnext", "ArgoCD apps", show=True)
        execute_command(ssh, "kubectl get all -n erpnext-dev", "All resources in erpnext-dev", show=True)
        execute_command(ssh, "kubectl get pods -n erpnext-dev", "Pods status", show=True)
        
        # Step 8: If no pods, check why
        out, _ = execute_command(ssh, "kubectl get pods -n erpnext-dev --no-headers | wc -l", "Count pods", show=False)
        pod_count = int(out.strip())
        
        if pod_count == 0:
            print("\n" + "="*60)
            print("🔍 Step 8: No pods found - investigating")
            print("="*60)
            
            execute_command(ssh, "kubectl describe application erpnext-dev -n argocd | grep -A 20 'Status:'", "ArgoCD status", show=True)
            execute_command(ssh, "kubectl get events -n erpnext-dev --sort-by='.lastTimestamp'", "Recent events", show=True)
        else:
            print(f"\n✅ Found {pod_count} pod(s)!")
            execute_command(ssh, "kubectl logs -n erpnext-dev deployment/erpnext --tail=20", "Pod logs", show=True)
        
        print("\n" + "="*60)
        print("✅ Script completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("\n🔌 Disconnected")

if __name__ == "__main__":
    main()
