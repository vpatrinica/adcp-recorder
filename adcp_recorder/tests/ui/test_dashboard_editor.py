"""Tests for Dashboard Editor page - full coverage.

Strategy: Streamlit's `st.rerun()` is mocked as a no-op (not raising) because
MagicMock context managers swallow exceptions inside `with` blocks.  We verify
side-effects (session state changes, method calls) instead of expecting
exceptions to propagate.
"""

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("streamlit")

from adcp_recorder.ui.config import PanelType
from adcp_recorder.ui.pages.dashboard_editor import (
    _render_add_panel_form,
    _render_create_dashboard,
    _render_dashboard_editor_form,
    _render_dashboard_list,
    _render_templates,
    render_dashboard_editor,
)


def _make_columns(arg):
    """Create the right number of column mocks based on argument."""
    if isinstance(arg, int):
        count = arg
    elif isinstance(arg, (list, tuple)):
        count = len(arg)
    else:
        count = 2
    cols = []
    for _ in range(count):
        m = MagicMock()
        m.__enter__ = MagicMock(return_value=m)
        m.__exit__ = MagicMock(return_value=False)
        cols.append(m)
    return cols


@pytest.fixture
def mock_st():
    """Mock streamlit module in dashboard_editor.

    Note: st.rerun() is a no-op (default MagicMock) rather than raising,
    because MagicMock context managers swallow exceptions.  Tests verify
    that rerun() *was called* instead.
    """
    with patch("adcp_recorder.ui.pages.dashboard_editor.st") as mock_st:
        mock_st.session_state = {}
        # Tabs
        tabs = []
        for _ in range(3):
            t = MagicMock()
            t.__enter__ = MagicMock(return_value=t)
            t.__exit__ = MagicMock(return_value=False)
            tabs.append(t)
        mock_st.tabs.return_value = tabs
        # columns
        mock_st.columns.side_effect = _make_columns
        # form
        form_cm = MagicMock()
        form_cm.__enter__ = MagicMock(return_value=form_cm)
        form_cm.__exit__ = MagicMock(return_value=False)
        mock_st.form.return_value = form_cm
        # container
        container_cm = MagicMock()
        container_cm.__enter__ = MagicMock(return_value=container_cm)
        container_cm.__exit__ = MagicMock(return_value=False)
        mock_st.container.return_value = container_cm
        # expander
        expander_cm = MagicMock()
        expander_cm.__enter__ = MagicMock(return_value=expander_cm)
        expander_cm.__exit__ = MagicMock(return_value=False)
        mock_st.expander.return_value = expander_cm
        # popover
        popover_cm = MagicMock()
        popover_cm.__enter__ = MagicMock(return_value=popover_cm)
        popover_cm.__exit__ = MagicMock(return_value=False)
        mock_st.popover.return_value = popover_cm
        # rerun: no-op (does NOT raise); tests assert it was called
        yield mock_st


# ---------------------------------------------------------------------------
# render_dashboard_editor (entry point)
# ---------------------------------------------------------------------------
class TestRenderDashboardEditor:
    """Test the main render_dashboard_editor entry point."""

    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_renders_header_and_tabs(self, mock_dc, mock_st):
        """Main function renders header, caption, and 3 tabs."""
        mock_dc.list_dashboards.return_value = []
        mock_dc.get_templates.return_value = {}
        dl = MagicMock()
        render_dashboard_editor(dl)

        mock_st.header.assert_called_once()
        assert mock_st.caption.call_count >= 1
        mock_st.tabs.assert_called_once()


