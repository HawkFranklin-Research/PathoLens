PathoLens

Overview

- PathoLens is a work-in-progress pathology tooling repo that bundles:
  - `wsi-viewer-local`: a lightweight Flask Web UI and backend for viewing WSIs (via OpenSeadragon) and proxying DICOMweb. It includes a MedSigLIP prediction endpoint as a component.
  - `path-foundation-demo`: a stripped, static copy of Google’s Path Foundation demo assets for reference. All Git history and attributes have been removed.
  - `data/`: local storage for large WSI files (e.g., `.svs`). These are ignored by Git.

Repo Layout

- `wsi-viewer-local/`: Viewer service with Dockerfile, simple server, example scripts, and tests.
- `path-foundation-demo/`: Self-contained demo (static artifacts + minimal server).
- `data/`: Place your `.svs` files here for local experiments (ignored by Git).

Quick Start: WSI Viewer

Option A: Local virtualenv

1) Create and activate a venv

   cd wsi-viewer-local
   python3 -m venv .venv
   source .venv/bin/activate

2) Install dependencies (note: downloads PyTorch/Transformers; this is large)

   pip install -U pip
   pip install -r requirements.txt

3) Run the server

   # Optional: set a DICOMweb endpoint to proxy
   # export DICOM_SERVER_URL="http://localhost:8042/dicom-web"
   export PORT=8081
   python server.py

4) Open the UI

   - Shell page: http://localhost:8081/
   - OpenSeadragon demo: http://localhost:8081/osd

Option B: Docker

From repo root or from `wsi-viewer-local/`:

   docker build -t patholens-viewer ./wsi-viewer-local
   docker run --rm -p 8081:8081 \
     -e PORT=8081 \
     # Optionally, to proxy an Orthanc DICOMweb
     # -e DICOM_SERVER_URL=http://host.docker.internal:8042/dicom-web \
     patholens-viewer

Smoke Tests

The smoke tests validate that the viewer server starts and serves local pages without external dependencies (model downloads, Orthanc) using Flask’s test client.

   cd wsi-viewer-local
   # If you created the venv above:
   . .venv/bin/activate
   python tests/server_smoke.py

Orthanc and DICOM Data (optional)

- An example Orthanc setup is included under `wsi-viewer-local/orthanc/` (with `docker-compose.yml`).
- Scripts to convert WSIs to DICOM and import them are under `wsi-viewer-local/scripts/`.
- Once Orthanc is populated, set `DICOM_SERVER_URL` for the viewer, then exercise the `/predict` endpoint using `examples/` in the same folder.

Notes

- Large WSI files (`.svs`, `.tiff`) are ignored by Git and should be placed in `data/`.
- The `path-foundation-demo` folder is included without its original Git attributes/history, per request.

