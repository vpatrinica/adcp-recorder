import json
import os

import duckdb

from adcp_recorder.config import RecorderConfig

# Use configured output directory
config = RecorderConfig.load()
data_path = config.output_dir

print(f"Inspecting Parquet files in: {data_path}")

parquet_files = []
for root, dirs, files in os.walk(data_path):
    for file in files:
        if file.endswith(".parquet"):
            parquet_files.append(os.path.join(root, file))

if not parquet_files:
    print("No Parquet files found.")
    exit(0)

print(f"Found {len(parquet_files)} Parquet files. Inspecting first 5...")

results = {}
for f in parquet_files[:5]:
    try:
        # Use relative path for cleaner output if possible
        rel_path = os.path.relpath(f, data_path)
        path_posix = f.replace("\\", "/")
        cols = duckdb.execute(f"DESCRIBE SELECT * FROM read_parquet('{path_posix}')").fetchall()
        col_names = [c[0] for c in cols]
        samples = duckdb.execute(f"SELECT * FROM read_parquet('{path_posix}') LIMIT 3").fetchall()
        results[rel_path] = {
            "columns": col_names,
            "samples": [[str(val) for val in s] for s in samples],
        }
    except Exception as e:
        results[f] = str(e)

print(json.dumps(results, indent=2))
