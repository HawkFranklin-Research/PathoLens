#!/usr/bin/env python3
"""
Download public DICOM WSI files and import into Orthanc.

Usage examples:
  python scripts/download_sample_wsi.py \
    --dest orthanc/import \
    --urls https://example.com/pathology_wsi_1.dcm https://example.com/pathology_wsi_2.dcm

  python scripts/download_sample_wsi.py --manifest urls.txt --dest orthanc/import

Notes:
- You must supply valid URLs. This script does not bundle sample data.
- After download, files are imported to Orthanc using REST /instances.
"""

import argparse
import os
import sys
from urllib.parse import urlparse
import requests


def download(url: str, dest_folder: str) -> str:
    os.makedirs(dest_folder, exist_ok=True)
    name = os.path.basename(urlparse(url).path) or 'file.dcm'
    out = os.path.join(dest_folder, name)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(out, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    print(f"Downloaded: {url} -> {out}")
    return out


def import_to_orthanc(orthanc_url: str, path: str) -> None:
    with open(path, 'rb') as f:
        r = requests.post(f"{orthanc_url.rstrip('/')}/instances", data=f, headers={'Expect': ''})
    r.raise_for_status()
    print(f"Imported to Orthanc: {path}")


def main():
    parser = argparse.ArgumentParser(description='Download and import WSI DICOM to Orthanc')
    parser.add_argument('--orthanc', default='http://localhost:8042', help='Orthanc base URL')
    parser.add_argument('--dest', default='orthanc/import', help='Destination download folder')
    parser.add_argument('--urls', nargs='*', default=None, help='One or more HTTPS URLs to .dcm files')
    parser.add_argument('--manifest', default=None, help='Text file with one URL per line')
    parser.add_argument('--no-import', action='store_true', help='Skip importing to Orthanc')
    args = parser.parse_args()

    urls = []
    if args.urls:
        urls.extend(args.urls)
    if args.manifest:
        with open(args.manifest, 'r') as f:
            for line in f:
                u = line.strip()
                if u and not u.startswith('#'):
                    urls.append(u)

    if not urls:
        print('No URLs provided. Provide with --urls or --manifest.')
        print('Tip: Some public sources host DICOM WSI (pathology) samples. Replace with valid links you have access to.')
        sys.exit(2)

    downloaded = [download(u, args.dest) for u in urls]

    if not args.no_import:
        for p in downloaded:
            import_to_orthanc(args.orthanc, p)


if __name__ == '__main__':
    main()

