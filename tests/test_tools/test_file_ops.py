"""Tests for file_ops tools."""

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
    import nx_mcp.tools.file_ops as _mod  # noqa: F401 – registers tools
    return ToolRegistry.get_handler(name)


def run(coro):
    """Run an async coroutine synchronously in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# nx_list_open_parts
# ---------------------------------------------------------------------------

class TestNxListOpenParts:
    """Tests for nx_list_open_parts tool."""

    def test_list_parts_returns_json(self, mock_nx):
        handler = _get_handler("nx_list_open_parts")

        # Set up NXSession singleton with the mock session
        mock_session = mock_nx._mock_session
        NXSession._instance = MagicMock(spec=NXSession)
        NXSession._instance.is_connected = True
        NXSession._instance.require.return_value = mock_session

        # Build a parts array
        mock_part1 = MagicMock()
        mock_part1.Name = "bracket"
        mock_part1.FullPath = r"C:\parts\bracket.prt"

        mock_part2 = MagicMock()
        mock_part2.Name = "shaft"
        mock_part2.FullPath = r"C:\parts\shaft.prt"

        mock_session.Parts.ToArray.return_value = [mock_part1, mock_part2]
        mock_session.Parts.Work = mock_part1

        result = run(handler())
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["count"] == 2
        assert data["data"]["parts"][0]["name"] == "bracket"
        assert data["data"]["parts"][0]["is_work"] is True
        assert data["data"]["parts"][1]["is_work"] is False

    def test_list_parts_empty(self, mock_nx):
        handler = _get_handler("nx_list_open_parts")

        mock_session = mock_nx._mock_session
        NXSession._instance = MagicMock(spec=NXSession)
        NXSession._instance.is_connected = True
        NXSession._instance.require.return_value = mock_session

        mock_session.Parts.ToArray.return_value = []
        mock_session.Parts.Work = None

        result = run(handler())
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["count"] == 0


# ---------------------------------------------------------------------------
# nx_save_part
# ---------------------------------------------------------------------------

class TestNxSavePart:
    """Tests for nx_save_part tool."""

    def test_save_part_success(self, mock_nx):
        handler = _get_handler("nx_save_part")

        mock_session = mock_nx._mock_session
        mock_work_part = mock_session.Parts.Work

        NXSession._instance = MagicMock(spec=NXSession)
        NXSession._instance.is_connected = True
        NXSession._instance.require.return_value = mock_session
        NXSession._instance.require_work_part.return_value = mock_work_part

        mock_work_part.Name = "test_part"
        mock_work_part.FullPath = r"C:\test\test_part.prt"

        result = run(handler())
        data = json.loads(result)

        assert data["status"] == "success"
        assert "test_part" in data["message"]
        assert data["data"]["name"] == "test_part"
        mock_work_part.Save.assert_called_once()

    def test_save_part_no_work_part(self, mock_nx):
        handler = _get_handler("nx_save_part")

        NXSession._instance = MagicMock(spec=NXSession)
        NXSession._instance.is_connected = True
        NXSession._instance.require.return_value = mock_nx._mock_session
        NXSession._instance.require_work_part.side_effect = RuntimeError(
            "No work part is open. Use nx_open_part or nx_create_part first."
        )

        result = run(handler())
        data = json.loads(result)

        assert data["status"] == "error"


# ---------------------------------------------------------------------------
# nx_export_step — invalid format
# ---------------------------------------------------------------------------

class TestNxExportStep:
    """Tests for nx_export_step tool."""

    def test_export_invalid_format(self, mock_nx):
        handler = _get_handler("nx_export_step")

        mock_session = mock_nx._mock_session
        NXSession._instance = MagicMock(spec=NXSession)
        NXSession._instance.is_connected = True
        NXSession._instance.require.return_value = mock_session
        NXSession._instance.require_work_part.return_value = mock_session.Parts.Work

        result = run(handler(path=r"C:\out\file.xyz", format="dxf"))
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_code"] == "NX_INVALID_PARAMS"
        assert "step" in data["suggestion"].lower() or "iges" in data["suggestion"].lower()

    def test_export_step_success(self, mock_nx):
        handler = _get_handler("nx_export_step")

        mock_session = mock_nx._mock_session
        mock_work_part = mock_session.Parts.Work

        NXSession._instance = MagicMock(spec=NXSession)
        NXSession._instance.is_connected = True
        NXSession._instance.require.return_value = mock_session
        NXSession._instance.require_work_part.return_value = mock_work_part

        # Mock DexManager
        mock_step_creator = MagicMock()
        mock_session.DexManager.CreateStepCreator.return_value = mock_step_creator

        result = run(handler(path=r"C:\out\bracket.stp", format="step"))
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["format"] == "step"
        mock_step_creator.Apply.assert_called_once()
