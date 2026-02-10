import paramiko
import time

SERVER_IP = "173.208.208.91"
USERNAME = "administrator"
PASSWORD = "Xatuute13@@"

def execute(ssh, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(f"sudo -S {cmd}", get_pty=True)
    stdin.write(f"{PASSWORD}\n")
    stdin.flush()
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err: print(f"Stderr: {err}")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=USERNAME, password=PASSWORD)

# 1. Check if nested
print("Checking directory structure...")
stdin, stdout, stderr = ssh.exec_command("ls /opt/erpnext-gitops/")
files = stdout.read().decode().split()

if "erpnext-gitops" in files:
    print("Found nested directory! Fixing...")
    # Move inner content to tmp
    execute(ssh, "mv /opt/erpnext-gitops/erpnext-gitops /opt/erpnext-gitops-temp")
    # Clear outer
    execute(ssh, "rm -rf /opt/erpnext-gitops")
    # Move temp to outer
    execute(ssh, "mv /opt/erpnext-gitops-temp /opt/erpnext-gitops")
    print("Fixed directory structure!")
else:
    print("Directory structure looks correct.")

# 2. Restart Git Daemon
print("Restarting Git daemon...")
execute(ssh, "pkill git-daemon")
time.sleep(1)
execute(ssh, "git daemon --reuseaddr --base-path=/opt --export-all --enable=receive-pack --detach")

# 3. Force Sync
print("Forcing ArgoCD sync...")
execute(ssh, "kubectl delete application erpnext-dev -n argocd --ignore-not-found=true")
time.sleep(2)
execute(ssh, "kubectl apply -f /opt/erpnext-gitops/apps/dev.yaml")

# 4. Check Pods
print("Checking pods...")
stdin, stdout, stderr = ssh.exec_command("sudo kubectl get pods -n erpnext-dev")
print(stdout.read().decode())

ssh.close()
