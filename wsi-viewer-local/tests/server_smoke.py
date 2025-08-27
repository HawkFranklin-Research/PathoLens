#!/usr/bin/env python3
"""
Lightweight smoke tests for the WSI viewer Flask app.

These tests avoid external dependencies (Orthanc, model downloads) by
using Flask's test client to verify that core routes are reachable and
return expected content from local static files.
"""

import sys
from pathlib import Path

# Ensure the package root (wsi-viewer-local) is on sys.path
THIS_DIR = Path(__file__).resolve().parent
ROOT = THIS_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import os
os.chdir(str(ROOT))


def main() -> int:
    try:
        # Import without starting the server
        from server import create_app  # type: ignore
    except Exception as e:
        print(f"Failed to import server: {e}")
        return 1

    app = create_app()
    client = app.test_client()

    # Index should serve the shell page
    r = client.get("/")
    if r.status_code != 200:
        print(f"GET / unexpected status: {r.status_code}")
        return 1
    if b"<html" not in r.data or b"Shell" not in r.data:
        print("GET / did not return expected HTML content")
        return 1

    # OSD demo page should be reachable
    r = client.get("/osd")
    if r.status_code != 200:
        print(f"GET /osd unexpected status: {r.status_code}")
        return 1
    if b"<html" not in r.data or b"OpenSeadragon" not in r.data:
        print("GET /osd did not return expected HTML content")
        return 1

    # DICOM proxy should fail without configuration
    r = client.get("/dicom/health")
    if r.status_code == 200:
        print("/dicom/* unexpectedly succeeded without DICOM_SERVER_URL")
        return 1

    print("WSI viewer smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
