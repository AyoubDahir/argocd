import paramiko
import time

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"
GIT_DIR = "/opt/erpnext-gitops"

def execute(client, cmd, show=True):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    if show and out:
        print(out)
    return out

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== Installing and Configuring Git Daemon ===\n")
    
    # Install git if not already (usually installed)
    print("1. Ensuring git is installed...")
    execute(client, "sudo apt-get install -y git", show=False)
    
    # Mark the directory as safe for git-daemon
    print(f"2. Configuring {GIT_DIR} for git-daemon...")
    execute(client, f"sudo touch {GIT_DIR}/.git/git-daemon-export-ok")
    
    # Kill any existing git-daemon
    print("3. Stopping old git-daemon...")
    execute(client, "sudo pkill git-daemon || true", show=False)
    time.sleep(1)
    
    # Start git-daemon
    print("4. Starting git-daemon on port 9418...")
    execute(client, 
        f"sudo git daemon --reuseaddr --base-path=/opt --export-all --enable=receive-pack --detach")
    
    time.sleep(2)
    
    # Test git daemon
    print("\n5. Testing git://localhost/erpnext-gitops...")
    result = execute(client, "git ls-remote git://localhost/erpnext-gitops")
    if result:
        print("   ✓ Git daemon is working!")
    else:
        print("   ⚠ No output from git daemon test")
    
    # Update manifests to use git://
    NEW_URL = "git://173.208.208.91/erpnext-gitops"
    print(f"\n6. Updating all manifeststo {NEW_URL}...")
    execute(client, f"sudo sed -i 's|repoURL:.*|repoURL: {NEW_URL}|g' {GIT_DIR}/bootstrap.yaml")
    execute(client, f"sudo find {GIT_DIR}/apps -name '*.yaml' -exec sed -i 's|repoURL:.*|repoURL: {NEW_URL}|g' {{}} +")
    
    # Delete apps
    print("\n7. Removing applications...")
    execute(client, "sudo kubectl delete applications --all -n argocd", show=False)
    time.sleep(3)
    
    # Recreate bootstrap
    print(f"8. Creating bootstrap with git:// URL...")
    execute(client, f"sudo kubectl apply -f {GIT_DIR}/bootstrap.yaml")
    
    print("\n9. Waiting 10 seconds for sync...")
    time.sleep(10)
    
    # Check applications
    print("\n10. Final status:")
    result = execute(client, "sudo kubectl get applications -n argocd")
    
    lines = result.strip().split('\n')
    app_count = len(lines) - 1
    
    print(f"\n📊 Found {app_count} applications")
    if app_count >= 3:
        print("🎉 SUCCESS! Child apps auto-created!")
    
    client.close()

if __name__ == "__main__":
    main()
