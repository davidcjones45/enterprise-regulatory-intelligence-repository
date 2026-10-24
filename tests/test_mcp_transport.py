"""Real official-SDK integration tests. Required in CI through the dev extra."""
import asyncio
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp", reason="Install .[dev] or .[mcp] for real MCP transport tests")
from mcp import Client, StdioServerParameters

from erir.mcp_poc import TOOLS, create_server

ROOT = Path(__file__).resolve().parents[1]


async def exercise(client):
    listed = (await client.list_tools()).tools
    assert {tool.name for tool in listed} == set(TOOLS)
    for tool in listed:
        assert tool.annotations.read_only_hint is True
        assert tool.annotations.open_world_hint is False
        assert tool.output_schema is not None
    result = await client.call_tool("get_obligation_trace", {"record_id": "OBL-FTC-001"})
    assert result.is_error is False
    response = result.structured_content
    assert response["boundaries"]["write_capability"] is False
    assert len(response["records"]) == 5
    for name, record_id in (
        ("get_applicability_assessment", "APP-FTC-001"),
        ("get_control_evidence", "CTL-CLAIMS-001"),
        ("get_source_status", "SRC-FTC-2026-001"),
    ):
        other = await client.call_tool(name, {"record_id": record_id})
        assert other.is_error is False
        assert other.structured_content["records"] == response["records"]
    assert (await client.call_tool("approve_applicability", {"record_id": "APP-FTC-001"})).is_error
    assert (await client.call_tool("get_obligation_trace", {"record_id": "../../etc/passwd"})).is_error
    assert (await client.call_tool("get_obligation_trace", {"record_id": "OBL-MISSING"})).is_error
    assert (await client.call_tool("get_obligation_trace", {"record_id": 42})).is_error
    assert (await client.call_tool("get_obligation_trace", {})).is_error
    return response


def test_official_sdk_in_process():
    async def run():
        async with Client(create_server(ROOT)) as client:
            await exercise(client)
    asyncio.run(asyncio.wait_for(run(), timeout=30))


def test_official_sdk_stdio_subprocess():
    async def run():
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-B", "-m", "erir.mcp_poc", "--repo-root", str(ROOT)],
            env={"PYTHONPATH": str(ROOT / "src"), "PATH": os.environ.get("PATH", "")},
        )
        async with Client(parameters) as client:
            await exercise(client)
    asyncio.run(asyncio.wait_for(run(), timeout=30))
