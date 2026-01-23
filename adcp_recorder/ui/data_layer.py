"""Unified data access layer for dashboard visualizations.

Provides abstraction over DuckDB tables with metadata extraction,
time-range queries, and aggregation functions for dashboard components.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import duckdb


class ColumnType(str, Enum):
    """Column data type categories for UI rendering."""

    NUMERIC = "numeric"
    TIMESTAMP = "timestamp"
    TEXT = "text"
    BOOLEAN = "boolean"
    JSON = "json"


@dataclass
class ColumnMetadata:
    """Metadata about a database column."""

    name: str
    column_type: ColumnType
    nullable: bool = True
    unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class DataSource:
    """Represents a queryable data source (table or view)."""

    name: str
    display_name: str
    columns: list[ColumnMetadata]
    record_count: int = 0
    has_timestamp: bool = True
    timestamp_column: str = "received_at"
    category: str = "general"

    def get_column(self, name: str) -> ColumnMetadata | None:
        """Get column metadata by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def get_numeric_columns(self) -> list[str]:
        """Return names of numeric columns suitable for plotting."""
        return [c.name for c in self.columns if c.column_type == ColumnType.NUMERIC]

    def get_text_columns(self) -> list[str]:
        """Return names of text columns."""
        return [c.name for c in self.columns if c.column_type == ColumnType.TEXT]


# Known column units based on schema definitions
COLUMN_UNITS: dict[str, str] = {
    "temperature": "°C",
    "pressure": "dbar",
    "heading": "°",
    "pitch": "°",
    "roll": "°",
    "sound_speed": "m/s",
    "battery": "V",
    "vel1": "m/s",
    "vel2": "m/s",
    "vel3": "m/s",
    "vel4": "m/s",
    "speed": "m/s",
    "direction": "°",
    "distance": "m",
    "blanking_distance": "m",
    "cell_size": "m",
    "hm0": "m",
    "hmax": "m",
    "tp": "s",
    "tm02": "s",
    "mean_dir": "°",
    "peak_dir": "°",
    "directional_spread": "°",
    "altimeter_distance": "m",
    "start_frequency": "Hz",
    "step_frequency": "Hz",
}

# Data source categories for organization
SOURCE_CATEGORIES = {
    "pnori": "Configuration",
    "pnori12": "Configuration",
    "pnors_df100": "Sensor Data",
    "pnors12": "Sensor Data",
    "pnors34": "Sensor Data",
    "pnorc_df100": "Velocity Data",
    "pnorc12": "Velocity Data",
    "pnorc34": "Velocity Data",
    "pnorh": "Header Data",
    "pnore_data": "Wave Data",
    "pnorw_data": "Wave Data",
    "pnorb_data": "Wave Data",
    "pnorf_data": "Wave Data",
    "pnorwd_data": "Wave Data",
    "pnora_data": "Altitude Data",
    "raw_lines": "Raw Data",
    "parse_errors": "Errors",
}


def _infer_column_type(duckdb_type: str) -> ColumnType:
    """Map DuckDB type to our column type enum."""
    type_lower = duckdb_type.lower()
    if any(
        t in type_lower
        for t in ("int", "bigint", "smallint", "tinyint", "decimal", "double", "float")
    ):
        return ColumnType.NUMERIC
    if "timestamp" in type_lower or "date" in type_lower or "time" in type_lower:
        return ColumnType.TIMESTAMP
    if "bool" in type_lower:
        return ColumnType.BOOLEAN
    if "json" in type_lower:
        return ColumnType.JSON
    return ColumnType.TEXT


def _format_display_name(table_name: str) -> str:
    """Format table name for display."""
    # Remove underscores and capitalize
    parts = table_name.replace("_", " ").split()
    return " ".join(p.upper() if len(p) <= 2 else p.title() for p in parts)


