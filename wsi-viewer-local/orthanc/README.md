Local Orthanc (DICOMweb)

What this is
- Dockerized Orthanc with DICOMweb enabled at http://localhost:8042/dicom-web
- CORS open for local development, auth disabled (dev only)

Prereqs
- Docker and Docker Compose installed

Run
1) cd ../wsi-viewer-local/orthanc
2) mkdir -p data import
3) docker compose up -d
4) Verify:
   - Orthanc UI: http://localhost:8042/
   - DICOMweb root: http://localhost:8042/dicom-web

Point the viewer to Orthanc
- In another terminal:
  - cd ../wsi-viewer-local
  - export DICOM_SERVER_URL="http://localhost:8042/dicom-web"
  - python server.py
  - Open http://localhost:8081 and use /dicom/... or paste the Orthanc DICOMweb URL in the form.

Import DICOM (optional)
- Drop .dcm files into ./import or use curl to POST:
  curl -X POST -H "Expect:" --data-binary @/path/to/file.dcm \
    http://localhost:8042/instances

Download and import a sample WSI
- Provide URLs to DICOM WSI files you have access to and run:
  python ../scripts/download_sample_wsi.py --dest import --urls https://example.com/slide1.dcm https://example.com/slide2.dcm
- Or use a manifest file listing one URL per line:
  python ../scripts/download_sample_wsi.py --dest import --manifest urls.txt
- The script downloads into `orthanc/import` and automatically imports to Orthanc (disable with --no-import).

Notes
- For Whole Slide Images (WSI), you need DICOM WSI objects. If you don’t have any locally, you can still verify Orthanc works, but the viewer’s WSI tools are best exercised with DICOM WSI data (e.g., slides converted to DICOM).
- This config disables authentication and enables wide-open CORS strictly for local development.
