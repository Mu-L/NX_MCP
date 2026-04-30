# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

NX_MCP is an MCP (Model Context Protocol) server that lets AI agents control Siemens NX (UG) CAD software via the stdio transport. Targets NX 2300+ (2023+).

## Commands

```bash
pip install -e ".[dev]"   # install with dev deps
pytest tests/ -v           # run all tests (no NX installation needed, all mocked)
pytest tests/test_tools/test_modeling.py -v  # run a single test file
```

## Architecture

Data flow: `AI Agent <-> MCP (stdio) <-> Python Server <-> NX Open API <-> NX`

- **`server.py`** — Entry point. Creates MCP `Server("nx-mcp")`, auto-discovers tool modules via `pkgutil.iter_modules`, runs stdio transport.
- **`tools/registry.py`** — `@mcp_tool(name, description, params)` decorator + `ToolRegistry` class. All tools register here automatically on import.
- **`nx_session.py`** — `NXSession` singleton wrapping `NXOpen.Session.GetSession()`. Use `.require()` or `.require_work_part()`.
- **`response.py`** — `ToolResult.success(data, message)` and `ToolError(error_code, message, suggestion)` for all tool responses. `ToolResult.from_exception(exc)` converts exceptions to `ToolError`.
- **`tools/*.py`** — 8 modules, ~47 tools total. Each tool is an `async def` with `@mcp_tool`.
- **`utils/geometry.py`** — Helpers: `make_point3d`, `make_vector3d`, `resolve_object_by_name`.
- **`utils/selection.py`** — `create_collector_from_names` for building `ScCollector` from named objects.

## Adding a New Tool

1. Add an `async def nx_<name>(...)` in the appropriate `tools/*.py` module (or create a new one).
2. Decorate with `@mcp_tool("nx_<name>", "description", {"param": {"type": "str", "description": "...", "required": True}})`.
3. Use `NXSession.get_instance().require()` or `.require_work_part()` to get the NX session.
4. Return `ToolResult.success(...)` or `ToolError(...)`.
5. Add tests mirroring the existing pattern in `tests/test_tools/`.

New tool modules under `tools/` are auto-discovered — no registration step needed.

## Conventions

- **NXOpen imports are local** (inside each tool function), not at module level. This allows the package to import without NX installed.
- **All tool names** use the `nx_` prefix with snake_case.
- **Builder pattern** for NX API: create builder → configure → `Commit()` → `Destroy()`.
- **Parameter validation** uses lookup dicts (e.g., `_PLANE_NORMALS`, `_MATE_TYPES`). Invalid values return `ToolError` with `error_code="NX_INVALID_PARAMS"`.
- **Tests** use a consistent pattern: each file has `_make_mock_nxopen()` building a mock NXOpen tree, an `autouse` `_setup_nx` fixture patching `sys.modules`, and `@pytest.mark.asyncio` tests calling handlers via `ToolRegistry.get_handler()`. Each test file has a `TestToolRegistration` class verifying expected tools are registered.
- **Async tests** use `asyncio_mode = "auto"` (pytest-asyncio).
