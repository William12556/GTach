"""
MCP client manager — async.

Manages stdio connections to one or more MCP servers.
Provides tool catalogue in OpenAI format and async tool dispatch.
"""

import uuid
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Manages connections to multiple MCP servers."""

    def __init__(self, servers: dict[str, dict]) -> None:
        self._servers = servers
        self._sessions: dict[str, ClientSession] = {}
        self._contexts: list = []
        self._tools: dict[str, dict] = {}  # tool_name -> {server, description, input_schema}

    async def connect(self) -> None:
        """Connect to all configured MCP servers and build tool catalogue."""
        for name, cfg in self._servers.items():
            params = StdioServerParameters(
                command=cfg["command"],
                args=cfg.get("args", []),
                env=cfg.get("env"),
            )
            try:
                ctx = stdio_client(params)
                read, write = await ctx.__aenter__()
                self._contexts.append(ctx)
                session = ClientSession(read, write)
                await session.__aenter__()
                await session.initialize()
                self._sessions[name] = session
                response = await session.list_tools()
                for tool in response.tools:
                    self._tools[tool.name] = {
                        "server": name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema or {},
                    }
                print(f"[ael] Connected: {name} ({len(response.tools)} tools)")
            except Exception as e:
                print(f"[ael] Warning: failed to connect to '{name}': {e}")

    def get_openai_tools(self) -> list[dict]:
        """Return tool catalogue in OpenAI tools array format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": meta["description"],
                    "parameters": meta["input_schema"],
                },
            }
            for name, meta in self._tools.items()
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Dispatch a tool call and return result as string."""
        if name not in self._tools:
            return f"Error: unknown tool '{name}'"
        server_name = self._tools[name]["server"]
        session = self._sessions.get(server_name)
        if not session:
            return f"Error: server '{server_name}' not connected"
        try:
            result = await session.call_tool(name, arguments)
            parts = []
            for content in result.content:
                if hasattr(content, "text"):
                    parts.append(content.text)
                else:
                    parts.append(str(content))
            return "\n".join(parts)
        except Exception as e:
            return f"Error calling '{name}': {e}"

    async def close(self) -> None:
        """Close all server connections."""
        for session in self._sessions.values():
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass
        for ctx in self._contexts:
            try:
                await ctx.__aexit__(None, None, None)
            except Exception:
                pass
