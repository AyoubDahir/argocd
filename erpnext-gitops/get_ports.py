import paramiko

HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("--- Argo CD Ports ---")
    # Get just the ports column which usually has the mapping
    stdin, stdout, stderr = client.exec_command("sudo kubectl get svc argocd-server -n argocd -o jsonpath='{.spec.ports[*].nodePort}'")
    ports = stdout.read().decode().strip()
    print(f"NodePorts: {ports}")
    
    # Also get names to match
    stdin, stdout, stderr = client.exec_command("sudo kubectl get svc argocd-server -n argocd -o jsonpath='{.spec.ports[*].name}'")
    names = stdout.read().decode().strip()
    print(f"Names: {names}")

    client.close()

if __name__ == "__main__":
    main()
