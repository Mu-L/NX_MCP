"""Tests for utility & view tools."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from nx_mcp.nx_session import NXSession
from nx_mcp.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_handler(name: str):
    """Import the module (triggering registration) and return the handler."""
    import nx_mcp.tools.utility as _mod  # noqa: F401 – registers tools
    return ToolRegistry.get_handler(name)


def run(coro):
    """Run an async coroutine synchronously in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


def _setup_session(mock_nx):
    """Set up NXSession singleton with mock and return the mock session."""
    mock_session = mock_nx._mock_session
    NXSession._instance = MagicMock(spec=NXSession)
    NXSession._instance.is_connected = True
    NXSession._instance.require.return_value = mock_session
    return mock_session


# ---------------------------------------------------------------------------
# nx_fit_view
# ---------------------------------------------------------------------------

class TestNxFitView:
    """Tests for nx_fit_view tool."""

    def test_fit_view_success(self, mock_nx):
        handler = _get_handler("nx_fit_view")
        mock_session = _setup_session(mock_nx)

        # Set up view mock
        mock_views = MagicMock()
        mock_session.Parts.Display.ViewsOfWorkPart = mock_views

        result = run(handler())
        data = json.loads(result)

        assert data["status"] == "success"
        assert "fitted" in data["message"].lower()

    def test_fit_view_no_session(self, mock_nx):
        handler = _get_handler("nx_fit_view")

        NXSession._instance = MagicMock(spec=NXSession)
        NXSession._instance.is_connected = True
        NXSession._instance.require.side_effect = RuntimeError("NX is not connected.")

        result = run(handler())
        data = json.loads(result)

        assert data["status"] == "error"


# ---------------------------------------------------------------------------
# nx_set_view
# ---------------------------------------------------------------------------

class TestNxSetView:
    """Tests for nx_set_view tool."""

    def test_set_view_valid_orientation(self, mock_nx):
        handler = _get_handler("nx_set_view")
        mock_session = _setup_session(mock_nx)

        mock_views = MagicMock()
        mock_session.Parts.Display.ViewsOfWorkPart = mock_views

        result = run(handler(orientation="front"))
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["orientation"] == "front"

    def test_set_view_invalid_orientation(self, mock_nx):
        handler = _get_handler("nx_set_view")
        _setup_session(mock_nx)

        result = run(handler(orientation="diagonal"))
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_code"] == "NX_INVALID_PARAMS"
        # Check that the suggestion lists valid orientations
        assert "front" in data["suggestion"] or "isometric" in data["suggestion"]

    def test_set_view_all_orientations(self, mock_nx):
        """Verify all 8 valid orientations are accepted."""
        handler = _get_handler("nx_set_view")
        valid = ["front", "back", "top", "bottom", "left", "right", "isometric", "trimetric"]

        for orient in valid:
            _setup_session(mock_nx)
            result = run(handler(orientation=orient))
            data = json.loads(result)
            assert data["status"] == "success", f"Expected success for '{orient}'"
            assert data["data"]["orientation"] == orient


# ---------------------------------------------------------------------------
# nx_undo
# ---------------------------------------------------------------------------

class TestNxUndo:
    """Tests for nx_undo tool."""

    def test_undo_success(self, mock_nx):
        handler = _get_handler("nx_undo")
        mock_session = _setup_session(mock_nx)

        result = run(handler())
        data = json.loads(result)

        assert data["status"] == "success"
        assert "undo" in data["message"].lower()
        mock_session.UndoLastNVisibleMarks.assert_called_once_with(1)

    def test_undo_no_session(self, mock_nx):
        handler = _get_handler("nx_undo")

        NXSession._instance = MagicMock(spec=NXSession)
        NXSession._instance.is_connected = True
        NXSession._instance.require.side_effect = RuntimeError("NX is not connected.")

        result = run(handler())
        data = json.loads(result)

        assert data["status"] == "error"


# ---------------------------------------------------------------------------
# nx_screenshot
# ---------------------------------------------------------------------------

class TestNxScreenshot:
    """Tests for nx_screenshot tool."""

    def test_screenshot_success(self, mock_nx):
        handler = _get_handler("nx_screenshot")
        mock_session = _setup_session(mock_nx)

        # NXOpen.Display.Imaging() returns an imaging object
        mock_imaging_instance = MagicMock()
        mock_builder = MagicMock()
        mock_imaging_instance.CreateImageExportBuilder.return_value = mock_builder
        mock_nx.Display.Imaging.return_value = mock_imaging_instance

        # FileFormats.Png mock
        mock_nx.Display.ImageExportBuilder = MagicMock()
        mock_nx.Display.ImageExportBuilder.FileFormats = MagicMock()
        mock_nx.Display.ImageExportBuilder.FileFormats.Png = MagicMock()

        result = run(handler(path=r"C:\tmp\shot.png"))
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["path"] == r"C:\tmp\shot.png"
        mock_builder.Apply.assert_called_once()


# ---------------------------------------------------------------------------
# nx_run_journal
# ---------------------------------------------------------------------------

class TestNxRunJournal:
    """Tests for nx_run_journal tool."""

    def test_run_journal_file_not_found(self, mock_nx):
        handler = _get_handler("nx_run_journal")
        _setup_session(mock_nx)

        result = run(handler(path=r"C:\nonexistent\script.py"))
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_code"] == "NX_NOT_FOUND"

    def test_run_journal_success(self, mock_nx):
        handler = _get_handler("nx_run_journal")
        mock_session = _setup_session(mock_nx)

        # Create a temporary file to simulate an existing journal
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            tmp.write(b"# test journal")
            tmp_path = tmp.name

        try:
            result = run(handler(path=tmp_path))
            data = json.loads(result)

            assert data["status"] == "success"
            assert data["data"]["path"] == tmp_path
            mock_session.ExecuteJournal.assert_called_once_with(tmp_path)
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# nx_record_start
# ---------------------------------------------------------------------------

class TestNxRecordStart:
    """Tests for nx_record_start tool."""

    def test_record_start_success(self, mock_nx):
        handler = _get_handler("nx_record_start")
        mock_session = _setup_session(mock_nx)

        result = run(handler())
        data = json.loads(result)

        assert data["status"] == "success"
        assert "started" in data["message"].lower()
        mock_session.BeginJournalRecording.assert_called_once()


# ---------------------------------------------------------------------------
# nx_record_stop
# ---------------------------------------------------------------------------

class TestNxRecordStop:
    """Tests for nx_record_stop tool."""

    def test_record_stop_without_save_path(self, mock_nx):
        handler = _get_handler("nx_record_stop")
        mock_session = _setup_session(mock_nx)

        result = run(handler())
        data = json.loads(result)

        assert data["status"] == "success"
        assert "stopped" in data["message"].lower()
        assert "save_path" not in data.get("data", {})
        mock_session.EndJournalRecording.assert_called_once()

    def test_record_stop_with_save_path(self, mock_nx):
        handler = _get_handler("nx_record_stop")
        mock_session = _setup_session(mock_nx)

        result = run(handler(save_path=r"C:\journals\recording.py"))
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["save_path"] == r"C:\journals\recording.py"
        mock_session.EndJournalRecording.assert_called_once()
