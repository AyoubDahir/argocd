import paramiko

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== Manually Syncing Bootstrap App ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl patch application bootstrap-apps -n argocd --type merge -p '{\"operation\":{\"sync\":{}}}'")
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(f"Note: {err}")
    
    print("\n=== Checking if Git server is still running ===")
    stdin, stdout, stderr = client.exec_command("ps aux | grep 'http.server 3000' | grep -v grep")
    print(stdout.read().decode())
    
    print("\n=== Testing Git HTTP access locally ===")
    stdin, stdout, stderr = client.exec_command("curl -I http://localhost:3000/.git/HEAD")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
