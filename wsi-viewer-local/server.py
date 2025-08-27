import os
import json
import http
from typing import Optional

from flask import Flask, Response, abort, request
from flask_cors import CORS
import requests

try:
    # Optional auth support if SERVICE_ACC_KEY is provided
    import datetime
    from google.oauth2 import service_account
    import google.auth.transport.requests
except Exception:
    service_account = None  # Auth not required unless env provided


def _make_credentials() -> Optional["service_account.Credentials"]:
    secret_key_json = os.environ.get("SERVICE_ACC_KEY")
    if not secret_key_json or not service_account:
        return None
    try:
        info = json.loads(secret_key_json)
        return service_account.Credentials.from_service_account_info(
            info, scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
    except Exception:
        return None


def _refresh(creds: "service_account.Credentials") -> "service_account.Credentials":
    if not creds:
        return None
    req = google.auth.transport.requests.Request()
    # refresh if near expiry
    if creds.expiry:
        expiry_time = creds.expiry.replace(tzinfo=datetime.timezone.utc)
        if (expiry_time - datetime.datetime.now(datetime.timezone.utc)) < datetime.timedelta(minutes=5):
            creds.refresh(req)
    else:
        creds.refresh(req)
    return creds


def create_app() -> Flask:
    app = Flask(__name__, static_folder='web', static_url_path='')
    CORS(app)

    DICOM_SERVER_URL = os.environ.get("DICOM_SERVER_URL", "")
    creds = _make_credentials()

    @app.route('/')
    def index():
        # Serve the simplified shell by default to bypass onboarding
        try:
            with open('shell.html', 'r') as f:
                return Response(f.read(), mimetype='text/html')
        except FileNotFoundError:
            abort(http.HTTPStatus.NOT_FOUND)

    @app.route('/osd')
    def osd_page():
        try:
            with open(os.path.join('osd', 'index.html'), 'r') as f:
                return Response(f.read(), mimetype='text/html')
        except FileNotFoundError:
            abort(http.HTTPStatus.NOT_FOUND)

    @app.route('/shell')
    def shell_page():
        try:
            with open('shell.html', 'r') as f:
                return Response(f.read(), mimetype='text/html')
        except FileNotFoundError:
            abort(http.HTTPStatus.NOT_FOUND)

    @app.route('/dicom/<path:url_path>', methods=['GET'])
    def dicom_proxy(url_path: str):
        if not DICOM_SERVER_URL:
            abort(http.HTTPStatus.BAD_REQUEST, "DICOM_SERVER_URL is not set.")

        full_url = f"{DICOM_SERVER_URL.rstrip('/')}/{url_path}"
        headers = {}

        # If creds available, attach Bearer token
        token = None
        if creds:
            _refresh(creds)
            token = creds.token
        elif os.environ.get('BEARER_TOKEN'):
            token = os.environ['BEARER_TOKEN']

        if token:
            headers['Authorization'] = f"Bearer {token}"

        try:
            r = requests.get(full_url, params=request.args, headers=headers, timeout=60)
            r.raise_for_status()
            content_type = r.headers.get('Content-Type', 'application/octet-stream')
            return Response(r.content, status=r.status_code, content_type=content_type)
        except requests.RequestException as e:
            abort(http.HTTPStatus.BAD_GATEWAY, f"Proxy error: {e}")

    from predict_medsiglip import MedSigLIPPredictor
    predictor: Optional[MedSigLIPPredictor] = None

    def _ensure_predictor():
        nonlocal predictor
        if predictor is None:
            predictor = MedSigLIPPredictor()

    def _bearer_token():
        token = None
        if creds:
            _refresh(creds)
            token = creds.token
        elif os.environ.get('BEARER_TOKEN'):
            token = os.environ['BEARER_TOKEN']
        return token

    def _rewrite_series_path(path: str) -> str:
        # Allow viewer to send "/dicom/..." and rewrite to actual DICOMweb
        if path.startswith('/dicom/'):
            base = DICOM_SERVER_URL.rstrip('/')
            return f"{base}/{path[len('/dicom/'):]}"
        # If pointing to this server origin (e.g., http://localhost:8081/dicom/..), rewrite too
        if DICOM_SERVER_URL and f"/dicom/" in path and "://" in path:
            try:
                prefix, after = path.split('/dicom/', 1)
                return f"{DICOM_SERVER_URL.rstrip('/')}/{after}"
            except ValueError:
                return path
        return path

    @app.route('/predict', methods=['POST'])
    def predict_route():
        _ensure_predictor()
        try:
            body = request.get_json(force=True, silent=False)
        except Exception:
            abort(http.HTTPStatus.BAD_REQUEST, 'Invalid JSON')

        if not isinstance(body, dict) or 'instances' not in body:
            abort(http.HTTPStatus.BAD_REQUEST, 'Missing instances')

        # Rewrite series_path for each instance if needed
        for inst in body['instances']:
            d = inst.get('dicom_path') or inst
            if 'series_path' in d and isinstance(d['series_path'], str):
                d['series_path'] = _rewrite_series_path(d['series_path'])

        token = _bearer_token()
        try:
            result = predictor.predict(body, token)  # type: ignore[arg-type]
        except Exception as e:
            abort(http.HTTPStatus.INTERNAL_SERVER_ERROR, f"Prediction error: {e}")

        # Return JSON directly (optionally gzip in future)
        return Response(json.dumps(result), status=200, content_type='application/json')

    return app


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8081'))
    app = create_app()
    app.run(host='0.0.0.0', port=port, debug=True)
