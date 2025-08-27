WSI Viewer (Local)

This folder contains two options to run a Whole Slide Image viewer locally:

- `web/` (compiled Angular viewer from the original repo) served by a tiny Flask app. It expects a DICOMweb endpoint (you can proxy via `/dicom/...`).
- `osd/` an OpenSeadragon demo page that loads a public DeepZoom (DZI) tile source.

Prerequisites
- Python 3.10+

Install
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the Angular viewer bundle
```
export PORT=8081
# Optional for private DICOMweb (Google):
# export SERVICE_ACC_KEY='{"type":"service_account",...}'
# Or provide a raw token:
# export BEARER_TOKEN=ya29....
# Set your DICOMweb base if you want to proxy via /dicom/...:
# export DICOM_SERVER_URL="https://healthcare.googleapis.com/v1/projects/.../dicomStores/.../dicomWeb"
python server.py
```
Then open:
- Angular viewer: http://localhost:8081
  - Use the form to paste your DICOMweb store URL or series URL. If you exported `DICOM_SERVER_URL`, you can enter paths that start with `/dicom/...` to use the local proxy.

Run the OpenSeadragon demo
- Open `osd/index.html` directly in a browser, or serve it from any static server. It loads a sample DeepZoom image by default; change the URL and click Load.

Notes
- The `web/` folder is a compiled viewer; source code is not included here.
- The `/dicom/...` proxy attaches an Authorization header if `SERVICE_ACC_KEY` (Google service account JSON) or `BEARER_TOKEN` is set; otherwise it forwards without auth.
- For a fully offline WSI demo without DICOMweb, use the OpenSeadragon page with a public DZI tile source.

Working with the local Orthanc
- Start Orthanc: see `orthanc/README.md` (Docker Compose, CORS enabled, auth disabled for dev).
- Import DICOM files:
  - `python orthanc/import_dicom.py --path /path/to/folder_or_file`
  - Or copy .dcm files into `orthanc/import` and use curl to POST to `/instances`.
- Find series UIDs and build viewer paths:
  - `python orthanc/query_series.py` prints DICOMweb URLs and viewer proxy paths like `/dicom/studies/<StudyUID>/series/<SeriesUID>`.
  - Use the printed `/dicom/...` path directly in the viewer form, or paste the full `http://localhost:8042/dicom-web/...` URL.

Download and import a sample WSI
- Provide URLs to public DICOM WSI files you have access to (this project does not bundle data), then run:
  - `python scripts/download_sample_wsi.py --dest orthanc/import --urls https://example.com/slide1.dcm https://example.com/slide2.dcm`
- Or put URLs into a text file (one per line) and run:
  - `python scripts/download_sample_wsi.py --dest orthanc/import --manifest urls.txt`
- The script downloads into `orthanc/import` and imports to Orthanc via REST.

Testing /predict with MedSigLIP
- Edit `examples/predict_example.json` and replace `REPLACE_*` with the UIDs from `orthanc/query_series.py` and a valid `instance_uids[0]`.
- Call:
  - `bash examples/call_predict.sh` (uses http://localhost:8081/predict)
- Response contains `predictions[0].result.patch_embeddings` with vectors per patch.

Testing (smoke checks)
- Orthanc reachable:
  - `python tests/ping_orthanc.py` (ORTHANC_URL can be overridden via env)
- Predict route end-to-end (requires at least one series and model weights):
  - `python tests/predict_smoke.py`
  - Ensures /predict returns an embedding_vector for a small patch.

WSI conversion (optional)
- If you have non-DICOM WSIs (e.g., SVS, TIFF) and want to convert them locally:
  - Install native dependency:
    - macOS: `brew install openslide`
    - Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y libopenslide0`
  - Install Python deps:
    - `pip install -r requirements-converter.txt`
  - Convert and import to Orthanc:
    - `python scripts/convert_wsi_to_dicom.py --input /path/to/slide.svs --outdir orthanc/import --orthanc http://localhost:8042`
  - Then discover the series path:
    - `python orthanc/query_series.py` and paste `/dicom/studies/<StudyUID>/series/<SeriesUID>` into the viewer.

How to run everything in one Docker

- Build image:
  - `cd ../wsi-viewer-local`
  - `docker build -t wsi-allinone .`
- Run container with your local folder mounted:
  - `docker run --rm -it -p 8080:8080 -p 8042:8042 -v /absolute/path/to/wsi-data:/data wsi-allinone`
  - `/data` will contain:
    - `/data/db` (Orthanc storage)
    - `/data/import` (drop .dcm here to auto-import via scripts)
    - You can also point the converter at `/data/import` to output DICOM WSIs.
- Open the UI:
  - http://localhost:8080
  - This is the simplified shell: enter your `/dicom/studies/<StudyUID>/series/<SeriesUID>` to open directly.
  - OSD demo is also served: http://localhost:8080/osd

Convert your .svs to DICOM WSI inside the container (recommended)

- Ensure your .svs files are in the host folder you mounted at `/data` (e.g., `/absolute/path/to/wsi-data`).
- In another terminal:
  - `docker exec -it $(docker ps -qf name=wsi-allinone) bash`
  - Or start the container with a name (`--name wsi-allinone`) and then: `docker exec -it wsi-allinone bash`
- Inside the container:
  - `cd /app`
  - Convert one file:
    - `python scripts/convert_wsi_to_dicom.py --input /data/your_slide.svs --outdir /data/import --orthanc http://127.0.0.1:8042`
- Convert all .svs in a folder (quick loop):
  - `for f in /data/*.svs; do python scripts/convert_wsi_to_dicom.py --input "$f" --outdir /data/import --orthanc http://127.0.0.1:8042; done`
- Find the series path:
  - `python orthanc/query_series.py`
  - Copy a “Viewer proxy series path” like `/dicom/studies/<StudyUID>/series/<SeriesUID>`
- Open it:
  - `http://localhost:8080/shell?series=/dicom/studies/<StudyUID>/series/<SeriesUID>`

If you prefer to avoid docker exec for conversion

- You can install converter deps on your host (OpenSlide + `requirements-converter.txt`) and run:
  - `python scripts/convert_wsi_to_dicom.py --input /absolute/path/to/slide.svs --outdir /absolute/path/to/wsi-data/import --orthanc http://localhost:8042`
  - The container sees those files via the bind mount.

Notes and troubleshooting

- Why Orthanc + viewer: The viewer needs DICOMweb. Orthanc is the simplest way to provide a full DICOMweb service locally. This Docker image bundles both so you don’t need multiple services.
- Ports:
  - Viewer: http://localhost:8080
  - Orthanc UI: http://localhost:8042 (useful to verify data)
- The shell view vs compiled app:
  - The original Angular app is compiled. The shell page wraps it and bypasses onboarding by opening the `/viewer` route directly with your series.
- Apple Silicon:
  - If Orthanc fails to start on M-series Macs, run the container with: `--platform=linux/amd64`
- First /predict call:
  - Downloads MedSigLIP weights inside the container; the first call may take some minutes.

Quick commands recap

- `docker build -t wsi-allinone .`
- `docker run --rm -it -p 8080:8080 -p 8042:8042 -v /abs/path/to/wsi-data:/data --name wsi-allinone wsi-allinone`
- `docker exec -it wsi-allinone bash`
  - `python scripts/convert_wsi_to_dicom.py --input /data/your_slide.svs --outdir /data/import --orthanc http://127.0.0.1:8042`
  - `python orthanc/query_series.py`
- Open `http://localhost:8080/shell?series=/dicom/studies/<StudyUID>/series/<SeriesUID>`
