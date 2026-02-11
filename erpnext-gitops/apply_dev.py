import paramiko

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Since bootstrap isn't working as expected, let's manually apply the dev app
    print("=== Manually Applying Dev Application ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl apply -f /home/administrator/erpnext-gitops/apps/dev.yaml")
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(f"Stderr: {err}")
    
    print("\n=== Checking All Applications ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get applications -n argocd")
    print(stdout.read().decode())
    
    print("\n=== Checking Dev App Details ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get application erpnext-dev -n argocd -o yaml | grep -A 10 'status:'")
    out = stdout.read().decode()
    if out:
        print(out[:1000])  # First 1000 chars to see the status

    client.close()

if __name__ == "__main__":
    main()
