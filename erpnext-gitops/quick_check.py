import paramiko

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Check if the previous script is still running
    print("=== Checking for running Python processes ===")
    stdin, stdout, stderr = client.exec_command("ps aux | grep fix_git_sync | grep -v grep")
    print(stdout.read().decode())
    
    # Check current applications status
    print("\n=== Current Applications ===")
    stdin,stdout, stderr = client.exec_command("sudo kubectl get applications -n argocd")
    print(stdout.read().decode())
    
    # Check if HTTP server is running on new path
    print("\n=== Testing New Git URL ===")
    stdin, stdout, stderr = client.exec_command("curl -I http://localhost:3000/erpnext-gitops/.git/HEAD")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    main()
