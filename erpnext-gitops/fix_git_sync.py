import paramiko
import time

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"
REMOTE_DIR = "/home/administrator/erpnext-gitops"

def execute_command(client, command, description=""):
    if description:
        print(f"\n=== {description} ===")
    print(f"Exec: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    
    if out:
        print(f"Output: {out}")
    if err and exit_status != 0:
        print(f"Error: {err}")
    
    return exit_status == 0

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Kill any existing HTTP servers
    print("=== Stopping old HTTP server ===")
    execute_command(client, "pkill -f 'http.server 3000' || true")
    time.sleep(1)
    
    # Configure Git for better HTTP transport
    print("\n=== Configuring Git for HTTP ===")
    commands = [
        f"cd {REMOTE_DIR} && git config http.receivepack true",
        f"cd {REMOTE_DIR} && git config http.uploadpack true",
        f"cd {REMOTE_DIR} && git update-server-info",
        # Create info/refs for dumb HTTP
        f"cd {REMOTE_DIR}/.git && chmod -R a+rX .",  # Make .git readable
        f"cd {REMOTE_DIR} && git update-server-info",
    ]
    
    for cmd in commands:
        execute_command(client, cmd)
    
    # Start HTTP server with better configuration
    print("\n=== Starting New HTTP Server ===")
    # Use nohup to keep it running, serve from parent directory so /erpnext-gitops/.git is accessible
    execute_command(client, 
        f"cd /home/administrator && nohup python3 -m http.server 3000 > /tmp/gitserver.log 2>&1 &")
    
    time.sleep(2)
    
    # Test Git HTTP access
    print("\n=== Testing Git HTTP Access ===")
    # Test the info/refs endpoint which Argo CD uses
    execute_command(client, 
        "curl -I http://localhost:3000/erpnext-gitops/.git/info/refs?service=git-upload-pack",
        "Testing Git Smart HTTP")
    
    # Also test direct HEAD access
    execute_command(client,
        "curl http://localhost:3000/erpnext-gitops/.git/HEAD",
        "Testing HEAD file")
    
    # Update the bootstrap app to use the corrected URL
    print("\n=== Updating Bootstrap App URL ===")
    # The URL should be http://173.208.208.91:3000/erpnext-gitops/.git (not just /.git)
    execute_command(client,
        f"sed -i 's|http://173.208.208.91:3000/.git|http://173.208.208.91:3000/erpnext-gitops/.git|g' {REMOTE_DIR}/bootstrap.yaml")
    
    # Also update all app manifests
    execute_command(client,
        f"sed -i 's|http://173.208.208.91:3000/.git|http://173.208.208.91:3000/erpnext-gitops/.git|g' {REMOTE_DIR}/apps/*.yaml")
    
    # Commit the changes
    execute_command(client, f"cd {REMOTE_DIR} && git add .")
    execute_command(client, f"cd {REMOTE_DIR} && git commit -m 'Fix Git URLs' || true")
    execute_command(client, f"cd {REMOTE_DIR} && git update-server-info")
    
    # Delete and recreate bootstrap app with correct URL
    print("\n=== Recreating Bootstrap App ===")
    execute_command(client, "sudo kubectl delete application bootstrap-apps -n argocd || true")
    time.sleep(2)
    execute_command(client, f"sudo kubectl apply -f {REMOTE_DIR}/bootstrap.yaml")
    
    # Also delete and let bootstrap recreate erpnext-dev
    print("\n=== Letting Bootstrap Auto-Create Dev App ===")
    execute_command(client, "sudo kubectl delete application erpnext-dev -n argocd || true")
    
    print("\n=== Waiting for Auto-Creation ===")
    time.sleep(5)
    
    # Check status
    execute_command(client, "sudo kubectl get applications -n argocd", "Checking Applications")
    
    client.close()
    print("\n✓ Done! Check Argo CD UI in a few moments.")

if __name__ == "__main__":
    main()
