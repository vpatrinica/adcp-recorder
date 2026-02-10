import duckdb

print(f"DuckDB version: {duckdb.__version__}")
conn = duckdb.connect(":memory:")
print("Connection successful")
