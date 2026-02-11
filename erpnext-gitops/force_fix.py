import paramiko
import time

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"
REMOTE_DIR = "/home/administrator/erpnext-gitops"

def execute(client, cmd, desc=""):
    if desc:
        print(f"\n=== {desc} ===")
    print(f"> {cmd[:80]}...")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    stdout.channel.recv_exit_status()
    return stdout.read().decode().strip()

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Update all YAML files with correct URL path
    print("=== Updating Git URLs in all manifests ===")
    execute(client, 
        f"find {REMOTE_DIR} -name '*.yaml' -exec sed -i 's|http://173.208.208.91:3000/.git|http://173.208.208.91:3000/erpnext-gitops/.git|g' {{}} +")
    
    # Commit changes
    print("\n=== Committing URL changes ===")
    execute(client, f"cd {REMOTE_DIR} && git add .")
    try:
        execute(client, f"cd {REMOTE_DIR} && git commit -m 'Fix repository URLs'")
    except:
        print("(No changes or already committed)")
    execute(client, f"cd {REMOTE_DIR} && git update-server-info")
    
    # Delete both apps to force clean recreation
    print("\n=== Removing existing applications ===")
    execute(client, "sudo kubectl delete application bootstrap-apps erpnext-dev -n argocd --ignore-not-found=true")
    
    time.sleep(3)
    
    # Recreate bootstrap with correct URL
    print("\n=== Recreating Bootstrap App ===")
    result = execute(client, f"sudo kubectl apply -f {REMOTE_DIR}/bootstrap.yaml")
    print(result)
    
    print("\n=== Waiting 10 seconds for sync ===")
    time.sleep(10)
    
    # Check results
    result = execute(client, "sudo kubectl get applications -n argocd", "Final Application Status")
    print(result)
   
    # Check if dev was auto-created
    result = execute(client, "sudo kubectl get application erpnext-dev -n argocd 2>&1 | head -n 3")
    if "NotFound" in result:
        print("\n❌ Dev app NOT auto-created yet. May need more time or manual trigger.")
    else:
        print("\n✓ Dev app exists!")
    
    client.close()

if __name__ == "__main__":
    main()
