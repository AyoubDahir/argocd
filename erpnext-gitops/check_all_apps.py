import paramiko
import time

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=== Waiting 5 seconds for sync to complete ===")
    time.sleep(5)
    
    print("\n=== All Applications (Should show dev, staging, production) ===")
    stdin, stdout, stderr = client.exec_command("sudo k kubectl get applications -n argocd")
    print(stdout.read().decode())
    
    print("\n=== Application Pods (ERPNext namespaces) ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get pods -A | grep erpnext")
    out = stdout.read().decode()
    if out:
        print(out)
    else:
        print("No ERPNext pods found yet")
    
    print("\n=== Checking Helm Repositories in Argo CD ===")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get configmap argocd-cm -n argocd -o yaml | grep -A 5 'repositories'")
    out = stdout.read().decode()
    if out:
        print(out)
    else:
        print("No custom repositories configured yet")

    client.close()

if __name__ == "__main__":
    main()