class DataLayer:
    """Unified data access for dashboard components."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Initialize with a DuckDB connection."""
        self.conn = conn
        self._source_cache: dict[str, DataSource] = {}

    def get_available_sources(self, include_views: bool = True) -> list[DataSource]:
        """List all available data sources with metadata."""
        sources = []

        # Get all tables
        tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        tables = self.conn.execute(tables_query).fetchall()

        for (table_name,) in tables:
            # Skip internal tables
            if table_name.startswith("_"):
                continue
            source = self.get_source_metadata(table_name)
            if source:
                sources.append(source)

        # Get DuckLake views if requested
        if include_views:
            try:
                views_query = """
                    SELECT view_name FROM duckdb_views()
                    WHERE schema_name = 'main'
                """
                views = self.conn.execute(views_query).fetchall()
                for (view_name,) in views:
                    source = self.get_source_metadata(view_name)
                    if source:
                        sources.append(source)
            except Exception:
                # Views may not exist yet
                pass

        return sources

    def get_source_metadata(self, source_name: str) -> DataSource | None:
        """Get detailed metadata for a specific data source."""
        if source_name in self._source_cache:
            return self._source_cache[source_name]

        try:
            # Get column info using DESCRIBE
            col_info = self.conn.execute(f"DESCRIBE {source_name}").fetchall()
        except Exception:
            return None

        columns = []
        timestamp_col = None

        for col_name, col_type, null, _key, _default, _extra in col_info:
            column_type = _infer_column_type(col_type)
            unit = COLUMN_UNITS.get(col_name)

            col = ColumnMetadata(
                name=col_name,
                column_type=column_type,
                nullable=null == "YES",
                unit=unit,
            )
            columns.append(col)

            # Track timestamp column
            if column_type == ColumnType.TIMESTAMP and timestamp_col is None:
                timestamp_col = col_name

        # Get record count
        try:
            res = self.conn.execute(f"SELECT COUNT(*) FROM {source_name}").fetchone()
            count = res[0] if res else 0
        except Exception:
            count = 0

        source = DataSource(
            name=source_name,
            display_name=_format_display_name(source_name),
            columns=columns,
            record_count=count,
            has_timestamp=timestamp_col is not None,
            timestamp_column=timestamp_col or "received_at",
            category=SOURCE_CATEGORIES.get(source_name, "Other"),
        )

        self._source_cache[source_name] = source
        return source

    def query(
        self,
        view_name: str,
        columns: list[str] | None = None,
        limit: int = 100,
        order_by: str | None = None,
        order_desc: bool = True,
    ) -> list[dict[str, Any]]:
        """Query data from a source (implements DataLayerProtocol)."""
        source = self.get_source_metadata(view_name)
        if not source:
            raise ValueError(f"Unknown data source: {view_name}")

        col_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {col_str} FROM {source.name}"

        if order_by:
            direction = "DESC" if order_desc else "ASC"
            query += f" ORDER BY {order_by} {direction}"
        elif source.has_timestamp:
            query += f" ORDER BY {source.timestamp_column} {'DESC' if order_desc else 'ASC'}"

        query += f" LIMIT {limit}"

        result = self.conn.execute(query).fetchall()
        col_names = [d[0] for d in self.conn.description]
        return [dict(zip(col_names, row, strict=False)) for row in result]

    def get_column_info(self, view_name: str) -> list[tuple[str, str]]:
        """Get column names and types for a view (implements DataLayerProtocol)."""
        # We can implement this via get_source_metadata or direct DESCRIBE
        # Using DESCRIBE directly to match expected output format if getting source fails
        try:
            source = self.get_source_metadata(view_name)
            if source:
                target_name = source.name
            else:
                target_name = view_name  # Try direct name

            result = self.conn.execute(f"DESCRIBE {target_name}").fetchall()
            return [(row[0], row[1]) for row in result]
        except Exception:
            return []

    def execute_sql(self, sql: str) -> list[dict[str, Any]]:
        """Execute arbitrary SQL query (implements DataLayerProtocol)."""
        try:
            result = self.conn.execute(sql).fetchall()
            if not self.conn.description:
                return []
            col_names = [d[0] for d in self.conn.description]
            return [dict(zip(col_names, row, strict=False)) for row in result]
        except Exception:
            return []

    def query_data(
        self,
        source_name: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        order_desc: bool = True,
    ) -> list[dict[str, Any]]:
        """Query data from a source with optional filters."""
        source = self.get_source_metadata(source_name)
        if not source:
            return []

        # Build column list
        if columns:
            # Validate columns exist
            valid_cols = {c.name for c in source.columns}
            cols = [c for c in columns if c in valid_cols]
            if not cols:
                cols = ["*"]
            col_str = ", ".join(cols)
        else:
            col_str = "*"

        # Build query
        query = f"SELECT {col_str} FROM {source.name}"
        params = []

        # Add filters
        conditions = []
        if filters:
            for col, value in filters.items():
                conditions.append(f"{col} = ?")
                params.append(value)

        # Add time filters
        if start_time and source.has_timestamp:
            conditions.append(f"{source.timestamp_column} >= ?")
            params.append(start_time)
        if end_time and source.has_timestamp:
            conditions.append(f"{source.timestamp_column} <= ?")
            params.append(end_time)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Add ordering (default to timestamp if available)
        order_by_col = source.timestamp_column if source.has_timestamp else None
        if order_by_col:
            query += f" ORDER BY {order_by_col} {'DESC' if order_desc else 'ASC'}"

        # Add limit
        query += f" LIMIT {limit}"

        # Execute and convert to dicts
        result = self.conn.execute(query, params).fetchall()
        col_names = [d[0] for d in self.conn.description]
        return [dict(zip(col_names, row, strict=False)) for row in result]

    def query_time_series(
        self,
        source_name: str,
        y_columns: list[str],
        time_range: str = "24h",
        x_column: str | None = None,
    ) -> dict[str, Any]:
        """Query time series data optimized for plotting."""
        source = self.get_source_metadata(source_name)
        if not source:
            return {"x": [], "series": {col: [] for col in y_columns}}

        x_col = x_column or source.timestamp_column

        # Parse time range
        start_time = self._parse_time_range(time_range)

        # Build columns list
        all_cols = [x_col] + y_columns
        valid_cols = {c.name for c in source.columns}
        cols = [c for c in all_cols if c in valid_cols]

        if len(cols) < 2:
            return {"x": [], "series": {}}

        col_str = ", ".join(cols)
        query = f"SELECT {col_str} FROM {source.name}"

        params = []
        if start_time:
            query += f" WHERE {source.timestamp_column} >= ?"
            params.append(start_time)

        query += f" ORDER BY {x_col} ASC LIMIT 10000"

        try:
            result = self.conn.execute(query, params).fetchall()

            # Structure for plotting
            x_values = []
            series_data: dict[str, list] = {col: [] for col in y_columns}

            for row in result:
                x_values.append(row[0])
                for _i, col in enumerate(y_columns):
                    if col in valid_cols:
                        idx = cols.index(col)
                        series_data[col].append(row[idx])

            return {"x": x_values, "series": series_data}
        except Exception:
            return {"x": [], "series": {col: [] for col in y_columns}}

    def query_velocity_profile(
        self,
        source_name: str,
        velocity_columns: list[str] | None = None,
        cell_size: float = 1.0,
        blanking_distance: float = 0.5,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        """Query velocity data structured for depth profile plotting."""
        if velocity_columns is None:
            velocity_columns = ["vel1", "vel2", "vel3", "vel4"]

        source = self.get_source_metadata(source_name)
        if not source:
            return {"depths": [], "velocities": {}}

        # Get the latest measurement if no timestamp specified
        if timestamp is None:
            query = f"""
                SELECT DISTINCT measurement_date, measurement_time
                FROM {source.name}
                ORDER BY measurement_date DESC, measurement_time DESC
                LIMIT 1
            """
            latest = self.conn.execute(query).fetchone()
            if not latest:
                return {"depths": [], "velocities": {}}
            date_filter, time_filter = latest
        else:
            date_filter = timestamp.strftime("%d%m%y")
            time_filter = timestamp.strftime("%H%M%S")

        # Query all cells for this measurement
        cols = ["cell_index", "distance"] + velocity_columns
        valid_cols = [c for c in cols if any(col.name == c for col in source.columns)]
        col_str = ", ".join(valid_cols)

        query = f"""
            SELECT {col_str} FROM {source.name}
            WHERE measurement_date = ? AND measurement_time = ?
            ORDER BY cell_index ASC
        """
        result = self.conn.execute(query, [date_filter, time_filter]).fetchall()

        # Calculate depths and organize velocities
        depths = []
        velocities: dict[str, list] = {col: [] for col in velocity_columns}

        for row in result:
            cell_idx = row[0]
            distance = row[1] if len(row) > 1 and "distance" in valid_cols else None

            depth = distance if distance is not None else blanking_distance + cell_idx * cell_size

            depths.append(depth)

            for _i, col in enumerate(velocity_columns):
                if col in valid_cols:
                    idx = valid_cols.index(col)
                    velocities[col].append(row[idx])

        return {"depths": depths, "velocities": velocities}

    def query_velocity_profiles(
        self,
        source_name: str,
        velocity_columns: list[str] | None = None,
        cell_size: float = 1.0,
        blanking_distance: float = 0.5,
        timestamps: list[datetime] | None = None,
    ) -> list[dict[str, Any]]:
        """Query multiple velocity profiles for overlapping plots."""
        if not timestamps:
            return [
                self.query_velocity_profile(
                    source_name, velocity_columns, cell_size, blanking_distance
                )
            ]

        return [
            self.query_velocity_profile(
                source_name, velocity_columns, cell_size, blanking_distance, ts
            )
            for ts in timestamps
        ]

    def query_amplitude_heatmap(
        self,
        source_name: str,
        time_range: str = "24h",
    ) -> list[dict[str, Any]]:
        """Query average signal strength (amplitude) for heatmaps."""
        source = self.get_source_metadata(source_name)
        if not source:
            return []

        start_time = self._parse_time_range(time_range)

        # We average across all 4 beams for "Average Signal Strength"
        query = f"""
            SELECT
                received_at,
                cell_index,
                (COALESCE(amp1, 0) + COALESCE(amp2, 0) +
                 COALESCE(amp3, 0) + COALESCE(amp4, 0)) / 4.0 as avg_amp
            FROM {source.name}
        """
        params = []
        if start_time:
            query += " WHERE received_at >= ?"
            params.append(start_time)

        query += " ORDER BY received_at DESC, cell_index ASC LIMIT 20000"

        result = self.conn.execute(query, params).fetchall()

        # Organize by timestamp for heatmap
        # Group by received_at, extract list of amplitudes
        from collections import defaultdict

        grouped = defaultdict(list)
        for ts, _idx, amp in result:
            grouped[ts].append(amp)

        heatmap_data = []
        for ts, amps in grouped.items():
            heatmap_data.append({"received_at": ts, "amplitudes": amps})

        return sorted(heatmap_data, key=lambda x: x["received_at"], reverse=True)

    def query_spectrum_data(
        self,
        source_name: str,
        coefficient: str = "A1",
        time_range: str = "24h",
    ) -> list[dict[str, Any]]:
        """Query Fourier coefficient spectrum data."""
        source = self.get_source_metadata(source_name)
        if not source:
            return []

        start_time = self._parse_time_range(time_range)

        query = f"""
            SELECT
                measurement_date, measurement_time,
                start_frequency, step_frequency, num_frequencies,
                coefficient_flag, coefficients
            FROM {source.name}
            WHERE coefficient_flag = ?
        """
        params: list[Any] = [coefficient]

        if start_time:
            query += " AND received_at >= ?"
            params.append(start_time)

        query += " ORDER BY received_at DESC LIMIT 100"

        try:
            result = self.conn.execute(query, params).fetchall()
            col_names = [d[0] for d in self.conn.description]
            return [dict(zip(col_names, row, strict=False)) for row in result]
        except Exception:
            return []

    def get_available_bursts(
        self,
        time_range: str = "24h",
        source_name: str = "pnore_data",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get a list of available measurement bursts (unique date/time) for wave data.

        Args:
            time_range: Search within this time range (used if start_time not provided)
            source_name: Data source to check (pnore_data, pnorw_data, etc.)
            start_time: Explicit start time filter
            end_time: Explicit end time filter

        Returns:
            List of dicts with measurement_date, measurement_time, and received_at
        """
        if not start_time:
            start_time = self._parse_time_range(time_range)

        source = self.get_source_metadata(source_name)
        if not source:
            return []

        real_source_name = source.name

        query = f"""
            SELECT DISTINCT measurement_date, measurement_time, received_at
            FROM {real_source_name}
        """
        params = []
        conditions = []

        if start_time:
            conditions.append("received_at >= ?")
            params.append(start_time)

        if end_time:
            conditions.append("received_at <= ?")
            params.append(end_time)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY received_at DESC LIMIT 1000"

        try:
            result = self.conn.execute(query, params).fetchall()
            return [
                {
                    "measurement_date": r[0],
                    "measurement_time": r[1],
                    "received_at": r[2],
                    "label": f"{r[0]} {r[1]}",
                }
                for r in result
            ]
        except Exception:
            return []

    def query_wave_energy(
        self,
        source_name: str,
        time_range: str = "24h",
    ) -> list[dict[str, Any]]:
        """Query wave energy density spectrum data for heatmaps."""
        source = self.get_source_metadata(source_name)
        if not source:
            return []

        start_time = self._parse_time_range(time_range)

        query = f"""
            SELECT
                received_at,
                start_frequency, step_frequency, num_frequencies,
                energy_densities
            FROM {source.name}
        """
        params = []

        if start_time:
            query += " WHERE received_at >= ?"
            params.append(start_time)

        query += " ORDER BY received_at DESC LIMIT 500"

        try:
            result = self.conn.execute(query, params).fetchall()
            col_names = [d[0] for d in self.conn.description]
            return [dict(zip(col_names, row, strict=False)) for row in result]
        except Exception:
            return []

    def query_directional_spectrum(
        self,
        time_range: str = "24h",
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        """Query unified directional spectrum data merging energy, direction, and spread."""
        import json

        source_pnore = self.get_source_metadata("pnore_data")
        source_pnorwd = self.get_source_metadata("pnorwd_data")

        if not source_pnore or not source_pnorwd:
            # Try simple defaults
            name_pnore = "pnore_data"
            name_pnorwd = "pnorwd_data"
        else:
            name_pnore = source_pnore.name
            name_pnorwd = source_pnorwd.name

        try:
            # 1. Find the target measurement time
            if timestamp:
                query = f"""
                    SELECT
                        start_frequency, step_frequency, num_frequencies, energy_densities,
                        received_at, measurement_date, measurement_time
                    FROM {name_pnore}
                    WHERE received_at = ?
                """
                energy_data = self.conn.execute(query, [timestamp]).fetchone()

                if not energy_data:
                    # Fallback to string matching if received_at fails
                    date_str = timestamp.strftime("%m%d%y")
                    time_str = timestamp.strftime("%H%M%S")
                else:
                    (start_f, step_f, num_f, energy_densities_json, ts, date_str, time_str) = (
                        energy_data
                    )
                    energy = json.loads(energy_densities_json)
            else:
                # Find the latest measurement that has all components
                latest_query = f"""
                    SELECT DISTINCT e.measurement_date, e.measurement_time, e.received_at
                    FROM {name_pnore} e
                    JOIN {name_pnorwd} md ON e.measurement_date = md.measurement_date
                        AND e.measurement_time = md.measurement_time AND md.direction_type = 'MD'
                    JOIN {name_pnorwd} ds ON e.measurement_date = ds.measurement_date
                        AND e.measurement_time = ds.measurement_time AND ds.direction_type = 'DS'
                    ORDER BY e.received_at DESC
                    LIMIT 1
                """
                latest = self.conn.execute(latest_query).fetchone()
                if not latest:
                    return {}
                date_str, time_str, _ = latest
                energy_data = None  # Will fetch below

            # 2. Fetch Energy if not already fetched
            if not energy_data:
                energy_data = self.conn.execute(
                    f"""
                    SELECT
                        start_frequency, step_frequency, num_frequencies,
                        energy_densities, received_at
                    FROM {name_pnore}
                    WHERE measurement_date = ? AND measurement_time = ?
                    """,
                    [date_str, time_str],
                ).fetchone()

                if not energy_data:
                    return {}

                start_f, step_f, num_f, energy_densities_json, ts = energy_data
                energy = json.loads(energy_densities_json)

            # Mean Direction
            md_data = self.conn.execute(
                f"""
                SELECT values FROM {name_pnorwd}
                WHERE measurement_date = ? AND measurement_time = ? AND direction_type = 'MD'
                """,
                [date_str, time_str],
            ).fetchone()
            directions = json.loads(md_data[0]) if md_data else [0.0] * num_f

            # Directional Spread
            ds_data = self.conn.execute(
                f"""
                SELECT values FROM {name_pnorwd}
                WHERE measurement_date = ? AND measurement_time = ? AND direction_type = 'DS'
                """,
                [date_str, time_str],
            ).fetchone()
            spreads = json.loads(ds_data[0]) if ds_data else [0.0] * num_f

            # 3. Reconstruct frequencies
            frequencies = [round(float(start_f + i * step_f), 4) for i in range(num_f)]

            return {
                "timestamp": ts,
                "measurement_date": date_str,
                "measurement_time": time_str,
                "frequencies": frequencies,
                "energy": energy,
                "directions": directions,
                "spreads": spreads,
            }
        except Exception:
            return {}

    def get_column_stats(
        self,
        source_name: str,
        column: str,
    ) -> dict[str, Any]:
        """Get statistics for a numeric column."""
        source = self.get_source_metadata(source_name)
        if not source:
            return {}

        col_meta = source.get_column(column)
        if not col_meta or col_meta.column_type != ColumnType.NUMERIC:
            return {}

        query = f"""
            SELECT
                MIN({column}) as min_val,
                MAX({column}) as max_val,
                AVG({column}) as avg_val,
                COUNT({column}) as count
            FROM {source.name}
            WHERE {column} IS NOT NULL
        """

        try:
            result = self.conn.execute(query).fetchone()
            if result:
                return {
                    "min": result[0],
                    "max": result[1],
                    "avg": result[2],
                    "count": result[3],
                }
        except Exception:
            pass
        return {}

    def _parse_time_range(self, time_range: str) -> datetime | None:
        """Parse time range string to start datetime."""
        now = datetime.now()
        parse_map = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        if time_range in parse_map:
            return now - parse_map[time_range]
        return None

    def aggregate_time_series(
        self,
        source_name: str,
        y_column: str,
        time_range: str = "24h",
        bucket_minutes: int = 5,
        aggregation: str = "avg",
    ) -> dict[str, list]:
        """Aggregate time series data into time buckets."""
        source = self.get_source_metadata(source_name)
        if not source or not source.has_timestamp:
            return {"x": [], "y": []}

        start_time = self._parse_time_range(time_range)
        ts_col = source.timestamp_column

        agg_func = aggregation.upper()
        if agg_func not in ("AVG", "MIN", "MAX", "SUM", "COUNT"):
            agg_func = "AVG"

        query = f"""
            SELECT
                time_bucket(INTERVAL '{bucket_minutes} minutes', {ts_col}) as bucket,
                {agg_func}({y_column}) as value
            FROM {source.name}
            WHERE {ts_col} IS NOT NULL
        """
        params = []

        if start_time:
            query += f" AND {ts_col} >= ?"
            params.append(start_time)

        query += " GROUP BY bucket ORDER BY bucket ASC"

        result = self.conn.execute(query, params).fetchall()

        return {
            "x": [row[0] for row in result],
            "y": [row[1] for row in result],
        }
