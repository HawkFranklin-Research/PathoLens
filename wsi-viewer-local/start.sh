#!/usr/bin/env bash
set -euo pipefail

# Ensure Orthanc data dirs exist
mkdir -p /data/db /data/import

echo "Starting Orthanc..."
orthanc /etc/orthanc/orthanc.json &

echo "Starting Flask viewer on port ${PORT:-8080}..."
exec python3 /app/server.py

