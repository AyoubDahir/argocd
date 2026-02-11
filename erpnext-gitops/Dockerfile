# syntax=docker/dockerfile:1

# Multi-stage build for custom ERPNext with custom apps
ARG FRAPPE_VERSION=v14.0.0
ARG ERPNEXT_VERSION=v14.0.0
ARG PYTHON_VERSION=3.11
ARG NODE_VERSION=18

################################################################################
# Base stage - Install system dependencies
################################################################################
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    # Required for building Python packages
    gcc g++ make \
    # Frappe dependencies
    git curl wget \
    libffi-dev python3-dev python3-venv \
    libpq-dev mariadb-client \
    redis-tools \
    # Additional dependencies
    wkhtmltopdf \
    fonts-cantarell \
    xfonts-75dpi xfonts-base \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
ARG NODE_VERSION
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn \
    && rm -rf /var/lib/apt/lists/*

################################################################################
# Builder stage - Build Frappe bench with all apps
################################################################################
FROM base AS builder

ARG FRAPPE_VERSION
ARG ERPNEXT_VERSION

WORKDIR /home/frappe

# Install bench
RUN pip install --no-cache-dir frappe-bench \
    && bench init --version ${FRAPPE_VERSION} --frappe-branch ${FRAPPE_VERSION} \
    --python $(which python3) frappe-bench

WORKDIR /home/frappe/frappe-bench

# Get ERPNext
RUN bench get-app --branch ${ERPNEXT_VERSION} erpnext

# Get custom apps from your repository
# Note: These will be cloned from the fullii repository
RUN bench get-app https://github.com/AyoubDahir/fullii.git --resolve-deps

# Note: The fullii repo contains multiple apps as subdirectories
# We need to install each one individually
WORKDIR /home/frappe/frappe-bench/apps

# Clone the fullii repository
RUN git clone --depth 1 https://github.com/AyoubDahir/fullii.git fullii-repo

# Move each app to the apps directory
RUN cp -r fullii-repo/healthcare . && \
    cp -r fullii-repo/his . && \
    cp -r fullii-repo/hrms . && \
    cp -r fullii-repo/insights . && \
    cp -r fullii-repo/rasiin_design . && \
    cp -r fullii-repo/rasiin_hr . && \
    cp -r fullii-repo/frappe_whatsapp . && \
    rm -rf fullii-repo

WORKDIR /home/frappe/frappe-bench

# Install all apps' Python dependencies
RUN for app in apps/*; do \
    if [ -f "$app/requirements.txt" ]; then \
    pip install --no-cache-dir -r "$app/requirements.txt"; \
    fi; \
    done

# Build assets
RUN bench build --production

################################################################################
# Runtime stage - Create lean production image
################################################################################
FROM base AS runtime

# Create frappe user
RUN useradd -ms /bin/bash frappe

# Copy bench from builder
COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FRAPPE_SITE_NAME=site1.localhost

# Expose port
EXPOSE 8000 9000 6787

USER frappe

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/method/ping || exit 1

# Default command
CMD ["bench", "start"]
