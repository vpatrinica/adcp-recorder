import argparse
import logging
import os

import duckdb

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = r"C:\s1000\data\db\adcp.duckdb"


def list_objects(con):
    """List all tables and views in the database."""
    print("\n--- TABLES ---")
    df_tables = con.execute("SELECT table_name FROM duckdb_tables()").fetchdf()
    print(df_tables)

    print("\n--- VIEWS ---")
    df_views = con.execute("SELECT view_name FROM duckdb_views()").fetchdf()
    print(df_views)


def search_sql(con, query_str):
    """Search all SQL definitions (views, indexes, constraints) for a string."""
    query_str = query_str.lower()
    print(f"\n--- SEARCHING FOR '{query_str}' IN METADATA ---")

    # 1. Search Views
    views = con.execute("SELECT view_name, sql FROM duckdb_views()").fetchall()
    for v_name, sql in views:
        if query_str in str(sql).lower():
            print(f"[VIEW] {v_name} contains '{query_str}'")

    # 2. Search Constraints
    constraints = con.execute(
        "SELECT table_name, constraint_text FROM duckdb_constraints()"
    ).fetchall()
    for t_name, text in constraints:
        if query_str in str(text).lower():
            print(f"[CONSTRAINT] Table {t_name} contains '{query_str}' in constraint: {text}")

    # 3. Search Indexes
    indices = con.execute("SELECT index_name, sql FROM duckdb_indexes()").fetchall()
    for idx_name, sql in indices:
        if query_str in str(sql).lower():
            print(f"[INDEX] {idx_name} depends on '{query_str}'")


def find_dependencies(con, table_name):
    """Find objects that depend on a specific table using OID lookups."""
    print(f"\n--- DEPENDENCIES ON TABLE '{table_name}' ---")

    # Get table OID
    row = con.execute(
        f"SELECT table_oid FROM duckdb_tables() WHERE table_name = '{table_name}'"
    ).fetchone()
    if not row:
        logger.error(f"Table '{table_name}' not found.")
        return
    t_oid = row[0]

    # Find all objects that depend on it in duckdb_dependencies
    deps = con.execute(f"""
        SELECT objid, classid, deptype
        FROM duckdb_dependencies()
        WHERE refobjid = {t_oid}
    """).fetchall()

    if not deps:
        print(f"No direct dependencies found in duckdb_dependencies for OID {t_oid}.")
        return

    for oid, cid, d_type in deps:
        name = "Unknown"
        if cid == 0:  # Table or View
            r = con.execute(
                f"SELECT table_name FROM duckdb_tables() WHERE table_oid = {oid} "
                f"UNION SELECT view_name FROM duckdb_views() WHERE view_oid = {oid}"
            ).fetchone()
            if r:
                name = r[0]
        elif cid == 1:  # Index
            r = con.execute(
                f"SELECT index_name FROM duckdb_indexes() WHERE index_oid = {oid}"
            ).fetchone()
            if r:
                name = r[0]
        elif cid == 2:  # Sequence
            r = con.execute(
                f"SELECT sequence_name FROM duckdb_sequences() WHERE sequence_oid = {oid}"
            ).fetchone()
            if r:
                name = f"Sequence: {r[0]}"

        print(f"- {name} (OID: {oid}, Class: {cid}, Type: {d_type})")


def main():
    parser = argparse.ArgumentParser(description="DuckDB Diagnostic Utility")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to DuckDB database")
    parser.add_argument("--list", action="store_true", help="List all tables and views")
    parser.add_argument("--search", help="Search all SQL definitions for a string")
    parser.add_argument("--deps", help="Find dependencies on a specific table")

    args = parser.parse_args()

    if not os.path.exists(args.db):
        logger.error(f"Database not found at {args.db}")
        return

    con = duckdb.connect(args.db)

    if args.list:
        list_objects(con)
    if args.search:
        search_sql(con, args.search)
    if args.deps:
        find_dependencies(con, args.deps)

    if not any([args.list, args.search, args.deps]):
        parser.print_help()


if __name__ == "__main__":
    main()
