FROM orthancteam/orthanc-plugins:latest

# Install Python, pip, and native libs for conversion
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-venv libopenslide0 && \
    rm -rf /var/lib/apt/lists/*

ENV APP_DIR=/app \
    ORTHANC_DB=/data/db \
    ORTHANC_IMPORT=/data/import \
    PORT=8080 \
    DICOM_SERVER_URL=http://127.0.0.1:8042/dicom-web \
    MEDSIGLIP_MODEL_DIR=/app/models/medsiglip-448

WORKDIR ${APP_DIR}

# Copy app files
COPY requirements.txt requirements.txt
COPY requirements-converter.txt requirements-converter.txt
RUN pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir -r requirements-converter.txt

COPY web ./web
COPY osd ./osd
COPY server.py shell.html predict_medsiglip.py ./
RUN mkdir -p ${MEDSIGLIP_MODEL_DIR}
COPY orthanc/orthanc.json /etc/orthanc/orthanc.json
COPY orthanc/query_series.py orthanc/import_dicom.py ./orthanc/
COPY scripts ./scripts

# Create data dirs inside container (host will bind-mount /data)
RUN mkdir -p ${ORTHANC_DB} ${ORTHANC_IMPORT}

EXPOSE 8042 8080

# Start both Orthanc and Flask app
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/start.sh"]
