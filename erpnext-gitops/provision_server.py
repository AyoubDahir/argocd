import paramiko
import time
import sys

# Server Details
HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def create_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASS)
        print("Connected successfully.")
        return client
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

def execute_command(client, command, description):
    print(f"\n--- {description} ---")
    print(f"Executing: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    
    # Stream output
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    
    if out:
        print(f"Output:\n{out}")
    if err:
        print(f"Error/Stderr:\n{err}")
    
    if exit_status != 0:
        print(f"Command failed with exit status {exit_status}")
        return False
    return True

def main():
    client = create_client()
    
    # 1. Update and Install Dependencies
    execute_command(client, "sudo apt-get update && sudo apt-get install -y git curl", "Installing Dependencies")
    
    # 2. Install K3s
    # K3s installation might fail if already installed, or return non-zero if service start is slow.
    # We strip the '| sh -' to run it more controllably if needed, but the one-liner is standard.
    print("\n--- Installing K3s ---")
    # check if K3s is already there
    stdin, stdout, stderr = client.exec_command("which k3s")
    if stdout.channel.recv_exit_status() == 0:
        print("K3s is already installed.")
    else:
        execute_command(client, "curl -sfL https://get.k3s.io | sh -", "Running K3s Installer")
    
    # 3. Check Node Status
    # Wait loop
    print("\n--- Waiting for Node Release ---")
    for i in range(10):
        # We need sudo to run kubectl usually unless config is chowned
        success = execute_command(client, "sudo kubectl get nodes", "Checking K3s Node Status")
        if success:
            break
        time.sleep(5)

    # 4. Install Argo CD
    print("\n--- Installing Argo CD ---")
    # Create namespace
    execute_command(client, "sudo kubectl create namespace argocd", "Creating argocd namespace")
    # Apply Manifest
    execute_command(client, "sudo kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml", "Applying Argo CD Manifests")
    
    # 5. Wait for Argo CD Server
    print("\n--- Waiting for Argo CD Server ---")
    execute_command(client, "sudo kubectl wait --for=condition=Available deployment/argocd-server -n argocd --timeout=300s", "Waiting for argocd-server")

    # 6. Retrieve Initial Password
    print("\n--- Retrieving Argo CD Admin Password ---")
    execute_command(client, "sudo kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d", "Fetching Password")
    
    client.close()

if __name__ == "__main__":
    main()
