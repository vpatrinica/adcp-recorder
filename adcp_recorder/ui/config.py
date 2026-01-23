"""Dashboard configuration system with YAML persistence.

Provides configuration classes for dashboard layouts, panels, and plot settings.
Configurations are persisted to ~/.adcp-recorder/dashboards/ as YAML files.
"""

from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

import yaml  # type: ignore
from pydantic import BaseModel, Field, field_validator


class PanelType(str, Enum):
    """Available panel/widget types for dashboards."""

    TABLE = "table"
    TIME_SERIES = "time_series"
    VELOCITY_PROFILE = "velocity_profile"
    SPECTRUM = "spectrum"
    HEATMAP = "heatmap"
    AMPLITUDE_HEATMAP = "amplitude_heatmap"
    POLAR = "polar"


class TimeRange(str, Enum):
    """Preset time range options."""

    HOUR_1 = "1h"
    HOURS_6 = "6h"
    HOURS_24 = "24h"
    DAYS_7 = "7d"
    DAYS_30 = "30d"
    ALL = "all"
    CUSTOM = "custom"


class PanelPosition(BaseModel):
    """Grid position and size for a panel."""

    row: int = Field(default=0, ge=0, description="Row position (0-indexed)")
    col: int = Field(default=0, ge=0, description="Column position (0-indexed)")
    width: int = Field(ge=1, default=1, description="Width in grid units")
    height: int = Field(ge=1, default=1, description="Height in grid units")


class SeriesConfig(BaseModel):
    """Configuration for a single data series in a plot."""

    source: str = Field(description="Table/view name as data source")
    x: str = Field(default="received_at", description="X-axis column")
    y: str = Field(description="Y-axis column")
    label: str | None = Field(default=None, description="Display label for series")
    color: str | None = Field(default=None, description="Hex color for series")

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is not None and not v.startswith("#"):
            raise ValueError("Color must be a hex value starting with #")
        return v


class TablePanelConfig(BaseModel):
    """Configuration specific to table panels."""

    data_source: str = Field(description="Table/view name")
    columns: list[str] = Field(default_factory=list, description="Columns to display")
    limit: int = Field(default=100, ge=1, le=10000, description="Row limit")
    sortable: bool = Field(default=True)
    filterable: bool = Field(default=True)


class TimeSeriesPanelConfig(BaseModel):
    """Configuration for time series plot panels."""

    series: list[SeriesConfig] = Field(default_factory=list)
    time_range: str = Field(default="24h")
    show_legend: bool = Field(default=True)
    y_axis_label: str | None = None


class SpectrumPanelConfig(BaseModel):
    """Configuration for spectrum/Fourier coefficient plots."""

    data_source: str = Field(default="pnorf_data")
    plot_type: str = Field(default="fourier_coefficients")
    coefficient: str = Field(default="A1", description="Coefficient type: A1, B1, A2, B2")
    time_range: str = Field(default="24h")

    @field_validator("coefficient")
    @classmethod
    def validate_coefficient(cls, v: str) -> str:
        """Validate the coefficient flag."""
        if v not in ("A1", "B1", "A2", "B2"):
            raise ValueError("Coefficient must be one of: A1, B1, A2, B2")
        return v


class VelocityProfilePanelConfig(BaseModel):
    """Configuration for velocity profile depth plots."""

    data_source: str = Field(default="pnorc12")
    velocity_columns: list[str] = Field(default_factory=lambda: ["vel1", "vel2", "vel3", "vel4"])
    cell_size: float = Field(default=1.0, description="Cell size in meters")
    blanking_distance: float = Field(default=0.5, description="Blanking distance in m")
    time_range: str = Field(default="24h")


class HeatmapPanelConfig(BaseModel):
    """Configuration for heatmap visualizations (e.g., wave energy)."""

    data_source: str = Field(default="pnore_data")
    x: str = Field(default="start_frequency")
    y: str = Field(default="received_at")
    z: str = Field(default="energy_densities")
    colorscale: str = Field(default="Viridis")
    time_range: str = Field(default="24h")


class PolarPanelConfig(BaseModel):
    """Configuration for polar plots (e.g., directional spectrum)."""

    time_range: str = Field(default="24h")


