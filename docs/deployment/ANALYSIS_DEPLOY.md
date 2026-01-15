# API & Dashboard Deployment

This guide covers the deployment of the analysis components (FastAPI and Streamlit) for production or remote monitoring.

## 🛠️ FastAPI Deployment (Production)

For production environments, we recommend using **Gunicorn** with **Uvicorn** workers or running via **Docker**.

### Using Uvicorn

```bash
uvicorn adcp_recorder.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Systemd Service (Linux)

You can run the API as a background service:

```ini
[Unit]
Description=ADCP Recorder API
After=network.target

[Service]
User=adcp
Group=adcp
WorkingDirectory=/opt/adcp-recorder
ExecStart=/opt/adcp-recorder/.venv/bin/uvicorn adcp_recorder.api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Windows Service (Servy)

Register the API as a Windows service using the provided script:

1. Open a terminal as **Administrator**.
2. Run: `scripts\install-analysis-windows.bat`.

Alternatively, use `servy-cli` manually:

```powershell
servy-cli install --name="ADCP-API" --path="C:\Program Files\ADCP-Recorder\venv\Scripts\uvicorn.exe" --params="adcp_recorder.api.main:app --host 0.0.0.0 --port 8000"
```

## 📊 Streamlit Deployment

Streamlit can be deployed behind a reverse proxy like **Nginx** for SSL and domain management.

### Windows Service for Dashboard (Servy)

The `scripts\install-analysis-windows.bat` script also installs the dashboard as a service. To do it manually:

```powershell
servy-cli install --name="ADCP-Dashboard" --path="C:\Program Files\ADCP-Recorder\venv\Scripts\streamlit.exe" --params="run adcp_recorder/ui/dashboard.py --server.port 8501 --server.address 0.0.0.0"
```

### Example Nginx Config

```nginx
server {
    listen 80;
    server_name dashboard.adcp.local;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Resource Considerations

- **Memory**: DuckDB and Parquet processing can be memory-intensive. Ensure the host has at least 4GB of RAM for the Analysis platform.
- **Storage**: Parquet files are compressed, but high-throughput recording (e.g., 8Hz) can still generate significant data over months. Use dedicated storage volumes if possible.

---

[🏠 Back to Docs](../README.md)
