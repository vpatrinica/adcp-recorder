import os

import duckdb

from adcp_recorder.config import RecorderConfig


def check():
    config = RecorderConfig.load()
    db_path = config.db_path or os.path.join(config.output_dir, "db", "adcp.duckdb")
    print(f"Checking DB: {db_path}")

    conn = duckdb.connect(db_path, read_only=True)

    print("\nTable Counts:")
    for table in ["pnore_data", "pnorwd_data", "pnorw_data", "pnorb_data"]:
        count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")

    print("\nPNORE samples:")
    print(
        conn.execute(
            "SELECT measurement_date, measurement_time, received_at FROM pnore_data LIMIT 5"
        ).df()
    )

    print("\nPNORWD samples:")
    print(
        conn.execute(
            """
            SELECT measurement_date, measurement_time, direction_type, received_at
            FROM pnorwd_data LIMIT 10
            """
        ).df()
    )

    print("\nJoined Records (query_directional_spectrum logic):")
    query = """
        SELECT DISTINCT e.measurement_date, e.measurement_time
        FROM pnore_data e
        JOIN pnorwd_data md ON e.measurement_date = md.measurement_date
            AND e.measurement_time = md.measurement_time AND md.direction_type = 'MD'
        JOIN pnorwd_data ds ON e.measurement_date = ds.measurement_date
            AND e.measurement_time = ds.measurement_time AND ds.direction_type = 'DS'
    """
    joined = conn.execute(query).df()
    print(f"Total matched bursts: {len(joined)}")
    if not joined.empty:
        print(joined.head())


if __name__ == "__main__":
    check()
