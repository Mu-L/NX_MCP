# NX to MCP Server — Design Specification

**Date**: 2026-04-17
**Status**: Draft
**Target**: Siemens NX 2300+ (2023+)

## Overview

A Python MCP (Model Context Protocol) server that runs inside Siemens NX's Python environment, exposing NX Open API operations as MCP tools. This allows AI agents (Claude Code, generic MCP clients) to programmatically control NX's GUI for CAD operations.

## Architecture

**Pattern**: In-process MCP server (Approach A)

```
AI Agent  <--MCP/stdio-->  MCP Server (runs inside NX Python)  <--NX Open API-->  NX Application (GUI)
```

- The MCP server runs as a long-lived Python process inside NX
- Uses stdio transport for MCP communication
- Direct access to NX session state — no IPC latency
- Real-time GUI manipulation

### Launch Configuration

```json
{
  "mcpServers": {
    "nx-mcp": {
      "command": "python",
      "args": ["-m", "nx_mcp.server"],
      "env": {
        "UGII_BASE_DIR": "C:\\Program Files\\Siemens\\NX2300"
      }
    }
  }
}
```

## Project Structure

```
NX_MCP/
├── src/
│   └── nx_mcp/
│       ├── __init__.py
│       ├── server.py              # MCP server entry point (stdio transport)
│       ├── nx_session.py          # NX session management & lifecycle
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── registry.py        # Tool registration decorator
│       │   ├── file_ops.py        # Open/Save/Import/Export parts
│       │   ├── sketch.py          # Sketch creation & constraints
│       │   ├── modeling.py        # Extrude, Revolve, Sweep, Blend, etc.
│       │   ├── assembly.py        # Assembly management
│       │   ├── drawing.py         # Drawing creation & annotation
│       │   ├── measure.py         # Measurements & queries
│       │   └── feature_tree.py    # Feature tree navigation & editing
│       ├── journal/
│       │   ├── __init__.py
│       │   ├── recorder.py        # Journal recording & replay
│       │   └── templates/         # Reusable journal script templates
│       └── utils/
│           ├── __init__.py
│           ├── geometry.py        # Geometry type helpers
│           └── selection.py       # Selection utilities
├── tests/
│   ├── test_tools/
│   └── conftest.py                # NX mock fixtures
├── examples/
│   ├── create_block.py
│   └── assembly_demo.py
├── pyproject.toml
└── README.md
```

### Key Design Patterns

- **Tool registry**: Each tool module registers tools via a `@tool` decorator. Server auto-discovers all registered tools.
- **NX session singleton**: One `NXSession` class wraps the NX Open `Session` object, providing centralized access to `Part`, `UFSession`, etc.
- **Journal subsystem**: Records operations to `.py` journal files for batch automation and auditing.
- **Mock-friendly**: Tests use mocks of NX Open types, runnable without NX installed.

## MCP Tool Catalog (~40 tools)

### File Operations (8 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `nx_open_part` | `path: str` | Part info |
| `nx_create_part` | `path: str, units: "mm"|"inch"` | Part info |
| `nx_save_part` | — | Success |
| `nx_save_as` | `path: str` | Success |
| `nx_close_part` | `save: bool` | Success |
| `nx_export_step` | `path: str, format: "step"|"iges"|"stl"|"parasolid"` | File path |
| `nx_import_geometry` | `path: str` | Imported body info |
| `nx_list_open_parts` | — | List of open parts |

### Sketch (6 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `nx_create_sketch` | `plane: str, name: str` | Sketch info |
| `nx_sketch_line` | `x1,y1, x2,y2` | Curve info |
| `nx_sketch_arc` | `cx,cy, r, start, end` | Curve info |
| `nx_sketch_rectangle` | `x1,y1, x2,y2` | Curves info |
| `nx_sketch_constraint` | `type, targets, value` | Constraint info |
| `nx_finish_sketch` | — | Feature info |

