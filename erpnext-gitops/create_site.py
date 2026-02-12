import paramiko
import time
import sys

SERVER_IP = "173.208.208.91"
USERNAME = "administrator"
PASSWORD = "Xatuute13@@"

def run_sudo(ssh, cmd):
    print(f"🔄 Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(f"sudo -S {cmd}", get_pty=True)
    stdin.write(f"{PASSWORD}\n")
    stdin.flush()
    
    output = ""
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            chunk = stdout.channel.recv(1024).decode('utf-8')
            output += chunk
            sys.stdout.write(chunk)
            sys.stdout.flush()
    
    if stdout.channel.recv_ready():
        chunk = stdout.channel.recv(1024).decode('utf-8')
        output += chunk
        sys.stdout.write(chunk)
    
    print("\n")
    return output

def main():
    print(f"🔗 Connecting to {SERVER_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(SERVER_IP, username=USERNAME, password=PASSWORD)
        print("✅ Connected!")
        
        # 1. Get Pod Name
        print("\n🔍 Finding Pod...")
        out = run_sudo(ssh, "kubectl get pods -n erpnext-dev -o jsonpath='{.items[0].metadata.name}'")
        pod_name = out.strip().split('\r\n')[-1].strip() # Handle potential sudo output noise
        
        # Clean up pod name if it contains password prompt or other noise
        if "password" in pod_name.lower():
            # Try to extract the pod name which usually starts with erpnext-
            import re
            match = re.search(r'(erpnext-[a-zA-Z0-9-]+)', out)
            if match:
                pod_name = match.group(1)
            else:
                print("❌ Could not find pod name!")
                return

        print(f"✅ Found Pod: {pod_name}")

        # 2. Create apps.txt inside pod
        print("\n📝 Creating apps.txt inside pod...")
        apps = [
            "frappe", "erpnext", "healthcare", "his", "hrms", 
            "insights", "rasiin_design", "rasiin_hr", "frappe_whatsapp"
        ]
        
        create_apps_cmd = " > sites/apps.txt && ".join([f"echo '{app}' >> sites/apps.txt" for app in apps])
        # Fix the first echo to use > instead of >> for implicit first line logic handling if needed, 
        # but easier to just clear it first
        
        full_cmd = f"cd /home/frappe/frappe-bench && echo '{apps[0]}' > sites/apps.txt"
        for app in apps[1:]:
            full_cmd += f" && echo '{app}' >> sites/apps.txt"
            
        run_sudo(ssh, f"kubectl exec -n erpnext-dev {pod_name} -- bash -c \"{full_cmd}\"")
        print("✅ apps.txt created.")

        # 3. Create Site
        print("\n🚀 Creating Site (this might take a few minutes)...")
        site_cmd = """
        bench new-site dev.erp.local \
        --mariadb-root-password changeme123 \
        --admin-password admin \
        --install-app erpnext \
        --install-app healthcare \
        --install-app his \
        --install-app hrms \
        --install-app insights \
        --install-app rasiin_design \
        --install-app rasiin_hr \
        --install-app frappe_whatsapp \
        --force
        """
        # Collapse whitespace
        site_cmd = " ".join(site_cmd.split())
        
        run_sudo(ssh, f"kubectl exec -n erpnext-dev {pod_name} -- bash -c \"cd /home/frappe/frappe-bench && {site_cmd}\"")
        
        print("\n✅ Site creation completed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
