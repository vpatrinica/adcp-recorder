
import duckdb
import os
import shutil
import sys
# Make sure adcp_recorder is in path
sys.path.append(os.getcwd())

from adcp_recorder.ui.data_layer import DataLayer, DataSource

DATA_DIR = os.path.join(os.getcwd(), "tmp_verify_quality")

def create_sample_data():
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
    os.makedirs(DATA_DIR)
    
    conn = duckdb.connect()
    
    # Create sample tables
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_id START 1;")
    conn.execute("CREATE TABLE pnors_data (id INTEGER, received_at TIMESTAMP)")
    conn.execute("INSERT INTO pnors_data VALUES (1, '2026-02-10 12:00:00')")
    
    conn.execute("CREATE TABLE parse_errors (id INTEGER, received_at TIMESTAMP, error_type VARCHAR)")
    conn.execute("INSERT INTO parse_errors VALUES (1, '2026-02-10 12:00:00', 'CHECKSUM')")
    
    return conn

def test_quality_metrics():
    print("\nTesting Quality Metrics...")
    conn = create_sample_data()
    dl = DataLayer(conn)
    
    metrics = dl.get_quality_metrics()
    print(f"Metrics: {metrics}")
    
    if metrics["total_records"] >= 1:
        print("PASS: Total records count > 0")
    else:
        print("FAIL: Total records count is 0")
        
    if "error_count" in metrics and metrics["error_count"] >= 1:
        print("PASS: Error count detected")
    else:
        print("FAIL: Error count not detected")

    if metrics["error_rate"] > 0:
        print("PASS: Error rate calculated")
    else:
         print(f"FAIL: Error rate is {metrics.get('error_rate')}")

if __name__ == "__main__":
    test_quality_metrics()
