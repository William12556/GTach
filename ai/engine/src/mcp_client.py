"""
MCP client manager — async.

Manages stdio connections to one or more MCP servers.
Provides tool catalogue in OpenAI format and async tool dispatch.

Note: connect() and close() must be awaited in the same task to ensure
proper AsyncExitStack teardown without anyio cancel-scope errors.
"""

import uuid
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Read-only tool name patterns — tools matching these are safe for reviewer use.
# All other tools (write/edit/delete/move) are excluded from the read-only subset.
# change-bdc6820f (audit-5bcd46ad L-09): read-only and write classification
# come from one source, scope.py, shared with the write-scope check.
from scope import is_readonly_tool


class MCPClient:
    """Manages connections to multiple MCP servers."""

    def __init__(self, servers: dict[str, dict], timeout_seconds: float = 120.0) -> None:
        """
        Args:
            servers: MCP server configurations keyed by server name.
            timeout_seconds: Read timeout of every session request
                (initialize, list_tools, call_tool); change-711a57d5 (M-06).
        """
        self._servers = servers
        self._timeout_seconds = timeout_seconds
        self._sessions: dict[str, ClientSession] = {}
        self._tools: dict[str, dict] = {}  # tool_name -> {server, description, input_schema}
        self._stack: AsyncExitStack = AsyncExitStack()

    async def connect(self) -> None:
        """
        Connect to all configured MCP servers and build tool catalogue.

        All stdio_client and ClientSession contexts are entered via the instance
        AsyncExitStack. Call close() in the same task to tear down cleanly.
        """
        for name, cfg in self._servers.items():
            params = StdioServerParameters(
                command=cfg["command"],
                args=cfg.get("args", []),
                env=cfg.get("env"),
            )
            try:
                # Enter stdio_client context via the stack
                read, write = await self._stack.enter_async_context(stdio_client(params))
                # Enter ClientSession context via the stack
                # change-711a57d5 (audit-caab2052 M-06): bound every session
                # request; a timeout surfaces through the except branches.
                session = await self._stack.enter_async_context(ClientSession(
                    read, write,
                    read_timeout_seconds=timedelta(seconds=self._timeout_seconds),
                ))
                await session.initialize()
                self._sessions[name] = session
                response = await session.list_tools()
                for tool in response.tools:
                    self._tools[tool.name] = {
                        "server": name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema or {},
                    }
                print(f"[engine] Connected: {name} ({len(response.tools)} tools)")
            except Exception as e:
                print(f"[engine] Warning: failed to connect to '{name}': {e}")

    def _is_readonly_tool(self, name: str) -> bool:
        """Return True for a read-only tool (scope.is_readonly_tool)."""
        return is_readonly_tool(name)

    def get_openai_tools(self, readonly: bool = False) -> list[dict]:
        """
        Return tool catalogue in OpenAI tools array format.

        Args:
            readonly: If True, return only read-only tools (read/list/grep/search).
                      If False, return all tools.
        """
        tools = []
        for name, meta in self._tools.items():
            if readonly and not self._is_readonly_tool(name):
                continue
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": meta["description"],
                    "parameters": meta["input_schema"],
                },
            })
        return tools

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
        """
        Close all server connections.

        Tears down all stdio_client and ClientSession contexts via the
        AsyncExitStack. Must be awaited in the same task as connect().
        An Exception raised during teardown (for example an ExceptionGroup
        from a server answering after a timeout) is printed as a warning and
        not raised; the sessions are cleared in every case. BaseException
        subclasses that are not Exception (asyncio.CancelledError,
        KeyboardInterrupt) still propagate (change-5e8aea4f, audit-711a57d5 F-02).
        """
        # change-5e8aea4f (audit-711a57d5 F-02): teardown never raises an Exception
        try:
            await self._stack.aclose()
        except Exception as e:
            print(f"[engine] Warning: error while closing MCP connections: {e}")
        finally:
            self._sessions.clear()
