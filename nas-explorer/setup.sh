#!/bin/bash
set -e

echo "========================================="
echo "  NAS Explorer - Setup Script"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "  -> Please edit .env with your settings before proceeding."
    echo ""
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    echo "  https://docs.docker.com/engine/install/"
    exit 1
fi

# Check for docker-compose
if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed."
    exit 1
fi

echo ""
echo "Step 1: Mount your Synology NAS"
echo "================================"
echo ""
echo "If not already mounted, run:"
echo ""
echo "  sudo mkdir -p /mnt/nas"
echo "  sudo mount -t cifs -o ro,username=YOUR_USER,password=YOUR_PASS \\"
echo "    //YOUR_NAS_IP/YOUR_SHARE /mnt/nas"
echo ""
echo "For permanent mount, add to /etc/fstab:"
echo "  //YOUR_NAS_IP/YOUR_SHARE /mnt/nas cifs ro,username=YOUR_USER,password=YOUR_PASS,uid=1000,gid=1000 0 0"
echo ""

# Check if NAS is mounted
if [ -d "/mnt/nas" ]; then
    file_count=$(ls /mnt/nas 2>/dev/null | wc -l)
    if [ "$file_count" -gt 0 ]; then
        echo "  ✓ NAS appears to be mounted at /mnt/nas ($file_count items visible)"

        # Check if read-only
        if touch /mnt/nas/.nas_explorer_test 2>/dev/null; then
            rm -f /mnt/nas/.nas_explorer_test
            echo "  ⚠ WARNING: NAS is mounted read-WRITE. Remount with 'ro' flag for safety!"
        else
            echo "  ✓ NAS is mounted read-only"
        fi
    else
        echo "  ⚠ /mnt/nas exists but appears empty. Mount your NAS before scanning."
    fi
else
    echo "  ⚠ /mnt/nas does not exist. Create it and mount your NAS."
fi

echo ""
echo "Step 2: Build and Start"
echo "======================="
echo ""
echo "Starting NAS Explorer..."
docker compose build
docker compose up -d

echo ""
echo "========================================="
echo "  NAS Explorer is running!"
echo "========================================="
echo ""
echo "  Web UI:  http://localhost:${PORT:-8000}"
echo "  API:     http://localhost:${PORT:-8000}/api/admin/health"
echo ""
echo "  Next steps:"
echo "  1. Open the web UI in your browser"
echo "  2. Click 'Scan Now' to index your NAS"
echo "  3. Browse, search, and explore your files!"
echo ""
echo "  To stop:  docker compose down"
echo "  To view logs: docker compose logs -f"
echo ""
