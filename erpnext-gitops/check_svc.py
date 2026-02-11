import paramiko

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("--- Argo CD Service ---")
    stdin, stdout, stderr = client.exec_command("sudo kubectl get svc argocd-server -n argocd -o wide")
    print(stdout.read().decode())
    
    print("--- Traefik Service ---") # To check port conflicts
    stdin, stdout, stderr = client.exec_command("sudo kubectl get svc traefik -n kube-system -o wide")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
