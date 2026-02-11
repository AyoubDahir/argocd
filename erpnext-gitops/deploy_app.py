import paramiko
import os
import sys
import time

# Server Details
HOST = "173.208.208.91"
USER = "administrator"
PASS = "Xatuute13@@"
LOCAL_DIR = r"c:\erp\erpnext-gitops"
REMOTE_DIR = "/home/administrator/erpnext-gitops"
# Point directly to the .git directory for dumb HTTP transport of non-bare repo
REPO_URL = f"http://{HOST}:3000/.git"

def create_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    return client

def upload_files(sftp, local_dir, remote_dir):
    print(f"Uploading {local_dir} to {remote_dir}...")
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass 

    for root, dirs, files in os.walk(local_dir):
        # Create relative Unix-style path
        rel_path = os.path.relpath(root, local_dir).replace("\\", "/")
        if rel_path == ".":
            remote_path = remote_dir
        else:
            remote_path = f"{remote_dir}/{rel_path}"
        
        try:
            sftp.mkdir(remote_path)
        except IOError:
            pass

        for file in files:
            local_file = os.path.join(root, file)
            remote_file = f"{remote_path}/{file}"
            # Ensure proper separators
            remote_file = remote_file.replace("//", "/")
            try:
                sftp.put(local_file, remote_file)
            except Exception as e:
                print(f"Failed to upload {file}: {e}")

def execute_command(client, command, stream_output=False):
    print(f"Exec: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    
    if stream_output:
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                print(stdout.channel.recv(1024).decode(), end="")
            if stderr.channel.recv_ready():
                print(stderr.channel.recv(1024).decode(), end="")

    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        err = stderr.read().decode()
        print(f"Error ({exit_status}): {err}")
        return False
    return True

def main():
    client = create_client()
    sftp = client.open_sftp()
    
    # 1. Upload Code
    upload_files(sftp, LOCAL_DIR, REMOTE_DIR)
    
    # 2. Init Git Repo & Server
    print("Setting up Git Repo...")
    cmds = [
        f"cd {REMOTE_DIR} && git config --global user.email 'admin@example.com'",
        f"cd {REMOTE_DIR} && git config --global user.name 'Admin'",
        f"cd {REMOTE_DIR} && git init",
        f"cd {REMOTE_DIR} && git add .",
        f"cd {REMOTE_DIR} && git commit -m 'Initial commit'",
        f"cd {REMOTE_DIR} && git update-server-info",
        # Allow dumb http transport
        f"cd {REMOTE_DIR} && mv .git/hooks/post-update.sample .git/hooks/post-update || true",
        f"cd {REMOTE_DIR} && chmod a+x .git/hooks/post-update",
        f"cd {REMOTE_DIR} && git update-server-info",
        # Kill old python server
        "pkill -f http.server || true",
        # Start new server on port 3000 pointing to the ROOT of the repo
        f"cd {REMOTE_DIR} && nohup python3 -m http.server 3000 > /dev/null 2>&1 &"
    ]
    
    for cmd in cmds:
        execute_command(client, cmd)

    # 3. Update Repo URL in the Manifests
    print("Updating Repo URL in manifests...")
    # Escape for sed: / becomes \/
    target_url_sed = REPO_URL.replace("/", "\\/") 
    old_url_sed = "https://github.com/my-org/erpnext-gitops.git".replace("/", "\\/")
    
    # Using python to replace is safer than sed complexity via SSH, but let's stick to sed
    # We replace in all yaml files
    sed_cmd = f"grep -rl '{old_url_sed}' {REMOTE_DIR} | xargs sed -i 's/{old_url_sed}/{target_url_sed}/g'"
    execute_command(client, sed_cmd)
    
    # 4. Apply Bootstrap
    # NOTE: K3s typically puts kubeconfig in /etc/rancher/k3s/k3s.yaml readable only by root
    # We use sudo. 
    print("Applying Bootstrap...")
    execute_command(client, f"sudo kubectl apply -f {REMOTE_DIR}/bootstrap.yaml")
    
    print("Deployment triggered! Access Argo CD to verify.")
    client.close()

if __name__ == "__main__":
    main()
