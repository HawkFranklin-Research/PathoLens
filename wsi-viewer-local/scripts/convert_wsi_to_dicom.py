#!/usr/bin/env python3
"""
Convert non-DICOM WSI (e.g., SVS, TIFF) to DICOM-WSI and import to Orthanc.

Requirements (install once):
  - pip install -r requirements-converter.txt
Native deps:
  - macOS: brew install openslide
  - Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y libopenslide0

Examples:
  python scripts/convert_wsi_to_dicom.py \
    --input /path/to/slide.svs \
    --outdir orthanc/import \
    --orthanc http://localhost:8042

This uses the wsidicomizer library to produce VL Whole Slide Microscopy DICOM files.
"""

import argparse
import os
import shutil
import subprocess
import sys

import requests


def ensure_tool():
    try:
        import wsidicomizer  # noqa: F401
    except Exception:
        print("wsidicomizer not installed. Install requirements-converter.txt first:")
        print("  pip install -r requirements-converter.txt")
        sys.exit(2)


def run_wsidicomizer(inp: str, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    # Prefer CLI entrypoint if available
    exe = shutil.which('wsidicomizer')
    if exe:
        cmd = [exe, '--out', outdir, inp]
    else:
        # Fallback: try module entrypoint (may not be available in some versions)
        cmd = [sys.executable, '-c', 'import wsidicomizer.cli as c; c.main()', '--out', outdir, inp]
    print('Running:', ' '.join(cmd))
    subprocess.check_call(cmd)


def import_folder(orthanc_url: str, folder: str):
    for root, _dirs, files in os.walk(folder):
        for name in files:
            if name.lower().endswith('.dcm'):
                full = os.path.join(root, name)
                with open(full, 'rb') as f:
                    r = requests.post(f"{orthanc_url.rstrip('/')}/instances", data=f, headers={'Expect': ''})
                    r.raise_for_status()
                print(f"Imported: {full}")


def main():
    parser = argparse.ArgumentParser(description='Convert WSI to DICOM-WSI and import to Orthanc')
    parser.add_argument('--input', required=True, help='Input WSI file (SVS, TIFF, etc.)')
    parser.add_argument('--outdir', default='orthanc/import', help='Output folder for DICOM files')
    parser.add_argument('--orthanc', default='http://localhost:8042', help='Orthanc base URL to import to')
    parser.add_argument('--no-import', action='store_true', help='Skip import into Orthanc')
    args = parser.parse_args()

    ensure_tool()

    # Clear output folder if it contains leftovers from prior conversions
    os.makedirs(args.outdir, exist_ok=True)
    # Keep existing files; wsidicomizer writes into a subfolder per series/study

    run_wsidicomizer(args.input, args.outdir)

    if not args.no_import:
        import_folder(args.orthanc, args.outdir)


if __name__ == '__main__':
    main()
