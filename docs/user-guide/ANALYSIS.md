# Analysis Platform Guide

ADCP Recorder provides a comprehensive analysis platform consisting of a high-performance **FastAPI** backend and an interactive **Streamlit** dashboard.

## 🚀 FastAPI Backend

The backend provides programmatic access to your data, allowing for custom integrations and large-scale data processing.

### Accessing the API

By default, the API is available at `http://localhost:8000`. You can access the interactive Swagger documentation at `http://localhost:8000/docs`.

### Key Endpoints

- `GET /records`: Retrieve raw logs with metadata and parse status.
- `GET /errors`: Monitor parsing failures across all ADCP message types.
- `GET /ducklake/{prefix}`: Query structured records directly from the Parquet data lake.

### Example: Custom Python Client

```python
import requests

# Get recent sensor data
response = requests.get("http://localhost:8000/ducklake/pnors?limit=10")
data = response.json()

for record in data:
    print(f"Time: {record['recorded_at']}, Temp: {record['temperature']}°C")
```

## 📊 Streamlit Dashboard

The dashboard provides a visual interface for exploring your data without writing code.

### Launching the Dashboard

Run the following command in your terminal:

```bash
streamlit run adcp_recorder/ui/dashboard.py
```

### Features

- **Profile Browser**: Select different record types (velocity, sensor data, waves) to view historical trends.
- **Error Tracking**: Visualize parsing errors and identify unhealthy instrument connections.
- **Real-time Refresh**: Manually refresh DuckLake views to incorporate the latest recorded data.

## 🌊 DuckLake Concept

The platform utilizes a **DuckLake** architecture:

- **DuckDB** handle transactional logging and fast metadata queries.
- **Parquet** handles the heavy lifting of structured sensor data storage.
- The two are merged via **DuckDB Views**, providing you with a unified SQL interface over all your data.

---

[🏠 Back to Docs](../README.md)