# ---------------------------------------------------------------------------
# _render_dashboard_list
# ---------------------------------------------------------------------------
class TestRenderDashboardList:
    """Test _render_dashboard_list function."""

    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_no_dashboards_shows_info(self, mock_dc, mock_st):
        """When no dashboards exist, show info message."""
        mock_dc.list_dashboards.return_value = []
        _render_dashboard_list()
        mock_st.subheader.assert_called_once_with("Saved Dashboards")
        mock_st.info.assert_called_once()

    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_lists_dashboards(self, mock_dc, mock_st):
        """Lists existing dashboards with edit/delete buttons."""
        mock_dashboard = MagicMock()
        mock_dashboard.name = "Test Dashboard"
        mock_dashboard.description = "Test description"
        mock_dashboard.panels = [MagicMock(), MagicMock()]

        mock_dc.list_dashboards.return_value = ["test_dashboard"]
        mock_dc.load.return_value = mock_dashboard
        mock_st.button.return_value = False

        _render_dashboard_list()

        mock_st.subheader.assert_called_once_with("Saved Dashboards")
        mock_dc.load.assert_called_once_with("test_dashboard")
        mock_st.divider.assert_called()

    @patch("adcp_recorder.ui.pages.dashboard_editor._render_dashboard_editor_form")
    @patch("adcp_recorder.ui.pages.dashboard_editor._render_add_panel_form")
    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_edit_button_sets_session_state(self, mock_dc, _mock_add, _mock_form, mock_st):
        """Clicking edit sets editing_dashboard in session state and calls rerun."""
        mock_dashboard = MagicMock()
        mock_dashboard.name = "Test"
        mock_dashboard.description = ""
        mock_dashboard.panels = []

        mock_dc.list_dashboards.return_value = ["test"]
        mock_dc.load.return_value = mock_dashboard

        # edit=True, delete=False, then "Done Editing"=False
        mock_st.button.side_effect = [True, False, False]

        _render_dashboard_list()

        assert mock_st.session_state.get("editing_dashboard") == "test"
        mock_st.rerun.assert_called()

    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_delete_button_first_click_confirms(self, mock_dc, mock_st):
        """First delete click sets confirmation state."""
        mock_dashboard = MagicMock()
        mock_dashboard.name = "Test"
        mock_dashboard.description = ""
        mock_dashboard.panels = []

        mock_dc.list_dashboards.return_value = ["test"]
        mock_dc.load.return_value = mock_dashboard
        mock_st.button.side_effect = [False, True]

        _render_dashboard_list()

        assert mock_st.session_state.get("confirm_delete_test") is True
        mock_st.warning.assert_called_once()

    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_delete_button_second_click_deletes(self, mock_dc, mock_st):
        """Second delete click (with confirmation) deletes dashboard."""
        mock_dashboard = MagicMock()
        mock_dashboard.name = "Test"
        mock_dashboard.description = ""
        mock_dashboard.panels = []

        mock_dc.list_dashboards.return_value = ["test"]
        mock_dc.load.return_value = mock_dashboard
        mock_st.session_state["confirm_delete_test"] = True
        mock_st.button.side_effect = [False, True]

        _render_dashboard_list()

        mock_dashboard.delete.assert_called_once()
        mock_st.success.assert_called_once()
        mock_st.rerun.assert_called()

    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_load_error_shows_error(self, mock_dc, mock_st):
        """Load failure shows error message."""
        mock_dc.list_dashboards.return_value = ["broken"]
        mock_dc.load.side_effect = Exception("corrupt file")
        mock_st.button.return_value = False

        _render_dashboard_list()
        mock_st.error.assert_called()

    @patch("adcp_recorder.ui.pages.dashboard_editor._render_dashboard_editor_form")
    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_editing_dashboard_renders_editor(self, mock_dc, mock_form, mock_st):
        """When editing_dashboard is in session_state, show editor form."""
        # Need at least one dashboard so we don't early-return at line 50
        mock_dashboard = MagicMock()
        mock_dashboard.name = "Existing"
        mock_dashboard.description = ""
        mock_dashboard.panels = []
        mock_dc.list_dashboards.return_value = ["existing"]
        mock_dc.load.return_value = mock_dashboard
        mock_st.session_state["editing_dashboard"] = "my_dash"
        mock_st.button.return_value = False

        _render_dashboard_list()

        mock_form.assert_called_once_with("my_dash")

    @patch("adcp_recorder.ui.pages.dashboard_editor._render_dashboard_editor_form")
    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_done_editing_clears_session(self, mock_dc, mock_form, mock_st):
        """Clicking Done Editing clears session state and reruns."""
        # Need at least one dashboard so we don't early-return at line 50
        mock_dashboard = MagicMock()
        mock_dashboard.name = "Existing"
        mock_dashboard.description = ""
        mock_dashboard.panels = []
        mock_dc.list_dashboards.return_value = ["existing"]
        mock_dc.load.return_value = mock_dashboard
        mock_st.session_state["editing_dashboard"] = "my_dash"
        # Buttons: edit=False, delete=False (for the listed dashboard), Done Editing=True
        mock_st.button.side_effect = [False, False, True]

        _render_dashboard_list()

        assert "editing_dashboard" not in mock_st.session_state
        mock_st.rerun.assert_called()