### Modeling — Features (11 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `nx_extrude` | `sketch, distance, direction, boolean` | Feature info |
| `nx_revolve` | `sketch, axis, angle` | Feature info |
| `nx_sweep` | `section, guide` | Feature info |
| `nx_blend` | `edges, radius` | Feature info |
| `nx_chamfer` | `edges, offset` | Feature info |
| `nx_hole` | `location, diameter, depth` | Feature info |
| `nx_pattern` | `features, type, count, spacing` | Feature info |
| `nx_boolean` | `type: "unite"|"subtract"|"intersect", targets` | Body info |
| `nx_delete_feature` | `name: str` | Success |
| `nx_edit_feature` | `name, params` | Feature info |
| `nx_mirror_body` | `body, plane` | Body info |

### Assembly (4 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `nx_add_component` | `part_path, name` | Component info |
| `nx_mate_component` | `component, type, references` | Constraint info |
| `nx_list_components` | — | Component list |
| `nx_reposition_component` | `component, transform` | Success |

### Drawing (5 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `nx_create_drawing` | `name, size, scale` | Drawing info |
| `nx_add_base_view` | `drawing, body, view: "front"|"top"|...` | View info |
| `nx_add_projection_view` | `base_view, direction` | View info |
| `nx_add_dimension` | `view, object1, object2` | Annotation info |
| `nx_export_drawing_pdf` | `path: str` | File path |

### Measurement & Query (6 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `nx_measure_distance` | `obj1, obj2` | Distance value |
| `nx_measure_angle` | `obj1, obj2` | Angle value |
| `nx_measure_volume` | `body` | Volume + mass |
| `nx_list_features` | `part` | Feature list |
| `nx_get_feature_info` | `name: str` | Feature details |
| `nx_get_bounding_box` | `body` | Box dimensions |

### Journal & Utility (7 tools)

| Tool | Parameters | Returns |
|------|-----------|---------|
| `nx_run_journal` | `path: str` | Execution result |
| `nx_record_start` | — | Success |
| `nx_record_stop` | `save_path: str` | File path |
| `nx_screenshot` | `path: str` | Image path |
| `nx_undo` | — | Success |
| `nx_fit_view` | — | Success |
| `nx_set_view` | `orientation: "front"|"top"|"iso"|...` | Success |

## Response Format

Every tool returns consistent JSON:

```json
{
  "status": "success",
  "data": { "feature_name": "EXTRUDE(1)", "type": "EXTRUDE" },
  "message": "Extrude created: EXTRUDE(1)"
}
```

```json
{
  "status": "error",
  "error_code": "NX_FEATURE_NOT_FOUND",
  "message": "Feature 'Boss' not found. Available: EXTRUDE(0), BLEND(1)",
  "suggestion": "Use nx_list_features to see all features"
}
```

## Error Handling

| Error Type | Handling |
|-----------|----------|
| NX API exception | Catch `NXException`, return structured error with code and message |
| Invalid parameters | Validate before calling NX, return clear validation error |
| NX not running | Detect at startup, return informative error on every call |
| Feature not found | Return "not found" with available alternatives |
| Operation failed | Return failure reason + suggested fix when possible |

## Startup Behavior

1. Attempt to connect to NX Open session (`NXOpen.Session.GetSession()`)
2. If NX is not running → server starts successfully but tools return errors until NX is launched
3. If NX is running → immediately ready
4. Server logs status to stderr (visible in MCP client logs)

## Technology Stack

- **Language**: Python 3.10+
- **MCP SDK**: `mcp` Python package (official MCP SDK)
- **NX API**: NX Open Python (`NXOpen`, `NXOpen.UF`)
- **Transport**: stdio (stdin/stdout)
- **Packaging**: `pyproject.toml` with `setuptools`
- **Testing**: `pytest` with NX Open mocks

## Dependencies

```
mcp>=1.0.0
pydantic>=2.0
```

NX Open dependencies are provided by the NX installation (not pip-installable).

## Scope Boundaries

**In scope (v1)**:
- Core CAD operations: file I/O, sketching, feature creation/editing, assembly, drawing, measurement
- Journal recording and replay
- Screenshot capture
- View manipulation

**Out of scope (v1)**:
- CAE/Simulation operations
- CAM/Manufacturing operations
- Sheet metal-specific features
- Routing/Piping
- Real-time collaborative editing
- Multi-user session management
