#!/usr/bin/env python3
import argparse
import requests


def main():
    parser = argparse.ArgumentParser(description="List studies/series in Orthanc and print DICOMweb series paths")
    parser.add_argument('--orthanc', default='http://localhost:8042', help='Orthanc base URL')
    parser.add_argument('--dicomweb-root', default='http://localhost:8042/dicom-web', help='DICOMweb root URL')
    args = parser.parse_args()

    # List studies via Orthanc REST
    studies = requests.get(f"{args.orthanc.rstrip('/')}/studies").json()
    if not studies:
        print("No studies found.")
        return

    for sid in studies:
        study = requests.get(f"{args.orthanc.rstrip('/')}/studies/{sid}").json()
        study_uid = study.get('MainDicomTags', {}).get('StudyInstanceUID')
        print(f"Study UID: {study_uid}")
        series_ids = study.get('Series', [])
        for ser_id in series_ids:
            series = requests.get(f"{args.orthanc.rstrip('/')}/series/{ser_id}").json()
            series_uid = series.get('MainDicomTags', {}).get('SeriesInstanceUID')
            # DICOMweb series path
            series_path = f"studies/{study_uid}/series/{series_uid}"
            print(f"  Series UID: {series_uid}")
            print(f"  DICOMweb series URL: {args.dicomweb_root.rstrip('/')}/{series_path}")
            print(f"  Viewer proxy series path: /dicom/{series_path}")


if __name__ == '__main__':
    main()

