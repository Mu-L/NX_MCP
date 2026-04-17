"""Utility & view tools — fit view, set orientation, undo, screenshot,
run journal, record start/stop."""

from __future__ import annotations

import os

from nx_mcp.nx_session import NXSession
from nx_mcp.response import ToolError, ToolResult
from nx_mcp.tools.registry import mcp_tool

# ---------------------------------------------------------------------------
# Orientation map for nx_set_view
# ---------------------------------------------------------------------------
_ORIENTATION_MAP: dict[str, str] = {
    "front": "kFront",
    "back": "kBack",
    "top": "kTop",
    "bottom": "kBottom",
    "left": "kLeft",
    "right": "kRight",
    "isometric": "kIsometric",
    "trimetric": "kTrimetric",
}


# ---------------------------------------------------------------------------
# 1. nx_fit_view
# ---------------------------------------------------------------------------
@mcp_tool(
    name="nx_fit_view",
    description="Fit all visible objects in the graphics viewport.",
    params={},
)
async def nx_fit_view() -> str:
    """Fit the view so that all objects are visible."""
    try:
        session = NXSession.get_instance().require()

        view = session.Parts.Display.ViewsOfWorkPart
        if view is not None:
            view.FitAll()
        else:
            # Fallback: use full-screen fit on the current display
            session.Views.FullScreen()

        return ToolResult.success(
            data={},
            message="View fitted — all objects visible.",
        ).to_text()

    except Exception as exc:
        return ToolResult.from_exception(exc).to_text()


# ---------------------------------------------------------------------------
# 2. nx_set_view
# ---------------------------------------------------------------------------
@mcp_tool(
    name="nx_set_view",
    description="Set the graphics view orientation (front, back, top, bottom, left, right, isometric, trimetric).",
    params={
        "orientation": {
            "type": "string",
            "description": "View orientation: front, back, top, bottom, left, right, isometric, or trimetric.",
            "required": True,
        },
    },
)
async def nx_set_view(orientation: str) -> str:
    """Set the view to a named orientation."""
    try:
        import NXOpen

        session = NXSession.get_instance().require()

        key = orientation.strip().lower()
        if key not in _ORIENTATION_MAP:
            valid = ", ".join(_ORIENTATION_MAP.keys())
            return ToolError(
                error_code="NX_INVALID_PARAMS",
                message=f"Invalid orientation '{orientation}'.",
                suggestion=f"Use one of: {valid}.",
            ).to_text()

        # Retrieve the current view and orient it
        view = session.Parts.Display.ViewsOfWorkPart
        if view is not None:
            nx_orient = getattr(
                NXOpen.View.ViewOrientation,
                _ORIENTATION_MAP[key],
            )
            view.Orient(nx_orient)

        return ToolResult.success(
            data={"orientation": key},
            message=f"View set to {key}.",
        ).to_text()

    except Exception as exc:
        return ToolResult.from_exception(exc).to_text()


# ---------------------------------------------------------------------------
# 3. nx_undo
# ---------------------------------------------------------------------------
@mcp_tool(
    name="nx_undo",
    description="Undo the last visible operation.",
    params={},
)
async def nx_undo() -> str:
    """Undo the last visible mark."""
    try:
        session = NXSession.get_instance().require()

        session.UndoLastNVisibleMarks(1)

        return ToolResult.success(
            data={},
            message="Undo successful.",
        ).to_text()

    except Exception as exc:
        return ToolResult.from_exception(exc).to_text()


# ---------------------------------------------------------------------------
# 4. nx_screenshot
# ---------------------------------------------------------------------------
@mcp_tool(
    name="nx_screenshot",
    description="Capture the current graphics viewport as a PNG image.",
    params={
        "path": {
            "type": "string",
            "description": "Full file path for the output PNG image.",
            "required": True,
        },
    },
)
async def nx_screenshot(path: str) -> str:
    """Export the viewport as a PNG screenshot."""
    try:
        import NXOpen

        session = NXSession.get_instance().require()

        imaging = NXOpen.Display.Imaging()
        # Grab the current display
        display_part = session.Parts.Display

        screenshot_builder = imaging.CreateImageExportBuilder()
        screenshot_builder.FileName = path
        screenshot_builder.FileFormat = NXOpen.Display.ImageExportBuilder.FileFormats.Png
        screenshot_builder.Apply()

        return ToolResult.success(
            data={"path": path},
            message=f"Screenshot saved to {path}.",
        ).to_text()

    except Exception as exc:
        return ToolResult.from_exception(exc).to_text()


# ---------------------------------------------------------------------------
# 5. nx_run_journal
# ---------------------------------------------------------------------------
@mcp_tool(
    name="nx_run_journal",
    description="Execute an NX journal (Python script) file.",
    params={
        "path": {
            "type": "string",
            "description": "Full file path to the journal script (.py).",
            "required": True,
        },
    },
)
async def nx_run_journal(path: str) -> str:
    """Run an NX journal file."""
    try:
        if not os.path.isfile(path):
            return ToolError(
                error_code="NX_NOT_FOUND",
                message=f"Journal file not found: {path}",
                suggestion="Provide a valid file path to an existing .py journal script.",
            ).to_text()

        session = NXSession.get_instance().require()

        session.ExecuteJournal(path)

        return ToolResult.success(
            data={"path": path},
            message=f"Journal executed: {path}",
        ).to_text()

    except Exception as exc:
        return ToolResult.from_exception(exc).to_text()


# ---------------------------------------------------------------------------
# 6. nx_record_start
# ---------------------------------------------------------------------------
@mcp_tool(
    name="nx_record_start",
    description="Start recording an NX journal.",
    params={},
)
async def nx_record_start() -> str:
    """Begin journal recording."""
    try:
        session = NXSession.get_instance().require()

        session.BeginJournalRecording()

        return ToolResult.success(
            data={},
            message="Journal recording started.",
        ).to_text()

    except Exception as exc:
        return ToolResult.from_exception(exc).to_text()


# ---------------------------------------------------------------------------
# 7. nx_record_stop
# ---------------------------------------------------------------------------
@mcp_tool(
    name="nx_record_stop",
    description="Stop recording an NX journal and optionally save it.",
    params={
        "save_path": {
            "type": "string",
            "description": "Optional file path to save the recorded journal.",
            "required": False,
        },
    },
)
async def nx_record_stop(save_path: str | None = None) -> str:
    """Stop journal recording."""
    try:
        session = NXSession.get_instance().require()

        session.EndJournalRecording()

        data: dict = {}
        if save_path:
            data["save_path"] = save_path

        return ToolResult.success(
            data=data,
            message="Journal recording stopped.",
        ).to_text()

    except Exception as exc:
        return ToolResult.from_exception(exc).to_text()
