"""Streamlit dashboard for ADCP data visualization and analysis."""

from datetime import datetime
from pathlib import Path

import plotly.express as px
import streamlit as st

from adcp_recorder.config import RecorderConfig
from adcp_recorder.db import DatabaseManager

# Setup page
st.set_page_config(page_title="ADCP Analysis Dashboard", layout="wide")

st.title("🌊 ADCP Recorder - Analysis Dashboard")


# Initialize DB connection
@st.cache_resource
def get_db():
    config = RecorderConfig.load()
    db_dir = Path(config.output_dir) / "db"
    db_path = config.db_path or (db_dir / "adcp.duckdb")
    return DatabaseManager(str(db_path))


db = get_db()
conn = db.get_connection()

# Sidebar
st.sidebar.header("Data Source")
db_path = st.sidebar.text_input("Database Path", value=db.db_path)

# Main Navigation
tab1, tab2, tab3 = st.tabs(["📊 Records & DuckLake", "⚠️ Parsing Errors", "⚙️ System Status"])

with tab1:
    st.header("Structured Records")

    # Query DuckLake views
    try:
        views_res = conn.execute(
            "SELECT view_name FROM duckdb_views() WHERE view_name LIKE 'view_%'"
        ).fetchall()
        available_views = [v[0] for v in views_res if v[0] and v[0].startswith("view_")]

        if available_views:
            selected_view = st.selectbox("Select Record Type", available_views)

            # Load sample data
            df = conn.execute(f'SELECT * FROM "{selected_view}" LIMIT 1000').df()

            st.metric("Total Records Loaded (Sample)", len(df))
            st.dataframe(df, width="stretch")

            # Simple visualization if applicable
            if "heading" in df.columns:
                st.subheader("Heading Distribution")
                fig = px.histogram(df, x="heading", title="Compass Heading Distribution")
                st.plotly_chart(fig, width="stretch")

            if "temperature" in df.columns:
                st.subheader("Temperature Over Time")
                # Assuming recorded_at is available
                if "recorded_at" in df.columns:
                    fig = px.line(df, x="recorded_at", y="temperature", title="Temperature Trend")
                    st.plotly_chart(fig, width="stretch")

        else:
            st.info(
                "📊 No DuckLake views available yet. "
                "Views will be created automatically as data is recorded."
            )
            # Show raw_lines as fallback
            st.subheader("Raw NMEA Lines")
            try:
                raw_df = conn.execute(
                    "SELECT * FROM raw_lines ORDER BY received_at DESC LIMIT 100"
                ).df()
                if not raw_df.empty:
                    st.dataframe(raw_df, width="stretch")
                else:
                    st.warning(
                        "No data recorded yet. Start the ADCP Recorder to begin collecting data."
                    )
            except Exception:
                st.warning(
                    "No data recorded yet. Start the ADCP Recorder to begin collecting data."
                )
    except Exception as e:
        st.error(f"Error loading data: {e}")

with tab2:
    st.header("Parsing Errors")
    try:
        errors_df = conn.execute(
            "SELECT * FROM parse_errors ORDER BY received_at DESC LIMIT 500"
        ).df()
        if not errors_df.empty:
            st.dataframe(errors_df, width="stretch")

            st.subheader("Error Types Distribution")
            fig = px.pie(errors_df, names="error_type", title="Error Distribution by Type")
            st.plotly_chart(fig, width="stretch")
        else:
            st.success("No parsing errors found! All systems nominal.")
    except Exception as e:
        st.error(f"Error loading parse errors: {e}")

with tab3:
    st.header("System Configuration")
    config = RecorderConfig.load()
    st.json({field: getattr(config, field) for field in RecorderConfig.PERSISTED_FIELDS})

    if st.button("Refresh DuckLake Views"):
        db.initialize_ducklake()
        st.success("Views refreshed!")

st.markdown("---")
st.caption(
    f"ADCP Recorder Dashboard - Last Refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
