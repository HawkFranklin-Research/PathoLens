#!/usr/bin/env python3
import os
import sys
import requests


def main():
    base = os.environ.get('ORTHANC_URL', 'http://localhost:8042')
    r = requests.get(f"{base.rstrip('/')}/dicom-web")
    if r.status_code != 200:
        print(f"Unexpected status: {r.status_code}")
        sys.exit(1)
    print("Orthanc DICOMweb reachable.")


if __name__ == '__main__':
    main()

