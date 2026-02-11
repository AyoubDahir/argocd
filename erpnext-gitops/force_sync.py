import paramiko
import time

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Force sync the bootstrap app using argocd CLI or kubectl patch
    print("=== Force Syncing Bootstrap App ===")
    stdin, stdout, stderr = client.exec_command(
        "sudo kubectl -n argocd patch application bootstrap-apps --type=json -p='[{\"op\": \"replace\", \"path\": \"/operation\", \"value\": {\"sync\": {}}}]' 2>&1")
    print(stdout.read().decode())
    
    print("\n=== Waiting 10 seconds forSync ===")
    time.sleep(10)
    
    # Check applications
    print("\n=== All Applications (Should show child apps if auto-created) ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get applications -n argocd")
    result = stdout.read().decode()
    print(result)
    
    # Check logs to see what's happening with bootstrap
    print("\n=== Bootstrap App Status ===")
    stdin, stdout, stderr = client.exec_command(
        "sudo kubectl -n argocd describe application bootstrap-apps | grep -A 20 'Status:'")
    desc = stdout.read().decode()
    print(desc[:2000])  # First 2000 chars
    
    client.close()

if __name__ == "__main__":
    main()
