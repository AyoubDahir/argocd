import paramiko
import time

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== Waiting 3 seconds for sync ===")
    time.sleep(3)
    
    print("\n=== All Applications ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get applications -n argocd")
    print(stdout.read().decode())
    
    print("\n=== Namespaces Created ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get namespaces | grep erpnext")
    print(stdout.read().decode())
    
    print("\n=== Resources in erpnext-dev namespace ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get all -n erpnext-dev")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
