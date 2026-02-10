import paramiko
import time
import sys

SERVER_IP = "173.208.208.91"
USERNAME = "administrator"
PASSWORD = "Xatuute13@@"

def run_sudo(ssh, cmd):
    print(f"🔄 Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(f"sudo -S {cmd}", get_pty=True)
    stdin.write(f"{PASSWORD}\n")
    stdin.flush()
    
    # Wait for execution
    output = ""
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            chunk = stdout.channel.recv(1024).decode('utf-8')
            output += chunk
            # Print minimal output for progress
            if "password" not in chunk.lower():
                sys.stdout.write(".")
                sys.stdout.flush()
    
    # Get remaining output
    if stdout.channel.recv_ready():
        output += stdout.channel.recv(1024).decode('utf-8')
    
    print("\n")
    return output

def main():
    print(f"🔗 Connecting to {SERVER_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(SERVER_IP, username=USERNAME, password=PASSWORD)
        print("✅ Connected!")
        
        # 1. Fix Directory Structure
        print("\n📁 Checking directory structure...")
        out = run_sudo(ssh, "ls -F /opt/erpnext-gitops/")
        
        if "erpnext-gitops/" in out:
            print("⚠️ Nested directory detected. Fixing...")
            run_sudo(ssh, "mv /opt/erpnext-gitops/erpnext-gitops /opt/erpnext-gitops-temp")
            run_sudo(ssh, "rm -rf /opt/erpnext-gitops")
            run_sudo(ssh, "mv /opt/erpnext-gitops-temp /opt/erpnext-gitops")
            print("✅ Directory nesting fixed.")
            
        # 2. Fix Git Repo
        print("\n🔧 Checking Git repository...")
        out = run_sudo(ssh, "test -d /opt/erpnext-gitops/.git && echo EXISTS || echo MISSING")
        if "MISSING" in out:
            print("⚠️ Git repo missing. Initializing...")
            run_sudo(ssh, "cd /opt/erpnext-gitops && git init")
            run_sudo(ssh, "cd /opt/erpnext-gitops && git config --global --add safe.directory /opt/erpnext-gitops")
            run_sudo(ssh, "cd /opt/erpnext-gitops && git remote add github https://github.com/AyoubDahir/argocd.git || true")
            run_sudo(ssh, "cd /opt/erpnext-gitops && git pull github main || true")
            run_sudo(ssh, "cd /opt/erpnext-gitops && git add .")
            run_sudo(ssh, "cd /opt/erpnext-gitops && git commit -m 'Initial commit' || true")
            print("✅ Git repository initialized and synced.")
        else:
            print("✅ Git repository exists.")
            # Ensure templates are there
            run_sudo(ssh, "cd /opt/erpnext-gitops && git pull github main || true")

        # 3. Check Templates
        print("\n📄 Verifying templates...")
        out = run_sudo(ssh, "ls /opt/erpnext-gitops/environments/dev/templates/deployment.yaml")
        if "No such file" in out:
            print("❌ Critical: deployment.yaml missing! Attempting force pull...")
            run_sudo(ssh, "cd /opt/erpnext-gitops && git fetch github && git reset --hard github/main")
        else:
            print("✅ Templates present.")

        # 4. Restart Git Daemon
        print("\n🔄 Restarting Git Daemon...")
        run_sudo(ssh, "pkill git-daemon || true")
        run_sudo(ssh, "git daemon --reuseaddr --base-path=/opt --export-all --enable=receive-pack --detach")
        print("✅ Git daemon restarted.")

        # 5. Fix ArgoCD App
        print("\n🚀 Re-triggering ArgoCD...")
        run_sudo(ssh, "kubectl delete application erpnext-dev -n argocd --ignore-not-found=true")
        time.sleep(3)
        run_sudo(ssh, "kubectl apply -f /opt/erpnext-gitops/apps/dev.yaml")
        print("✅ ArgoCD application recreated.")

        # 6. Monitor Pods using simple exec
        print("\n⏳ Monitoring Pods (timeout 60s)...")
        stdin, stdout, stderr = ssh.exec_command("sudo -S kubectl get pods -n erpnext-dev -w", get_pty=True)
        stdin.write(f"{PASSWORD}\n")
        stdin.flush()

        start_time = time.time()
        while time.time() - start_time < 60:
            if stdout.channel.recv_ready():
                line = stdout.channel.recv(1024).decode('utf-8')
                sys.stdout.write(line)
                sys.stdout.flush()
                
                if "Running" in line:
                    print("\n\n✅ Pod is RUNNING! Success!")
                    break
                if "Error" in line or "CrashLoopBackOff" in line:
                    print("\n\n❌ Pod failed! Fetching logs...")
                    break
            time.sleep(1)
            
        # Final Status
        print("\n\n📊 Final Pod Status:")
        print(run_sudo(ssh, "kubectl get pods -n erpnext-dev"))
        
        # Get logs if needed
        print("Creating site instructions:")
        print("1. Once pod is running, shell into it: kubectl exec -it -n erpnext-dev <pod-name> -- bash")
        print("2. Create site: bench new-site dev.erp.local --install-app erpnext --install-app healthcare ...")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