class PanelConfig(BaseModel):
    """Configuration for a single dashboard panel."""

    id: str = Field(description="Unique panel identifier")
    type: PanelType = Field(description="Panel type")
    title: str | None = Field(default=None, description="Panel title")
    position: PanelPosition = Field(default_factory=PanelPosition)
    config: dict[str, Any] = Field(default_factory=dict, description="Type-specific configuration")

    def get_typed_config(
        self,
    ) -> (
        TablePanelConfig
        | TimeSeriesPanelConfig
        | SpectrumPanelConfig
        | VelocityProfilePanelConfig
        | HeatmapPanelConfig
        | PolarPanelConfig
    ):
        """Return the appropriately typed config based on panel type."""
        config_map = {
            PanelType.TABLE: TablePanelConfig,
            PanelType.TIME_SERIES: TimeSeriesPanelConfig,
            PanelType.SPECTRUM: SpectrumPanelConfig,
            PanelType.VELOCITY_PROFILE: VelocityProfilePanelConfig,
            PanelType.HEATMAP: HeatmapPanelConfig,
            PanelType.AMPLITUDE_HEATMAP: HeatmapPanelConfig,
            PanelType.POLAR: PolarPanelConfig,
        }
        config_class = config_map.get(self.type)
        if config_class:
            return config_class(**self.config)
        raise ValueError(f"Unknown panel type: {self.type}")


class LayoutConfig(BaseModel):
    """Dashboard grid layout configuration."""

    columns: int = Field(default=3, ge=1, le=6, description="Number of grid columns")
    rows: int = Field(default=2, ge=1, le=10, description="Number of grid rows")


class DashboardConfig(BaseModel):
    """Complete dashboard configuration with persistence."""

    name: str = Field(description="Dashboard display name")
    description: str = Field(default="", description="Dashboard description")
    refresh_interval: int = Field(
        default=0,
        ge=0,
        description="Auto-refresh interval in seconds (0=disabled)",
    )
    default_time_range: str = Field(default="24h")
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    panels: list[PanelConfig] = Field(default_factory=list)

    # Class-level configuration directory
    CONFIG_DIR_NAME: ClassVar[str] = "dashboards"

    @classmethod
    def get_config_dir(cls) -> Path:
        """Return the dashboard configuration directory path."""
        from adcp_recorder.config import RecorderConfig

        base_dir = RecorderConfig.get_default_config_dir()
        return base_dir / cls.CONFIG_DIR_NAME

    @classmethod
    def list_dashboards(cls) -> list[str]:
        """List all available dashboard configuration files."""
        config_dir = cls.get_config_dir()
        if not config_dir.exists():
            return []
        return [f.stem for f in config_dir.glob("*.yaml")]

    @classmethod
    def load(cls, name: str) -> "DashboardConfig":
        """Load a dashboard configuration from YAML file."""
        config_path = cls.get_config_dir() / f"{name}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Dashboard config not found: {name}")

        with config_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    @classmethod
    def load_or_default(cls, name: str) -> "DashboardConfig":
        """Load dashboard or return a default if not found."""
        try:
            return cls.load(name)
        except FileNotFoundError:
            return cls.create_default(name)

    @classmethod
    def create_default(cls, name: str = "default") -> "DashboardConfig":
        """Create a default dashboard configuration."""
        return cls(
            name=name,
            description="Default ADCP Analysis Dashboard",
            default_time_range="24h",
            layout=LayoutConfig(columns=2, rows=2),
            panels=[
                PanelConfig(
                    id="sensor_overview",
                    type=PanelType.TABLE,
                    title="Sensor Data",
                    position=PanelPosition(row=0, col=0, width=1, height=1),
                    config={
                        "data_source": "pnors_df100",
                        "columns": [
                            "measurement_date",
                            "temperature",
                            "pressure",
                            "heading",
                        ],
                        "limit": 100,
                    },
                ),
                PanelConfig(
                    id="temp_trend",
                    type=PanelType.TIME_SERIES,
                    title="Temperature Trend",
                    position=PanelPosition(row=0, col=1, width=1, height=1),
                    config={
                        "series": [
                            {
                                "source": "pnors_df100",
                                "x": "received_at",
                                "y": "temperature",
                                "label": "Temperature (°C)",
                                "color": "#FF6B6B",
                            },
                        ],
                        "time_range": "24h",
                    },
                ),
                PanelConfig(
                    id="velocity_profile",
                    type=PanelType.VELOCITY_PROFILE,
                    title="Velocity Profile",
                    position=PanelPosition(row=1, col=0, width=1, height=1),
                    config={
                        "data_source": "pnorc12",
                        "velocity_columns": ["vel1", "vel2", "vel3"],
                        "cell_size": 1.0,
                    },
                ),
                PanelConfig(
                    id="wave_energy",
                    type=PanelType.HEATMAP,
                    title="Wave Energy Spectrum",
                    position=PanelPosition(row=1, col=1, width=1, height=1),
                    config={
                        "data_source": "pnore_data",
                        "x": "start_frequency",
                        "y": "received_at",
                        "z": "energy_densities",
                    },
                ),
            ],
        )

    def save(self, name: str | None = None) -> Path:
        """Save the dashboard configuration to a YAML file."""
        config_dir = self.get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)

        filename = name or self._slugify(self.name)
        config_path = config_dir / f"{filename}.yaml"

        # Convert to dict, handling Pydantic models
        data = self.model_dump(mode="json")

        with config_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        return config_path

    def delete(self) -> bool:
        """Delete this dashboard configuration file."""
        config_path = self.get_config_dir() / f"{self._slugify(self.name)}.yaml"
        if config_path.exists():
            config_path.unlink()
            return True
        return False

    def add_panel(self, panel: PanelConfig) -> None:
        """Add a panel to the dashboard."""
        # Ensure unique ID
        existing_ids = {p.id for p in self.panels}
        if panel.id in existing_ids:
            raise ValueError(f"Panel with ID '{panel.id}' already exists")
        self.panels.append(panel)

    def remove_panel(self, panel_id: str) -> bool:
        """Remove a panel from the dashboard by ID."""
        for i, panel in enumerate(self.panels):
            if panel.id == panel_id:
                self.panels.pop(i)
                return True
        return False

    def get_panel(self, panel_id: str) -> PanelConfig | None:
        """Get a panel by ID."""
        for panel in self.panels:
            if panel.id == panel_id:
                return panel
        return None

    @staticmethod
    def _slugify(name: str) -> str:
        """Convert name to filesystem-safe slug."""
        return name.lower().replace(" ", "_").replace("-", "_")


