FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# - openbabel: format conversions
# - autodock-vina: molecular docking executor
# - libpq-dev: postgres driver compilation
# - libxrender1, libxext6: required by RDKit
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    openbabel \
    autodock-vina \
    libxrender1 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Ensure AutoDock Vina binary alias exists in path
# On some Debian packages, it is named autodock-vina, let's create a symlink
RUN if [ -f /usr/bin/autodock-vina ]; then ln -sf /usr/bin/autodock-vina /usr/bin/vina; fi

WORKDIR /code

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose backend API port
EXPOSE 8000