# ---------------------------------------------------------------------------
# _render_create_dashboard
# ---------------------------------------------------------------------------
class TestRenderCreateDashboard:
    """Test _render_create_dashboard function."""

    def test_renders_form_elements(self, mock_st):
        """Form renders all input elements."""
        mock_st.form_submit_button.return_value = False
        _render_create_dashboard()
        mock_st.subheader.assert_called_once_with("Create New Dashboard")
        mock_st.form.assert_called_once()

    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_submit_empty_name_shows_error(self, mock_dc, mock_st):
        """Submitting with empty name shows error."""
        mock_st.form_submit_button.return_value = True
        mock_st.text_input.return_value = ""
        mock_st.text_area.return_value = ""
        mock_st.number_input.side_effect = [2, 2, 0]
        mock_st.selectbox.return_value = "24h"

        _render_create_dashboard()
        mock_st.error.assert_called_once_with("Dashboard name is required")

    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_submit_valid_creates_dashboard(self, mock_dc, mock_st):
        """Submitting with valid name creates and saves dashboard."""
        mock_st.form_submit_button.return_value = True
        mock_st.text_input.return_value = "My Dashboard"
        mock_st.text_area.return_value = "Description"
        mock_st.number_input.side_effect = [2, 2, 0]
        mock_st.selectbox.return_value = "24h"

        mock_instance = MagicMock()
        mock_instance.save.return_value = "/path/to/config.yaml"
        mock_dc.return_value = mock_instance

        _render_create_dashboard()

        mock_dc.assert_called_once()
        mock_instance.save.assert_called_once()
        mock_st.success.assert_called_once()

    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_submit_exception_shows_error(self, mock_dc, mock_st):
        """Exception during creation shows error."""
        mock_st.form_submit_button.return_value = True
        mock_st.text_input.return_value = "My Dashboard"
        mock_st.text_area.return_value = ""
        mock_st.number_input.side_effect = [2, 2, 0]
        mock_st.selectbox.return_value = "24h"
        mock_dc.side_effect = Exception("validation error")

        _render_create_dashboard()
        mock_st.error.assert_called()


# ---------------------------------------------------------------------------
# _render_templates
# ---------------------------------------------------------------------------
class TestRenderTemplates:
    """Test _render_templates function."""

    @patch("adcp_recorder.ui.pages.dashboard_editor.DASHBOARD_TEMPLATES", {})
    def test_empty_templates(self, mock_st):
        """No templates renders header only."""
        _render_templates()
        mock_st.subheader.assert_called_once()
        mock_st.caption.assert_called_once()

    @patch("adcp_recorder.ui.pages.dashboard_editor.get_template")
    @patch("adcp_recorder.ui.pages.dashboard_editor.DASHBOARD_TEMPLATES")
    def test_lists_templates(self, mock_templates, mock_get, mock_st):
        """Templates are listed with Use Template button."""
        template = MagicMock()
        template.name = "Overview"
        template.description = "General overview"
        panel = MagicMock()
        panel.title = "Panel 1"
        panel.id = "p1"
        panel.type = MagicMock()
        panel.type.value = "table"
        template.panels = [panel]

        mock_templates.items.return_value = [("overview", template)]
        mock_st.button.return_value = False

        _render_templates()
        mock_st.subheader.assert_called_once()

    @patch("adcp_recorder.ui.pages.dashboard_editor.get_template")
    @patch("adcp_recorder.ui.pages.dashboard_editor.DASHBOARD_TEMPLATES")
    def test_use_template_creates_copy(self, mock_templates, mock_get, mock_st):
        """Clicking Use Template creates a copy and calls rerun."""
        template = MagicMock()
        template.name = "Overview"
        template.description = "Desc"
        template.panels = []

        mock_templates.items.return_value = [("overview", template)]
        mock_st.button.return_value = True

        new_dash = MagicMock()
        new_dash.save.return_value = "/path/to/copy.yaml"
        mock_get.return_value = new_dash

        _render_templates()

        mock_get.assert_called_once_with("overview")
        assert new_dash.name == "Overview (Copy)"
        new_dash.save.assert_called_once()
        mock_st.success.assert_called_once()
        mock_st.rerun.assert_called()

    @patch("adcp_recorder.ui.pages.dashboard_editor.get_template")
    @patch("adcp_recorder.ui.pages.dashboard_editor.DASHBOARD_TEMPLATES")
    def test_use_template_failure(self, mock_templates, mock_get, mock_st):
        """Template creation failure shows error."""
        template = MagicMock()
        template.name = "Overview"
        template.description = "Desc"
        template.panels = []

        mock_templates.items.return_value = [("overview", template)]
        mock_st.button.return_value = True
        mock_get.side_effect = Exception("template error")

        _render_templates()
        mock_st.error.assert_called()


