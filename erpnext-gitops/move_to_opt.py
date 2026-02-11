import paramiko
import time

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"
OLD_DIR = "/home/administrator/erpnext-gitops"
NEW_DIR = "/opt/erpnext-gitops"

def execute(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    if exit_status != 0:
        err = stderr.read().decode().strip()
        if err:
            print(f"   Error: {err}")
    return out

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== Moving Git Repo to /opt/ (accessible to all users) ===\n")
    
    # Copy to /opt with sudo
    print("1. Copying repository to /opt/")
    execute(client, f"sudo rm -rf {NEW_DIR}")  # Clean if exists
    execute(client, f"sudo cp -r {OLD_DIR} {NEW_DIR}")
    
    # Make it readable by all
    print("2. Setting permissions for all users")
    execute(client, f"sudo chmod -R 755 {NEW_DIR}")
    execute(client, f"sudo chown -R root:root {NEW_DIR}")
    
    # Update all manifests to use new path
    print(f"3. Updating manifests to use {NEW_DIR}")
    execute(client, f"sudo sed -i 's|file://{OLD_DIR}|file://{NEW_DIR}|g' {NEW_DIR}/bootstrap.yaml")
    execute(client, f"sudo find {NEW_DIR}/apps -name '*.yaml' -exec sed -i 's|file://{OLD_DIR}|file://{NEW_DIR}|g' {{}} +")
    
    # Commit the change
    execute(client, f"cd {NEW_DIR} && sudo git config --global --add safe.directory {NEW_DIR}")
    execute(client, f"cd {NEW_DIR} && sudo git add .")
    try:
        execute(client, f"cd {NEW_DIR} && sudo git commit -m 'Update paths to /opt'")
    except:
        pass
    
    # Delete all apps
    print("\n4. Removing all applications")
    execute(client, "sudo kubectl delete applications --all -n argocd")
    time.sleep(3)
    
    # Apply bootstrap from new location
    print(f"5. Creating bootstrap from {NEW_DIR}")
    result = execute(client, f"sudo kubectl apply -f {NEW_DIR}/bootstrap.yaml")
    print(f"   {result}")
    
    print("\n6. Waiting 8 seconds for auto-creation...")
    time.sleep(8)
    
    # Check results
    print("\n7. Checking applications:")
    result = execute(client, "sudo kubectl get applications -n argocd")
    print(result)
    
    lines = result.strip().split('\n')
    app_count = len(lines) - 1
    
    if app_count >= 3:
        print(f"\n✓ SUCCESS! {app_count} applications created automatically!")
    else:
        print(f"\n⚠ Still only {app_count} app(s). Checking bootstrap status...")
        status = execute(client, "sudo kubectl -n argocd describe application bootstrap-apps | tail -n 20")
        print(status)
    
    client.close()

if __name__ == "__main__":
    main()
