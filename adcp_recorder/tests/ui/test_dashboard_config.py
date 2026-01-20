"""Unit tests for dashboard configuration system."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Skip this test module if optional UI dependencies are missing
pytest.importorskip("yaml")
pytest.importorskip("pydantic")

from adcp_recorder.ui.config import (
    DASHBOARD_TEMPLATES,
    DashboardConfig,
    LayoutConfig,
    PanelConfig,
    PanelPosition,
    PanelType,
    SeriesConfig,
    SpectrumPanelConfig,
    TablePanelConfig,
    get_template,
)


class TestPanelConfig:
    """Tests for panel configuration classes."""

    def test_panel_position_defaults(self):
        """Test default position values."""
        pos = PanelPosition()
        assert pos.row == 0
        assert pos.col == 0
        assert pos.width == 1
        assert pos.height == 1

    def test_panel_position_validation(self):
        """Test position validation."""
        pos = PanelPosition(row=2, col=3, width=2, height=1)
        assert pos.row == 2
        assert pos.col == 3

    def test_series_config_color_validation(self):
        """Test color must be hex format."""
        # Valid color
        series = SeriesConfig(source="test", y="temp", color="#FF6B6B")
        assert series.color == "#FF6B6B"

        # Invalid color - should raise
        with pytest.raises(ValueError):
            SeriesConfig(source="test", y="temp", color="red")

    def test_table_panel_config(self):
        """Test table panel configuration."""
        config = TablePanelConfig(
            data_source="pnors_df100",
            columns=["temp", "pressure"],
            limit=50,
        )
        assert config.data_source == "pnors_df100"
        assert len(config.columns) == 2
        assert config.limit == 50

    def test_spectrum_panel_config_validation(self):
        """Test coefficient validation."""
        config = SpectrumPanelConfig(coefficient="A1")
        assert config.coefficient == "A1"

        with pytest.raises(ValueError):
            SpectrumPanelConfig(coefficient="C1")

    def test_panel_config_get_typed_config(self):
        """Test typed config extraction."""
        panel = PanelConfig(
            id="test",
            type=PanelType.TABLE,
            config={"data_source": "pnors_df100", "limit": 100},
        )
        typed = panel.get_typed_config()
        assert isinstance(typed, TablePanelConfig)
        assert typed.data_source == "pnors_df100"

    def test_panel_config_unknown_type(self):
        """Test error on unknown panel type."""
        panel = PanelConfig.model_construct(id="test", type="UNKNOWN")
        with pytest.raises(ValueError, match="Unknown panel type"):
            panel.get_typed_config()


class TestLayoutConfig:
    """Tests for layout configuration."""

    def test_default_layout(self):
        """Test default layout values."""
        layout = LayoutConfig()
        assert layout.columns == 3
        assert layout.rows == 2

    def test_layout_bounds(self):
        """Test layout bounds validation."""
        # Valid
        layout = LayoutConfig(columns=4, rows=5)
        assert layout.columns == 4

        # Would fail with Pydantic validation if out of bounds
        with pytest.raises(ValueError):
            LayoutConfig(columns=10)


class TestDashboardConfig:
    """Tests for dashboard configuration."""

    def test_create_default(self):
        """Test default dashboard creation."""
        dashboard = DashboardConfig.create_default("test")
        assert dashboard.name == "test"
        assert len(dashboard.panels) > 0
        assert dashboard.layout.columns > 0

    def test_add_panel(self):
        """Test adding panels."""
        dashboard = DashboardConfig(name="test", panels=[])
        panel = PanelConfig(id="new_panel", type=PanelType.TABLE)

        dashboard.add_panel(panel)
        assert len(dashboard.panels) == 1

        # Duplicate ID should raise
        with pytest.raises(ValueError):
            dashboard.add_panel(panel)

    def test_remove_panel(self):
        """Test removing panels."""
        panel = PanelConfig(id="to_remove", type=PanelType.TABLE)
        dashboard = DashboardConfig(name="test", panels=[panel])

        assert dashboard.remove_panel("to_remove") is True
        assert len(dashboard.panels) == 0
        assert dashboard.remove_panel("nonexistent") is False

    def test_get_panel(self):
        """Test getting panel by ID."""
        panel = PanelConfig(id="target", type=PanelType.TABLE)
        dashboard = DashboardConfig(name="test", panels=[panel])

        found = dashboard.get_panel("target")
        assert found is not None
        assert found.id == "target"

        assert dashboard.get_panel("nonexistent") is None

    def test_slugify(self):
        """Test name slugification."""
        assert DashboardConfig._slugify("My Dashboard") == "my_dashboard"
        assert DashboardConfig._slugify("Test-Dashboard") == "test_dashboard"

    def test_save_and_load(self):
        """Test YAML save and load roundtrip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock config dir
            with patch.object(DashboardConfig, "get_config_dir", return_value=Path(tmpdir)):
                dashboard = DashboardConfig(
                    name="Test Dashboard",
                    description="A test dashboard",
                    panels=[
                        PanelConfig(
                            id="panel1",
                            type=PanelType.TABLE,
                            title="Test Panel",
                            config={"data_source": "test_table"},
                        )
                    ],
                )

                # Save
                path = dashboard.save("test_dashboard")
                assert path.exists()
                assert path.suffix == ".yaml"

                # Load
                loaded = DashboardConfig.load("test_dashboard")
                assert loaded.name == "Test Dashboard"
                assert loaded.description == "A test dashboard"
                assert len(loaded.panels) == 1
                assert loaded.panels[0].id == "panel1"

    def test_list_dashboards(self):
        """Test listing saved dashboards."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(DashboardConfig, "get_config_dir", return_value=Path(tmpdir)):
                # Initially empty
                assert DashboardConfig.list_dashboards() == []

                # Create some dashboards
                DashboardConfig(name="Dash1").save("dash1")
                DashboardConfig(name="Dash2").save("dash2")

                dashboards = DashboardConfig.list_dashboards()
                assert len(dashboards) == 2
                assert "dash1" in dashboards
                assert "dash2" in dashboards

    def test_get_config_dir(self):
        """Test getting the configuration directory."""
        # This will call RecorderConfig.get_default_config_dir()
        config_dir = DashboardConfig.get_config_dir()
        assert config_dir.name == "dashboards"
        assert ".adcp-recorder" in str(config_dir)

    def test_list_dashboards_missing_dir(self):
        """Test listing dashboards when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_dir = Path(tmpdir) / "nonexistent"
            with patch.object(DashboardConfig, "get_config_dir", return_value=bad_dir):
                assert DashboardConfig.list_dashboards() == []

    def test_load_missing_file(self):
        """Test error when loading nonexistent dashboard."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(DashboardConfig, "get_config_dir", return_value=Path(tmpdir)):
                with pytest.raises(FileNotFoundError):
                    DashboardConfig.load("nonexistent")

    def test_load_or_default(self):
        """Test load_or_default fallback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(DashboardConfig, "get_config_dir", return_value=Path(tmpdir)):
                # Fallback to default
                dash = DashboardConfig.load_or_default("new_dash")
                assert dash.name == "new_dash"

                # Load existing
                dash.save("new_dash")
                loaded = DashboardConfig.load_or_default("new_dash")
                assert loaded.name == "new_dash"

    def test_delete_success_and_failure(self):
        """Test deleting dashboards."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(DashboardConfig, "get_config_dir", return_value=Path(tmpdir)):
                dash = DashboardConfig(name="To Delete")
                # Failure case
                assert dash.delete() is False

                # Success case
                dash.save()
                assert dash.delete() is True
                assert dash.delete() is False


class TestDashboardTemplates:
    """Tests for dashboard templates."""

    def test_templates_exist(self):
        """Test that templates are defined."""
        assert "overview" in DASHBOARD_TEMPLATES
        assert "velocity_analysis" in DASHBOARD_TEMPLATES
        assert "wave_analysis" in DASHBOARD_TEMPLATES

    def test_get_template(self):
        """Test getting a template."""
        template = get_template("overview")
        assert template.name == "Overview"
        assert len(template.panels) > 0

    def test_get_template_unknown(self):
        """Test error on unknown template."""
        with pytest.raises(ValueError):
            get_template("nonexistent_template")

    def test_template_is_copy(self):
        """Test that get_template returns a copy."""
        template1 = get_template("overview")
        template2 = get_template("overview")

        template1.name = "Modified"
        assert template2.name == "Overview"  # Original unchanged
