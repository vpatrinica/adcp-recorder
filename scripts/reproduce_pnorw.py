
import duckdb
import os
import shutil
import sys
# Make sure adcp_recorder is in path
sys.path.append(os.getcwd())

from adcp_recorder.ui.parquet_data_layer import ParquetDataLayer

DATA_DIR = os.path.join(os.getcwd(), "tmp_reproduce_pnorw")

def create_pnorw_data():
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
    os.makedirs(DATA_DIR)
    
    conn = duckdb.connect()
    
    # Create PNORW-like table with 'date' and 'time' columns
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_id START 1;")
    conn.execute("""
        CREATE TABLE pnorw_data (
            id INTEGER DEFAULT nextval('seq_id'),
            received_at TIMESTAMP,
            date VARCHAR,
            time VARCHAR,
            data INTEGER
        )
    """)
    # Inserting date as MMDDYY and time as HHMMSS 
    conn.execute("INSERT INTO pnorw_data (received_at, date, time, data) VALUES ('2026-02-10 12:00:00', '021026', '120000', 100)")
    
    # Export to parquet
    path_pnorw = os.path.join(DATA_DIR, "parquet", "PNORW", "date=2026-02-10")
    os.makedirs(path_pnorw)
    conn.execute(f"COPY pnorw_data TO '{path_pnorw}/data.parquet' (FORMAT PARQUET)")
    
    conn.close()

def test_pnorw_datetime():
    print("\nTesting PNORW measurement_datetime creation...")
    create_pnorw_data()
    
    dl = ParquetDataLayer(base_path=DATA_DIR)
    dl.load_data()
    
    source_name = "pq_pnorw"
    if source_name not in dl.get_loaded_views():
        print(f"Error: {source_name} not loaded")
        return
        
    cols = dl.execute_sql(f"DESCRIBE {source_name}")
    col_names = [c['column_name'] for c in cols]
    print(f"Columns for {source_name}: {col_names}")
    
    if "measurement_datetime" in col_names:
        print("PASS: measurement_datetime created for PNORW")
        # Check value
        count_res = dl.execute_sql(f"SELECT COUNT(*) as cnt FROM {source_name}")
        count = count_res[0]['cnt'] if count_res else 0
        print(f"Record count in {source_name}: {count}")
        
        # Try a simpler query first
        try:
            res_simple = dl.execute_sql(f"SELECT * FROM {source_name}")
            print(f"Simple SELECT count: {len(res_simple)}")
        except Exception as e:
            print(f"Simple SELECT failed: {e}")

        rows = dl.execute_sql(f"SELECT measurement_datetime FROM {source_name}")
        if count > 0 and len(rows) > 0 and rows[0]['measurement_datetime'] is not None:
             print(f"PASS: measurement_datetime populated: {rows[0]['measurement_datetime']}")
        else:
             print(f"FAIL: measurement_datetime is None or query failed. Rows: {rows}")

    # Verify query_data with timestamp_col override
    print("\nTesting query_data with timestamp_col override...")
    try:
        data_override = dl.query_data(
            source_name="pq_pnorw", 
            timestamp_col="received_at", 
            limit=1
        )
        print(f"Data with custom timestamp_col='received_at': {len(data_override)} records")
        if len(data_override) > 0 and 'received_at' in data_override[0]:
             print("PASS: query_data with timestamp_col override works")
        else:
             print("FAIL: query_data returned no data or incorrect columns")
    except Exception as e:
         print(f"FAIL: query_data with override raised exception: {e}")

if __name__ == "__main__":
    test_pnorw_datetime()