# Dashboard templates for common use cases
DASHBOARD_TEMPLATES = {
    "overview": DashboardConfig(
        name="Overview",
        description="General ADCP data overview",
        layout=LayoutConfig(columns=2, rows=2),
        panels=[
            PanelConfig(
                id="sensor_table",
                type=PanelType.TABLE,
                title="Latest Sensor Readings",
                position=PanelPosition(row=0, col=0),
                config={"data_source": "pnors_df100", "limit": 50},
            ),
            PanelConfig(
                id="temp_pressure",
                type=PanelType.TIME_SERIES,
                title="Temperature & Pressure",
                position=PanelPosition(row=0, col=1),
                config={
                    "series": [
                        {"source": "pnors_df100", "y": "temperature", "label": "Temp"},
                        {"source": "pnors_df100", "y": "pressure", "label": "Pressure"},
                    ],
                },
            ),
        ],
    ),
    "velocity_analysis": DashboardConfig(
        name="Velocity Analysis",
        description="Current velocity profiling and analysis with sensor data",
        layout=LayoutConfig(columns=3, rows=3),
        panels=[
            PanelConfig(
                id="sensor_table",
                type=PanelType.TABLE,
                title="Sensor Data (PNORS)",
                position=PanelPosition(row=0, col=0),
                config={"data_source": "pnors_data", "limit": 50, "time_range": "24h"},
            ),
            PanelConfig(
                id="sensor12_table",
                type=PanelType.TABLE,
                title="Sensor Data 12 (PNORS12)",
                position=PanelPosition(row=0, col=1),
                config={"data_source": "pnors12", "limit": 50, "time_range": "24h"},
            ),
            PanelConfig(
                id="sensor34_table",
                type=PanelType.TABLE,
                title="Sensor Data 34 (PNORS34)",
                position=PanelPosition(row=0, col=2),
                config={"data_source": "pnors34", "limit": 50, "time_range": "24h"},
            ),
            PanelConfig(
                id="velocity_table",
                type=PanelType.TABLE,
                title="Velocity Data (PNORC)",
                position=PanelPosition(row=1, col=0),
                config={"data_source": "pnorc12", "limit": 100, "time_range": "24h"},
            ),
            PanelConfig(
                id="velocity_profile",
                type=PanelType.VELOCITY_PROFILE,
                title="Depth Profile",
                position=PanelPosition(row=1, col=1, width=2),
                config={"data_source": "pnorc12", "time_range": "24h"},
            ),
            PanelConfig(
                id="temp_pressure",
                type=PanelType.TIME_SERIES,
                title="Temperature & Pressure",
                position=PanelPosition(row=2, col=0, width=3),
                config={
                    "series": [
                        {"source": "pnors_data", "y": "temperature", "label": "Temp (°C)"},
                        {"source": "pnors_data", "y": "pressure", "label": "Pressure (dbar)"},
                    ],
                    "time_range": "24h",
                },
            ),
        ],
    ),
    "wave_analysis": DashboardConfig(
        name="Wave Analysis",
        description="Comprehensive wave spectrum and directional analysis",
        layout=LayoutConfig(columns=3, rows=4),
        panels=[
            PanelConfig(
                id="wave_params",
                type=PanelType.TABLE,
                title="Bulk Wave Parameters (PNORW)",
                position=PanelPosition(row=0, col=0),
                config={"data_source": "pnorw_data", "limit": 20},
            ),
            PanelConfig(
                id="wave_bands",
                type=PanelType.TABLE,
                title="Wave Band Parameters (PNORB)",
                position=PanelPosition(row=0, col=1),
                config={"data_source": "pnorb_data", "limit": 20},
            ),
            PanelConfig(
                id="directional_spectrum",
                type=PanelType.POLAR,
                title="Directional Spectrum (PNORWD)",
                position=PanelPosition(row=0, col=2, height=2),
                config={"time_range": "7d"},
            ),
            PanelConfig(
                id="wave_ener_heatmap",
                type=PanelType.HEATMAP,
                title="Wave Energy Density Heatmap",
                position=PanelPosition(row=1, col=0, width=2, height=1),
                config={"data_source": "pnore_data", "colorscale": "Plasma", "time_range": "7d"},
            ),
            PanelConfig(
                id="wave_amp_heatmap",
                type=PanelType.AMPLITUDE_HEATMAP,
                title="Signal Strength Heatmap",
                position=PanelPosition(row=2, col=0, width=2, height=1),
                config={"data_source": "pnorc12", "colorscale": "Jet", "time_range": "7d"},
            ),
            PanelConfig(
                id="fourier_a1",
                type=PanelType.SPECTRUM,
                title="Fourier A1 Coefficients",
                position=PanelPosition(row=2, col=0),
                config={"data_source": "pnorf_data", "coefficient": "A1"},
            ),
            PanelConfig(
                id="fourier_b1",
                type=PanelType.SPECTRUM,
                title="Fourier B1 Coefficients",
                position=PanelPosition(row=2, col=1),
                config={"data_source": "pnorf_data", "coefficient": "B1"},
            ),
            PanelConfig(
                id="fourier_a2",
                type=PanelType.SPECTRUM,
                title="Fourier A2 Coefficients",
                position=PanelPosition(row=2, col=2),
                config={"data_source": "pnorf_data", "coefficient": "A2"},
            ),
            PanelConfig(
                id="fourier_b2",
                type=PanelType.SPECTRUM,
                title="Fourier B2 Coefficients",
                position=PanelPosition(row=3, col=0),
                config={"data_source": "pnorf_data", "coefficient": "B2"},
            ),
            PanelConfig(
                id="wave_full_table",
                type=PanelType.TABLE,
                title="Full Wave Data View (Joined)",
                position=PanelPosition(row=3, col=1, width=2),
                config={
                    "data_source": "wave_measurement_full",
                    "columns": [
                        "received_at",
                        "measurement_date",
                        "measurement_time",
                        "hm0",
                        "tp",
                        "main_dir",
                        "band_hm0",
                        "band_tp",
                        "band_main_dir",
                        "coefficient_flag",
                        "direction_type",
                    ],
                    "limit": 50,
                },
            ),
        ],
    ),
}


def get_template(template_name: str) -> DashboardConfig:
    """Get a dashboard template by name."""
    if template_name not in DASHBOARD_TEMPLATES:
        raise ValueError(
            f"Unknown template: {template_name}. Available: {list(DASHBOARD_TEMPLATES.keys())}",
        )
    return DASHBOARD_TEMPLATES[template_name].model_copy(deep=True)
