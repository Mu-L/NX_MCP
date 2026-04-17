"""Tests for drawing tools (5 tools)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock

import pytest

from nx_mcp.nx_session import NXSession
from nx_mcp.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_handler(name: str):
    """Import the module (triggering registration) and return the handler."""
    import nx_mcp.tools.drawing as _mod  # noqa: F401 – registers tools
    return ToolRegistry.get_handler(name)


def run(coro):
    """Run an async coroutine synchronously in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


def _setup_session(mock_nx):
    """Wire up NXSession singleton with the mock session and work part."""
    mock_session = mock_nx._mock_session
    mock_work_part = mock_session.Parts.Work

    NXSession._instance = MagicMock(spec=NXSession)
    NXSession._instance.is_connected = True
    NXSession._instance.require.return_value = mock_session
    NXSession._instance.require_work_part.return_value = mock_work_part

    return mock_session, mock_work_part


# ---------------------------------------------------------------------------
# nx_create_drawing
# ---------------------------------------------------------------------------

class TestNxCreateDrawing:
    """Tests for nx_create_drawing tool."""

    def test_create_drawing_success(self, mock_nx):
        handler = _get_handler("nx_create_drawing")
        mock_session, mock_work_part = _setup_session(mock_nx)

        # Mock DrawingSheets builder
        mock_builder = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.Name = "Sheet1"
        mock_builder.Commit.return_value = mock_sheet
        mock_builder.Destroy = MagicMock()
        mock_work_part.DrawingSheets.CreateDrawingSheetBuilder.return_value = mock_builder

        result = run(handler(name="MySheet", size="A3", scale=1.0))
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["sheet_name"] == "Sheet1"
        assert data["data"]["size"] == "A3"
        assert data["data"]["scale"] == "1.0:1"
        mock_builder.Commit.assert_called_once()
        mock_builder.Destroy.assert_called_once()

    def test_create_drawing_invalid_size(self, mock_nx):
        handler = _get_handler("nx_create_drawing")
        _setup_session(mock_nx)

        result = run(handler(name="Sheet1", size="Z9", scale=1.0))
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_code"] == "NX_INVALID_PARAMS"
        assert "A0" in data["suggestion"] or "A3" in data["suggestion"]

    def test_create_drawing_default_params(self, mock_nx):
        handler = _get_handler("nx_create_drawing")
        mock_session, mock_work_part = _setup_session(mock_nx)

        mock_builder = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.Name = "Sheet1"
        mock_builder.Commit.return_value = mock_sheet
        mock_builder.Destroy = MagicMock()
        mock_work_part.DrawingSheets.CreateDrawingSheetBuilder.return_value = mock_builder

        result = run(handler())
        data = json.loads(result)

        assert data["status"] == "success"
        # Verify defaults were applied
        mock_builder.Name = "Sheet1"  # default name set on builder
        assert data["data"]["size"] == "A3"


# ---------------------------------------------------------------------------
# nx_add_base_view
# ---------------------------------------------------------------------------

class TestNxAddBaseView:
    """Tests for nx_add_base_view tool."""

    def test_add_base_view_success(self, mock_nx):
        handler = _get_handler("nx_add_base_view")
        mock_session, mock_work_part = _setup_session(mock_nx)

        # Mock DrawingSheets array
        mock_sheet = MagicMock()
        mock_sheet.Name = "Sheet1"
        mock_work_part.DrawingSheets.ToArray.return_value = [mock_sheet]

        # Mock DrawingViews builder
        mock_builder = MagicMock()
        mock_view = MagicMock()
        mock_view.Name = "BaseView1"
        mock_builder.Commit.return_value = mock_view
        mock_builder.Destroy = MagicMock()
        mock_work_part.DrawingViews.CreateBaseViewBuilder.return_value = mock_builder

        result = run(handler(drawing="Sheet1", body="Body1", view="front"))
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["view_name"] == "BaseView1"
        assert data["data"]["orientation"] == "front"
        assert data["data"]["drawing"] == "Sheet1"
        mock_builder.Commit.assert_called_once()

    def test_add_base_view_invalid_view(self, mock_nx):
        handler = _get_handler("nx_add_base_view")
        _setup_session(mock_nx)

        result = run(handler(drawing="Sheet1", body="Body1", view="diagonal"))
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_code"] == "NX_INVALID_PARAMS"

    def test_add_base_view_sheet_not_found(self, mock_nx):
        handler = _get_handler("nx_add_base_view")
        mock_session, mock_work_part = _setup_session(mock_nx)

        mock_work_part.DrawingSheets.ToArray.return_value = []

        result = run(handler(drawing="MissingSheet", body="Body1", view="front"))
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_code"] == "NX_NOT_FOUND"
        assert "MissingSheet" in data["message"]


# ---------------------------------------------------------------------------
# nx_add_projection_view
# ---------------------------------------------------------------------------

