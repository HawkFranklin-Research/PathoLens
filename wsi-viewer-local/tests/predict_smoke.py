#!/usr/bin/env python3
import os
import sys
import json
import requests


def get_any_series(orthanc_base: str):
    studies = requests.get(f"{orthanc_base.rstrip('/')}/studies").json()
    if not studies:
        return None
    for sid in studies:
        study = requests.get(f"{orthanc_base.rstrip('/')}/studies/{sid}").json()
        study_uid = study.get('MainDicomTags', {}).get('StudyInstanceUID')
        for ser_id in study.get('Series', []):
            series = requests.get(f"{orthanc_base.rstrip('/')}/series/{ser_id}").json()
            series_uid = series.get('MainDicomTags', {}).get('SeriesInstanceUID')
            insts = series.get('Instances', [])
            if insts:
                inst_id = insts[0]
                inst = requests.get(f"{orthanc_base.rstrip('/')}/instances/{inst_id}").json()
                instance_uid = inst.get('MainDicomTags', {}).get('SOPInstanceUID')
                return study_uid, series_uid, instance_uid
    return None


def main():
    viewer = os.environ.get('VIEWER_URL', 'http://localhost:8081')
    orthanc = os.environ.get('ORTHANC_URL', 'http://localhost:8042')

    any_series = get_any_series(orthanc)
    if not any_series:
        print('No series found in Orthanc. Import data first.')
        sys.exit(1)

    study_uid, series_uid, instance_uid = any_series
    body = {
        "instances": [
            {
                "dicom_path": {"series_path": f"/dicom/studies/{study_uid}/series/{series_uid}"},
                "instance_uids": [instance_uid],
                "patch_coordinates": [
                    {"x_origin": 0, "y_origin": 0, "width": 448, "height": 448}
                ]
            }
        ]
    }
    r = requests.post(f"{viewer.rstrip('/')}/predict", json=body)
    r.raise_for_status()
    data = r.json()
    preds = data.get('predictions', [])
    if not preds:
        print('No predictions in response')
        sys.exit(1)
    emb = preds[0].get('result', {}).get('patch_embeddings', [])
    if not emb or not isinstance(emb[0].get('embedding_vector'), list):
        print('Missing embedding_vector')
        sys.exit(1)
    print('Predict smoke test passed.')


if __name__ == '__main__':
    main()

