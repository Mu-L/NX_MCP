"""MCP server entry point — stdio transport."""

from __future__ import annotations

import asyncio
import importlib
import json
import logging
import pkgutil
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from nx_mcp.response import ToolError
from nx_mcp.tools.registry import ToolRegistry

logger = logging.getLogger("nx_mcp")


def _discover_tools() -> None:
    """Auto-import all tool modules so @mcp_tool decorators fire."""
    import nx_mcp.tools as tools_pkg

    for _importer, modname, _ispkg in pkgutil.iter_modules(tools_pkg.__path__):
        if modname == "registry":
            continue
        full_name = f"{tools_pkg.__name__}.{modname}"
        try:
            importlib.import_module(full_name)
        except Exception as e:
            logger.error("Failed to import tool module %s: %s", full_name, e)


def create_server() -> Server:
    """Create and configure the MCP server."""
    _discover_tools()

    server = Server("nx-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        tools = []
        for t in ToolRegistry.list_tools():
            tools.append(
                Tool(
                    name=t["name"],
                    description=t["description"],
                    inputSchema=t["inputSchema"],
                )
            )
        return tools

    @server.call_tool()
    async def call_tool_handler(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        result = await call_tool(name, arguments)
        return result

    return server


async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Dispatch a tool call by name."""
    handler = ToolRegistry.get_handler(name)
    if handler is None:
        error = ToolError(
            error_code="NX_TOOL_NOT_FOUND",
            message=f"Unknown tool: {name}",
            suggestion=f"Available tools: {', '.join(ToolRegistry.get_tool_names())}",
        )
        return [TextContent(type="text", text=error.to_text())]

    try:
        result = await handler(**arguments)
        if isinstance(result, str):
            text = result
        elif isinstance(result, dict):
            text = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            text = str(result)
        return [TextContent(type="text", text=text)]
    except Exception as exc:
        error = ToolError(
            error_code="NX_EXECUTION_ERROR",
            message=str(exc),
            suggestion="Check that NX is running and the work part is open.",
        )
        return [TextContent(type="text", text=error.to_text())]


async def async_main() -> None:
    """Run the MCP server with stdio transport."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    server = create_server()
    logger.info("NX MCP Server starting (stdio transport)")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """Entry point for the nx-mcp console script."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
