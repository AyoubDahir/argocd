import paramiko
import time

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"
REMOTE_DIR = "/home/administrator/erpnext-gitops"

def execute(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    stdout.channel.recv_exit_status()
    return stdout.read().decode().strip()

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== Using file:// protocol (local filesystem access) ===\n")
    
    # Update all manifest files to use file:// instead of http://
    NEW_URL = f"file://{REMOTE_DIR}"
    
    print(f"New Git URL: {NEW_URL}")
    
    # Update bootstrap.yaml
    print("\n1. Updating bootstrap.yaml")
    execute(client, 
        f"sed -i 's|repoURL:.*|repoURL: {NEW_URL}|g' {REMOTE_DIR}/bootstrap.yaml")
    
    # Update all app manifests
    print("2. Updating apps/*.yaml")
    execute(client,
        f"find {REMOTE_DIR}/apps -name '*.yaml' -exec sed -i 's|repoURL:.*|repoURL: {NEW_URL}|g' {{}} +")
    
    # Commit changes
    print("3. Committing changes")
    execute(client, f"cd {REMOTE_DIR} && git add .")
    try:
        execute(client, f"cd {REMOTE_DIR} && git commit -m 'Switch to file:// protocol'")
    except:
        print("   (No new changes)")
    
    # Delete all existing applications
    print("\n4. Removing ALL applications for clean start")
    execute(client, "sudo kubectl delete applications --all -n argocd")
    
    time.sleep(3)
    
    # Recreate bootstrap
    print("\n5. Creating bootstrap app with file:// URL")
    result = execute(client, f"sudo kubectl apply -f {REMOTE_DIR}/bootstrap.yaml")
    print(f"   {result}")
    
    print("\n6. Waiting 5 seconds for Argo CD to process...")
    time.sleep(5)
    
    # Check applications
    print("\n7. Checking applications:")
    result = execute(client, "sudo kubectl get applications -n argocd")
    print(result)
    
    # Count apps
    lines = result.strip().split('\n')
    app_count = len(lines) - 1  # Minus header
    
    if app_count >= 3:
        print(f"\n✓ SUCCESS! Found {app_count} applications (should be 4: bootstrap + dev + staging + prod)")
    elif app_count == 1:
        print(f"\n⚠ Only bootstrap exists. Child apps not created yet. Checking status...")
        status = execute(client, "sudo kubectl -narocd get application bootstrap-apps -o yaml | tail -n 50")
        print(status[:1000])
    
    client.close()

if __name__ == "__main__":
    main()
