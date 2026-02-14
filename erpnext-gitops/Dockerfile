FROM frappe/erpnext:v15-debian

USER root
# Install git if needed to fetch apps
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

USER frappe
WORKDIR /home/frappe/frappe-bench

# If you have local apps, uncomment the next line:
# COPY --chown=frappe:frappe apps /home/frappe/frappe-bench/apps

# Install custom apps
# Example:
# RUN bench get-app healthcare
# RUN bench get-app https://github.com/myuser/myapp.git

# Since we don't know the app URLs yet, this is a placeholder.
# PLEASE EDIT THIS FILE to add your apps.
