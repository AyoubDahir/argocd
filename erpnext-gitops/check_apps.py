import paramiko

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== All Applications ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get applications -n argocd")
    print(stdout.read().decode())
    
    print("\n=== Bootstrap App Details ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl describe application bootstrap-apps -n argocd")
    output = stdout.read().decode()
    # Print only relevant parts
    for line in output.split('\n'):
        if 'Health Status' in line or 'Sync Status' in line or 'Message' in line or 'Repo URL' in line:
            print(line)
    
    print("\n=== Pods in argocd namespace ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get pods -n argocd")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
