import paramiko

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== ALL APPLICATIONS ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get applications -n argocd")
    result = stdout.read().decode()
    print(result)
    
    lines = result.strip().split('\n')
    app_count = len(lines) - 1
    
    print(f"\n📊 Total: {app_count} applications")
    
    if app_count >= 3:
        print("✓ Child apps auto-created successfully!")
    else:
        print("\nLet me check bootstrap sync status...")
        stdin, stdout, stderr = client.exec_command(
            "sudo kubectl -n argocd get application bootstrap-apps -o jsonpath='{.status.sync.status}'")
        sync_status = stdout.read().decode()
        print(f"Sync Status: {sync_status}")
        
        stdin, stdout, stderr = client.exec_command(
            "sudo kubectl -n argocd get application bootstrap-apps -o jsonpath='{.status.conditions[0].message}'")
        message = stdout.read().decode()
        print(f"Message: {message[:500]}")
    
    # Check namespaces
    print("\n=== ERPNEXT NAMESPACES ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get ns | grep erpnext")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
