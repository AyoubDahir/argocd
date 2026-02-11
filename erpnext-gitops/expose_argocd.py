import paramiko

# Server Details
HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"

def create_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    return client

def execute_command(client, command):
    print(f"Exec: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if exit_status != 0:
        print(f"Error: {err}")
    else:
        print(f"Output: {out}")

def main():
    client = create_client()
    
    # 1. Patch Argo CD Server to be Type=LoadBalancer
    # K3s has a built-in LoadBalancer (Klipper) that will use the Host IP.
    print("Patching Argo CD Server Service to LoadBalancer...")
    execute_command(client, "sudo kubectl -n argocd patch svc argocd-server -p '{\"spec\": {\"type\": \"LoadBalancer\"}}'")
    
    # 2. Check Ingresses
    print("\n--- Checking Ingress Status ---")
    execute_command(client, "sudo kubectl get ingress -A")
    
    client.close()

if __name__ == "__main__":
    main()