# ---------------------------------------------------------------------------
# _render_dashboard_editor_form
# ---------------------------------------------------------------------------
class TestRenderDashboardEditorForm:
    """Test _render_dashboard_editor_form function."""

    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_load_error_shows_error(self, mock_dc, mock_st):
        """Load failure shows error and returns."""
        mock_dc.load.side_effect = Exception("not found")
        _render_dashboard_editor_form("bad_dash")
        mock_st.error.assert_called()

    @patch("adcp_recorder.ui.pages.dashboard_editor._render_add_panel_form")
    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_renders_empty_dashboard(self, mock_dc, mock_add, mock_st):
        """Dashboard with no panels shows info message."""
        mock_dashboard = MagicMock()
        mock_dashboard.name = "Test"
        mock_dashboard.description = "Desc"
        mock_dashboard.layout = MagicMock(columns=2, rows=2)
        mock_dashboard.refresh_interval = 0
        mock_dashboard.panels = []

        mock_dc.load.return_value = mock_dashboard
        mock_st.text_input.return_value = "Test"
        mock_st.text_area.return_value = "Desc"
        mock_st.number_input.side_effect = [2, 2, 0]
        mock_st.button.return_value = False

        _render_dashboard_editor_form("test")
        mock_st.info.assert_called()

    @patch("adcp_recorder.ui.pages.dashboard_editor._render_add_panel_form")
    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_save_settings_updates_dashboard(self, mock_dc, mock_add, mock_st):
        """Save Settings button updates dashboard properties."""
        mock_dashboard = MagicMock()
        mock_dashboard.name = "Old Name"
        mock_dashboard.description = "Old Desc"
        mock_dashboard.layout = MagicMock(columns=2, rows=2)
        mock_dashboard.refresh_interval = 0
        mock_dashboard.panels = []

        mock_dc.load.return_value = mock_dashboard
        mock_st.text_input.return_value = "New Name"
        mock_st.text_area.return_value = "New Desc"
        mock_st.number_input.side_effect = [3, 4, 60]
        mock_st.button.return_value = True

        _render_dashboard_editor_form("test")

        assert mock_dashboard.name == "New Name"
        assert mock_dashboard.description == "New Desc"
        mock_dashboard.save.assert_called_once_with("test")
        mock_st.success.assert_called()

    @patch("adcp_recorder.ui.pages.dashboard_editor._render_add_panel_form")
    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_renders_panels_with_positions(self, mock_dc, mock_add, mock_st):
        """Dashboard with panels renders position info and controls."""
        panel = MagicMock()
        panel.id = "panel_1"
        panel.title = "My Panel"
        panel.type = MagicMock(value="table")
        panel.position = MagicMock(row=0, col=1, width=2, height=1)

        mock_dashboard = MagicMock()
        mock_dashboard.name = "Test"
        mock_dashboard.description = "Desc"
        mock_dashboard.layout = MagicMock(columns=2, rows=2)
        mock_dashboard.refresh_interval = 0
        mock_dashboard.panels = [panel]

        mock_dc.load.return_value = mock_dashboard
        mock_st.text_input.return_value = "Test"
        mock_st.text_area.return_value = "Desc"
        mock_st.number_input.side_effect = [2, 2, 0, 0, 0]
        mock_st.button.return_value = False

        _render_dashboard_editor_form("test")
        mock_st.divider.assert_called()

    @patch("adcp_recorder.ui.pages.dashboard_editor._render_add_panel_form")
    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_update_panel_position(self, mock_dc, mock_add, mock_st):
        """Clicking Update on panel position saves and calls rerun."""
        panel = MagicMock()
        panel.id = "panel_1"
        panel.title = "My Panel"
        panel.type = MagicMock(value="table")
        panel.position = MagicMock(row=0, col=0, width=1, height=1)

        mock_dashboard = MagicMock()
        mock_dashboard.name = "Test"
        mock_dashboard.description = "Desc"
        mock_dashboard.layout = MagicMock(columns=2, rows=2)
        mock_dashboard.refresh_interval = 0
        mock_dashboard.panels = [panel]

        mock_dc.load.return_value = mock_dashboard
        mock_st.text_input.return_value = "Test"
        mock_st.text_area.return_value = "Desc"
        mock_st.number_input.side_effect = [2, 2, 0, 1, 2]
        # Save Settings=False, Update=True, Delete=False
        mock_st.button.side_effect = [False, True, False]

        _render_dashboard_editor_form("test")

        assert panel.position.row == 1
        assert panel.position.col == 2
        mock_dashboard.save.assert_called_with("test")
        mock_st.rerun.assert_called()

    @patch("adcp_recorder.ui.pages.dashboard_editor._render_add_panel_form")
    @patch("adcp_recorder.ui.pages.dashboard_editor.DashboardConfig")
    def test_remove_panel(self, mock_dc, mock_add, mock_st):
        """Clicking delete removes panel from dashboard."""
        panel = MagicMock()
        panel.id = "panel_1"
        panel.title = "My Panel"
        panel.type = MagicMock(value="table")
        panel.position = MagicMock(row=0, col=0, width=1, height=1)

        mock_dashboard = MagicMock()
        mock_dashboard.name = "Test"
        mock_dashboard.description = "Desc"
        mock_dashboard.layout = MagicMock(columns=2, rows=2)
        mock_dashboard.refresh_interval = 0
        mock_dashboard.panels = [panel]

        mock_dc.load.return_value = mock_dashboard
        mock_st.text_input.return_value = "Test"
        mock_st.text_area.return_value = "Desc"
        mock_st.number_input.side_effect = [2, 2, 0, 0, 0]
        # Save Settings=False, Update=False, Delete=True
        mock_st.button.side_effect = [False, False, True]

        _render_dashboard_editor_form("test")

        mock_dashboard.remove_panel.assert_called_once_with("panel_1")
        mock_dashboard.save.assert_called()
        mock_st.rerun.assert_called()


