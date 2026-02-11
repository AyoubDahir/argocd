import paramiko

HOST = "173.208.208.91"
USER = "administrator" 
PASS = "Xatuute13@@"
REMOTE_DIR = "/home/administrator/erpnext-gitops"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Remove Chart.yaml files that reference external Helm repos
    print("=== Removing problematic Chart.yaml files ===")
    cmds = [
        f"rm {REMOTE_DIR}/environments/dev/Chart.yaml",
        f"rm {REMOTE_DIR}/environments/staging/Chart.yaml",
        f"rm {REMOTE_DIR}/environments/production/Chart.yaml",
    ]
    
    for cmd in cmds:
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
    
    # Create simple Kubernetes manifests instead
    print("\n=== Creating Simple Namespace Manifest ===")
    manifest = """apiVersion: v1
kind: Namespace
metadata:
  name: erpnext-dev
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: erpnext-placeholder
  namespace: erpnext-dev
data:
  message: "ERPNext deployment pending custom image"
"""
    
    stdin, stdout, stderr = client.exec_command(f"cat > {REMOTE_DIR}/environments/dev/namespace.yaml << 'EOF'\n{manifest}\nEOF")
    stdout.channel.recv_exit_status()
    
    # Update git repo
    print("\n=== Committing changes to Git ===")
    git_cmds = [
        f"cd {REMOTE_DIR} && git add .",
        f"cd {REMOTE_DIR} && git commit -m 'Remove external Helm dependencies'",
        f"cd {REMOTE_DIR} && git update-server-info",
    ]
    
    for cmd in git_cmds:
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
    
    # Delete and recreate the dev app
    print("\n=== Refreshing Dev Application ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl delete application erpnext-dev -n argocd")
    stdout.channel.recv_exit_status()
    
    import time
    time.sleep(2)
    
    stdin, stdout, stderr = client.exec_command("sudo kubectl apply -f /home/administrator/erpnext-gitops/apps/dev.yaml")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