class TestNxAddProjectionView:
    """Tests for nx_add_projection_view tool."""

    def test_add_projection_view_success(self, mock_nx):
        handler = _get_handler("nx_add_projection_view")
        mock_session, mock_work_part = _setup_session(mock_nx)

        # Mock existing base view
        mock_base_view = MagicMock()
        mock_base_view.Name = "BaseView1"
        mock_work_part.DrawingViews.ToArray.return_value = [mock_base_view]

        # Mock projected view builder
        mock_builder = MagicMock()
        mock_proj_view = MagicMock()
        mock_proj_view.Name = "ProjView1"
        mock_builder.Commit.return_value = mock_proj_view
        mock_builder.Destroy = MagicMock()
        mock_work_part.DrawingViews.CreateProjectedViewBuilder.return_value = mock_builder

        result = run(handler(base_view="BaseView1", direction="right"))
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["view_name"] == "ProjView1"
        assert data["data"]["direction"] == "right"
        assert data["data"]["base_view"] == "BaseView1"

    def test_add_projection_view_invalid_direction(self, mock_nx):
        handler = _get_handler("nx_add_projection_view")
        _setup_session(mock_nx)

        result = run(handler(base_view="BaseView1", direction="diagonal"))
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_code"] == "NX_INVALID_PARAMS"

    def test_add_projection_view_base_not_found(self, mock_nx):
        handler = _get_handler("nx_add_projection_view")
        mock_session, mock_work_part = _setup_session(mock_nx)

        mock_work_part.DrawingViews.ToArray.return_value = []

        result = run(handler(base_view="MissingView", direction="right"))
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_code"] == "NX_NOT_FOUND"


# ---------------------------------------------------------------------------
# nx_add_dimension
# ---------------------------------------------------------------------------

class TestNxAddDimension:
    """Tests for nx_add_dimension tool."""

    def test_add_dimension_success(self, mock_nx):
        handler = _get_handler("nx_add_dimension")
        mock_session, mock_work_part = _setup_session(mock_nx)

        # Mock existing view
        mock_view = MagicMock()
        mock_view.Name = "BaseView1"
        mock_work_part.DrawingViews.ToArray.return_value = [mock_view]

        # Mock dimension builder
        mock_builder = MagicMock()
        mock_dim = MagicMock()
        mock_dim.Name = "Dim0"
        mock_builder.Commit.return_value = mock_dim
        mock_builder.Destroy = MagicMock()
        mock_work_part.Annotations.CreateDimensionBuilder.return_value = mock_builder

        result = run(handler(
            view="BaseView1",
            object1="Edge1",
            object2="Edge2",
            dim_type="horizontal",
        ))
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["dim_type"] == "horizontal"
        assert data["data"]["object1"] == "Edge1"
        assert data["data"]["object2"] == "Edge2"
        mock_builder.Commit.assert_called_once()

    def test_add_dimension_invalid_type(self, mock_nx):
        handler = _get_handler("nx_add_dimension")
        _setup_session(mock_nx)

        result = run(handler(view="V1", object1="E1", dim_type="chamfer"))
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_code"] == "NX_INVALID_PARAMS"

    def test_add_dimension_diameter_with_object2_rejected(self, mock_nx):
        handler = _get_handler("nx_add_dimension")
        _setup_session(mock_nx)

        result = run(handler(
            view="BaseView1",
            object1="Edge1",
            object2="Edge2",
            dim_type="diameter",
        ))
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_code"] == "NX_INVALID_PARAMS"
        assert "single object" in data["message"].lower()

    def test_add_dimension_view_not_found(self, mock_nx):
        handler = _get_handler("nx_add_dimension")
        mock_session, mock_work_part = _setup_session(mock_nx)

        mock_work_part.DrawingViews.ToArray.return_value = []

        result = run(handler(view="MissingView", object1="E1", dim_type="aligned"))
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_code"] == "NX_NOT_FOUND"

    def test_add_radius_dimension_single_object(self, mock_nx):
        handler = _get_handler("nx_add_dimension")
        mock_session, mock_work_part = _setup_session(mock_nx)

        mock_view = MagicMock()
        mock_view.Name = "V1"
        mock_work_part.DrawingViews.ToArray.return_value = [mock_view]

        mock_builder = MagicMock()
        mock_dim = MagicMock()
        mock_dim.Name = "RadDim0"
        mock_builder.Commit.return_value = mock_dim
        mock_builder.Destroy = MagicMock()
        mock_work_part.Annotations.CreateDimensionBuilder.return_value = mock_builder

        result = run(handler(view="V1", object1="Arc1", dim_type="radius"))
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["dim_type"] == "radius"
        assert data["data"]["object2"] is None


# ---------------------------------------------------------------------------
# nx_export_drawing_pdf
# ---------------------------------------------------------------------------

class TestNxExportDrawingPdf:
    """Tests for nx_export_drawing_pdf tool."""

    def test_export_pdf_success(self, mock_nx):
        handler = _get_handler("nx_export_drawing_pdf")
        mock_session, mock_work_part = _setup_session(mock_nx)

        # Mock PDF exporter
        mock_exporter = MagicMock()
        mock_exporter.Apply = MagicMock()
        mock_work_part.ExportManager.CreatePdfExporter.return_value = mock_exporter

        result = run(handler(path=r"C:\output\drawing.pdf"))
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["path"] == r"C:\output\drawing.pdf"
        assert "drawing.pdf" in data["message"]
        mock_exporter.Apply.assert_called_once()

    def test_export_pdf_no_work_part(self, mock_nx):
        handler = _get_handler("nx_export_drawing_pdf")

        NXSession._instance = MagicMock(spec=NXSession)
        NXSession._instance.is_connected = True
        NXSession._instance.require.return_value = mock_nx._mock_session
        NXSession._instance.require_work_part.side_effect = RuntimeError(
            "No work part is open."
        )

        result = run(handler(path=r"C:\output\drawing.pdf"))
        data = json.loads(result)

        assert data["status"] == "error"
