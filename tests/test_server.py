"""Tests for MCP server entry point."""

import json

import pytest

# Import at module level to avoid PyO3 re-initialization errors when
# mock_nx patches sys.modules and triggers re-imports of mcp/rpds.
from nx_mcp.response import ToolResult
from nx_mcp.server import call_tool, create_server
from nx_mcp.tools.registry import ToolRegistry, mcp_tool


@pytest.mark.asyncio
async def test_server_lists_tools(mock_nx):
    server = create_server()
    assert server is not None
    assert server.name == "nx-mcp"


@pytest.mark.asyncio
async def test_call_tool_not_found(mock_nx):
    @mcp_tool(name="dummy_test", description="Dummy", params={})
    async def dummy():
        return {"ok": True}

    result = await call_tool("nonexistent_tool", {})
    parsed = json.loads(result[0].text)
    assert parsed["status"] == "error"


@pytest.mark.asyncio
async def test_call_tool_dispatches_correctly(mock_nx):
    @mcp_tool(
        name="echo_test",
        description="Echo input",
        params={"msg": {"type": "string", "description": "Message"}},
    )
    async def echo(msg: str) -> str:
        return ToolResult.success(data={"msg": msg}, message=f"Echo: {msg}").to_text()

    result = await call_tool("echo_test", {"msg": "hello"})
    text = result[0].text
    assert "hello" in text
