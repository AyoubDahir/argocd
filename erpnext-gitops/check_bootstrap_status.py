import paramiko

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Get detailed status
    print("=== Bootstrap App Detailed Status ===\n")
    stdin, stdout, stderr = client.exec_command(
        "sudo kubectl -n argocd get application bootstrap-apps -o yaml")
    yaml_output = stdout.read().decode()
    
    # Extract relevant sections
    lines = yaml_output.split('\n')
    in_status = False
    status_lines = []
    
    for line in lines:
        if line.startswith('status:'):
            in_status = True
        if in_status:
            status_lines.append(line)
            if len(status_lines) > 80:  # Limit output
                break
    
    print('\n'.join(status_lines))
    
    # Also manually apply one of the child apps to test
    print("\n\n=== Manually Testing Dev App Creation ===")
    stdin, stdout, stderr = client.exec_command(
        "sudo kubectl apply -f /home/administrator/erpnext-gitops/apps/dev.yaml")
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(f"Stderr: {err}")
    
    # Check again
    print("\n=== Applications After Manual Apply ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get applications -n argocd")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
