import os

import duckdb

from adcp_recorder.config import RecorderConfig


def check():
    config = RecorderConfig.load()
    db_path = config.db_path or os.path.join(config.output_dir, "db", "adcp.duckdb")
    print(f"Checking DB: {db_path}")

    # Try to connect with a different approach to bypass locks if possible,
    # though DuckDB generally doesn't support concurrent write/read well.
    # We'll use the existing read_only=True.
    try:
        conn = duckdb.connect(db_path, read_only=True)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    print("\n--- PNORE Data (First 3) ---")
    pnore = conn.execute(
        """
        SELECT
            measurement_date, measurement_time,
            length(measurement_date), length(measurement_time)
        FROM pnore_data LIMIT 3
        """
    ).fetchall()
    for row in pnore:
        print(f"Date: '{row[0]}' (len {row[2]}), Time: '{row[1]}' (len {row[3]})")

    print("\n--- PNORWD Data (First 5) ---")
    pnorwd = conn.execute(
        """
        SELECT
            measurement_date, measurement_time, direction_type,
            length(measurement_date), length(measurement_time)
        FROM pnorwd_data LIMIT 5
        """
    ).fetchall()
    for row in pnorwd:
        print(f"Date: '{row[0]}' (len {row[3]}), Time: '{row[1]}' (len {row[4]}), Type: {row[2]}")

    print("\n--- Testing Join ---")
    query = """
        SELECT e.measurement_date, e.measurement_time
        FROM pnore_data e
        JOIN pnorwd_data md ON e.measurement_date = md.measurement_date
            AND e.measurement_time = md.measurement_time AND md.direction_type = 'MD'
        JOIN pnorwd_data ds ON e.measurement_date = ds.measurement_date
            AND e.measurement_time = ds.measurement_time AND ds.direction_type = 'DS'
        LIMIT 5
    """
    joined = conn.execute(query).fetchall()
    print(f"Matched rows: {len(joined)}")
    for row in joined:
        print(f"Matched: {row[0]} {row[1]}")

    if not joined:
        print("\n--- Debugging Join Failure ---")
        date_check = conn.execute(
            """
            SELECT DISTINCT e.measurement_date, md.measurement_date
            FROM pnore_data e, pnorwd_data md LIMIT 5
            """
        ).fetchall()
        print("Sample dates from both tables:")
        for row in date_check:
            print(f"PNORE: '{row[0]}', PNORWD: '{row[1]}'")

        time_check = conn.execute(
            """
            SELECT DISTINCT e.measurement_time, md.measurement_time
            FROM pnore_data e, pnorwd_data md LIMIT 5
            """
        ).fetchall()
        print("Sample times from both tables:")
        for row in time_check:
            print(f"PNORE: '{row[0]}', PNORWD: '{row[1]}'")


if __name__ == "__main__":
    check()
