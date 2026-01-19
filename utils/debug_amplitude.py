import os

import duckdb

from adcp_recorder.config import RecorderConfig


def debug_amplitude():
    config = RecorderConfig.load()
    db_path = config.db_path or os.path.join(config.output_dir, "db", "adcp.duckdb")
    print(f"Checking database at: {db_path}")

    conn = duckdb.connect(db_path, read_only=True)

    tables = ["pnorc12", "pnorc_df100", "pnorc34"]
    for table in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"Table {table}: {count} records")
            if count > 0:
                latest = conn.execute(f"SELECT MAX(received_at) FROM {table}").fetchone()[0]
                print(f"  Latest record: {latest}")
                sample = conn.execute(
                    f"SELECT amp1, amp2, amp3, amp4 FROM {table} WHERE amp1 IS NOT NULL LIMIT 3"
                ).fetchall()
                print(f"  Sample amplitudes: {sample}")
        except Exception as e:
            print(f"Table {table} error: {e}")

    conn.close()


if __name__ == "__main__":
    debug_amplitude()
