# NX MCP Server

MCP (Model Context Protocol) server for Siemens NX (UG). Enables AI agents to
programmatically control NX's GUI for CAD operations.

## Features

- **~47 MCP tools** covering core CAD operations
- File operations: create, open, save, close, export, import
- Sketching: lines, arcs, rectangles, constraints
- Modeling: extrude, revolve, sweep, blend, chamfer, hole, pattern, boolean
- Assembly: add components, mate, list, reposition
- Drawing: create sheets, add views, dimensions, export PDF
- Measurement: distance, angle, volume
- Utility: view control, undo, screenshot, journal recording

## Prerequisites

- Siemens NX 2300+ (2023+)
- Python 3.10+
- NX Open Python API (bundled with NX)

## Installation

```bash
pip install -e .
```

## Configuration

### Claude Code

Add to `.claude/settings.local.json`:

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

### Generic MCP Client

Start the server via stdio:

```bash
python -m nx_mcp.server
```

## Usage

1. Start Siemens NX
2. Ensure your MCP client has the server configured
3. Ask your AI agent to perform NX operations

Example prompts:
- "Create a new part called bracket.prt"
- "Draw a 50x30 rectangle on the XY plane and extrude it 20mm"
- "Add a 3mm fillet to all edges"
- "Export the current part as STEP"

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

Tests run with mocked NX Open — no NX installation required.

## Architecture

```
AI Agent <-> MCP Protocol (stdio) <-> MCP Server (Python) <-> NX Open API <-> NX Application
```

## Project Structure

```
src/nx_mcp/
  server.py          # MCP server entry point
  nx_session.py      # NX session wrapper
  response.py        # Response types
  tools/             # ~47 MCP tools
    file_ops.py      # File operations
    sketch.py        # Sketch tools
    modeling.py      # Modeling features
    feature_tree.py  # Feature queries
    assembly.py      # Assembly tools
    drawing.py       # Drawing tools
    measure.py       # Measurement tools
    utility.py       # View, undo, screenshot, journal
  journal/           # Journal subsystem
  utils/             # Utilities
```

## License

MIT
