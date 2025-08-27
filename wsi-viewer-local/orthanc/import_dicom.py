#!/usr/bin/env python3
import argparse
import os
import sys
import requests


def post_file(orthanc_url: str, path: str) -> None:
    with open(path, 'rb') as f:
        r = requests.post(f"{orthanc_url.rstrip('/')}/instances", data=f, headers={'Expect': ''})
        r.raise_for_status()
    print(f"Imported: {path}")


def main():
    parser = argparse.ArgumentParser(description="Import DICOM files into Orthanc via REST")
    parser.add_argument('--orthanc', default='http://localhost:8042', help='Orthanc base URL')
    parser.add_argument('--path', required=True, help='File or folder containing .dcm files')
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Path not found: {args.path}")
        sys.exit(1)

    if os.path.isfile(args.path):
        post_file(args.orthanc, args.path)
        return

    # Walk folder
    count = 0
    for root, _dirs, files in os.walk(args.path):
        for name in files:
            if name.lower().endswith('.dcm'):
                full = os.path.join(root, name)
                post_file(args.orthanc, full)
                count += 1

    print(f"Imported {count} files")


if __name__ == '__main__':
    main()

