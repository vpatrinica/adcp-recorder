import os
from datetime import datetime

from adcp_recorder.config import RecorderConfig
from adcp_recorder.ui.parquet_data_layer import ParquetDataLayer

# Use configured output directory
config = RecorderConfig.load()
data_path = config.output_dir

if not os.path.exists(data_path):
    print(f"Error: {data_path} does not exist.")
    exit(1)

layer = ParquetDataLayer(data_path)

# Load data
print("Loading data...")
layer.load_data()

# Check sources
sources = layer.get_available_sources()
source_names = [s.name for s in sources]
print(f"Available sources: {source_names}")

# 1. Check PNORE
if "pq_pnore" in source_names:
    print("\nVerifying pq_pnore...")
    metadata = layer.get_source_metadata("pq_pnore")
    print(f"Timestamp column: {metadata.timestamp_column}")

    # Query all to see what dates we have
    data = layer.query_data("pq_pnore", limit=10)
    if data:
        print(f"Found {len(data)} records in pq_pnore.")
        for i, row in enumerate(data[:3]):
            print(f"Row {i} measurement_datetime: {row.get('measurement_datetime')}")
            print(f"Row {i} date: {row.get('date')}, time: {row.get('time')}")

        # Test filtering
        # Since data is from Feb 9, we need a range that includes it
        test_start = datetime(2026, 2, 9, 0, 0, 0)
        test_end = datetime(2026, 2, 11, 0, 0, 0)
        filtered = layer.query_data("pq_pnore", start_time=test_start, end_time=test_end, limit=5)
        print(f"Filtered (Feb 9-11) pq_pnore: {len(filtered)} records.")
    else:
        print("No records found in pq_pnore.")
else:
    print("\npq_pnore NOT LOADED.")

# 2. Check current_profile_df100 (which joins PNORI)
if "current_profile_df100" in source_names:
    print("\nVerifying current_profile_df100...")
    try:
        data = layer.query_data("current_profile_df100", limit=5)
        print(f"Success! Found {len(data)} records in current_profile_df100.")
    except Exception as e:
        print(f"Failed to query current_profile_df100: {e}")
else:
    print("\ncurrent_profile_df100 NOT CREATED.")
    if "pq_pnors" in source_names and "pq_pnorc" in source_names:
        print("Base views pq_pnors and pq_pnorc are present, but join failed.")
    else:
        print(
            f"Missing base views for current_profile_df100. Loaded: {[s for s in source_names if 'pnor' in s]}"
        )
