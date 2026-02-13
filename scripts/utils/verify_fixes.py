import os
from datetime import datetime, timedelta

from adcp_recorder.config import RecorderConfig
from adcp_recorder.ui.parquet_data_layer import ParquetDataLayer

# Use configured output directory
config = RecorderConfig.load()
data_path = config.output_dir

if not os.path.exists(data_path):
    print(f"Error: {data_path} does not exist.")
    exit(1)

layer = ParquetDataLayer(data_path)

# Load data - this will create views
print("Loading data and creating views...")
layer.load_data()

# Check sources
sources = layer.get_available_sources()
print(f"Available sources: {[s.name for s in sources]}")

# Try to query wave_measurement_full
print("\nAttempting to query wave_measurement_full...")
try:
    if "wave_measurement_full" in [s.name for s in sources]:
        data = layer.query_data("wave_measurement_full", limit=5)
        print(f"Success! Found {len(data)} records in wave_measurement_full.")
        if data:
            print("Sample record keys:", data[0].keys())
            print("measurement_datetime:", data[0].get("measurement_datetime"))
            print("measurement_date:", data[0].get("measurement_date"))
    else:
        print("wave_measurement_full NOT created. Check base views.")
        base_views = [s.name for s in sources if s.name.startswith("pq_")]
        print(f"Base views: {base_views}")
except Exception as e:
    print(f"Failed to query wave_measurement_full: {e}")

# Check PNORWD
print("\nAttempting to query pq_pnorwd...")
try:
    source = layer.get_source_metadata("pq_pnorwd")
    if source:
        print(f"pq_pnorwd has_timestamp: {source.has_timestamp}")
        print(f"pq_pnorwd timestamp_column: {source.timestamp_column}")

        # Try filtering with a very wide range to see if it works
        start_time = datetime(2020, 1, 1)
        data = layer.query_data("pq_pnorwd", start_time=start_time, limit=5)
        print(f"Filtered (wide) pq_pnorwd: {len(data)} records.")
        if data:
            print("Sample measurement_datetime:", data[0].get("measurement_datetime"))

        # Try filtering with a narrow range
        now = datetime.utcnow()
        start_time_narrow = now - timedelta(days=365)  # Wide but not 2020
        data_narrow = layer.query_data("pq_pnorwd", start_time=start_time_narrow, limit=5)
        print(f"Filtered (1y) pq_pnorwd: {len(data_narrow)} records.")
    else:
        print("pq_pnorwd NOT found.")

except Exception as e:
    print(f"Failed to query pq_pnorwd: {e}")