# ---------------------------------------------------------------------------
# _render_add_panel_form
# ---------------------------------------------------------------------------
class TestRenderAddPanelForm:
    """Test _render_add_panel_form function."""

    def test_add_table_panel(self, mock_st):
        """Adding a TABLE panel includes data_source and limit config."""
        mock_dashboard = MagicMock()
        mock_st.text_input.side_effect = ["my_panel", "My Panel", "pnors_df100"]
        mock_st.selectbox.return_value = PanelType.TABLE.value
        mock_st.number_input.side_effect = [0, 0, 100]
        mock_st.button.return_value = True

        _render_add_panel_form(mock_dashboard, "test_dash")

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.TABLE
        assert panel.config["data_source"] == "pnors_df100"
        mock_dashboard.save.assert_called_once_with("test_dash")
        mock_st.rerun.assert_called()

    def test_add_time_series_panel(self, mock_st):
        """Adding a TIME_SERIES panel shows info message."""
        mock_dashboard = MagicMock()
        mock_st.text_input.side_effect = ["ts_panel", "Time Series"]
        mock_st.selectbox.return_value = PanelType.TIME_SERIES.value
        mock_st.number_input.side_effect = [0, 0]
        mock_st.button.return_value = True

        _render_add_panel_form(mock_dashboard, "test_dash")

        mock_st.info.assert_called()
        mock_dashboard.add_panel.assert_called_once()
        mock_st.rerun.assert_called()

    def test_add_spectrum_panel(self, mock_st):
        """Adding a SPECTRUM panel includes coefficient config."""
        mock_dashboard = MagicMock()
        mock_st.text_input.side_effect = ["spec_panel", "Spectrum"]
        mock_st.selectbox.side_effect = [PanelType.SPECTRUM.value, "A1"]
        mock_st.number_input.side_effect = [0, 0]
        mock_st.button.return_value = True

        _render_add_panel_form(mock_dashboard, "test_dash")

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.config["coefficient"] == "A1"
        mock_st.rerun.assert_called()

    def test_add_velocity_profile_panel(self, mock_st):
        """Adding a VELOCITY_PROFILE panel includes data_source config."""
        mock_dashboard = MagicMock()
        mock_st.text_input.side_effect = ["vp_panel", "Velocity", "pnorc_df101"]
        mock_st.selectbox.return_value = PanelType.VELOCITY_PROFILE.value
        mock_st.number_input.side_effect = [1, 1]
        mock_st.button.return_value = True

        _render_add_panel_form(mock_dashboard, "test_dash")

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.config["data_source"] == "pnorc_df101"
        mock_st.rerun.assert_called()

    def test_add_panel_empty_id_shows_error(self, mock_st):
        """Adding panel with empty ID shows error."""
        mock_dashboard = MagicMock()
        mock_st.text_input.side_effect = ["", "Title"]
        mock_st.selectbox.return_value = PanelType.TIME_SERIES.value
        mock_st.number_input.side_effect = [0, 0]
        mock_st.button.return_value = True

        _render_add_panel_form(mock_dashboard, "test_dash")

        mock_st.error.assert_called_once_with("Panel ID is required")
        mock_dashboard.add_panel.assert_not_called()

    def test_add_panel_exception_shows_error(self, mock_st):
        """Exception during panel creation shows error."""
        mock_dashboard = MagicMock()
        mock_dashboard.add_panel.side_effect = Exception("duplicate panel")
        mock_st.text_input.side_effect = ["dup_panel", "Dup"]
        mock_st.selectbox.return_value = PanelType.TIME_SERIES.value
        mock_st.number_input.side_effect = [0, 0]
        mock_st.button.return_value = True

        _render_add_panel_form(mock_dashboard, "test_dash")

        mock_st.error.assert_called()

    def test_add_panel_button_not_clicked(self, mock_st):
        """When Add Panel button is not clicked, nothing happens."""
        mock_dashboard = MagicMock()
        mock_st.text_input.side_effect = ["some_id", "Title"]
        mock_st.selectbox.return_value = PanelType.TIME_SERIES.value
        mock_st.number_input.side_effect = [0, 0]
        mock_st.button.return_value = False

        _render_add_panel_form(mock_dashboard, "test_dash")

        mock_dashboard.add_panel.assert_not_called()

    def test_add_heatmap_panel(self, mock_st):
        """Adding a HEATMAP panel (no extra config branch)."""
        mock_dashboard = MagicMock()
        mock_st.text_input.side_effect = ["hm_panel", "Heatmap"]
        mock_st.selectbox.return_value = PanelType.HEATMAP.value
        mock_st.number_input.side_effect = [0, 0]
        mock_st.button.return_value = True

        _render_add_panel_form(mock_dashboard, "test_dash")

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.HEATMAP

    def test_add_polar_panel(self, mock_st):
        """Adding a POLAR panel (no extra config branch)."""
        mock_dashboard = MagicMock()
        mock_st.text_input.side_effect = ["polar_panel", "Polar"]
        mock_st.selectbox.return_value = PanelType.POLAR.value
        mock_st.number_input.side_effect = [0, 0]
        mock_st.button.return_value = True

        _render_add_panel_form(mock_dashboard, "test_dash")

        mock_dashboard.add_panel.assert_called_once()
        panel = mock_dashboard.add_panel.call_args[0][0]
        assert panel.type == PanelType.POLAR
