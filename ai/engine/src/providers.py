"""
Model providers for the engine (design-14e05e35 §4.0; change-53c6f252).

One interface, two implementations:

    OpenAICompatProvider  kinds 'omlx' and 'openai_compatible' (oMLX, Mistral API)
    AnthropicProvider     kind 'anthropic' (native Messages API)

The engine keeps its message history in the OpenAI chat format. Each provider
converts at its boundary and returns a normalised Completion, so the loop does
not branch on provider (NFR-03).

build_role_bindings() resolves the worker and reviewer roles from the
'roles:' and 'providers:' blocks of ai/config.yaml, or from the legacy
'omlx:' block when 'roles:' is absent (FR-04-08).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import secrets
import string
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

from parser import parse_tool_calls

log = logging.getLogger("engine")

KINDS = ("omlx", "openai_compatible", "anthropic")
ROLES = ("worker", "reviewer")
_ID_ALPHABET = string.ascii_letters + string.digits
_ID_LENGTH = 9  # FR-04-09: the format Mistral issues; a compatibility convention
_ANTHROPIC_DEFAULT_MAX_TOKENS = 8192

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_COHERE_THINK_RE = re.compile(r"<\|START_THINKING\|>.*?<\|END_THINKING\|>", re.DOTALL)


class ConfigError(Exception):
    """Invalid provider or role configuration. The message names the key or variable."""


class ProviderError(Exception):
    """A provider returned a response the engine cannot use."""


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class Completion:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"            # stop, tool_calls, length
    usage: dict | None = None
    reasoning_content: str | None = None   # read by orchestrator.extract_reasoning


def new_tool_call_id() -> str:
    """Return a tool call ID of 9 alphanumeric characters (FR-04-09)."""
    return "".join(secrets.choice(_ID_ALPHABET) for _ in range(_ID_LENGTH))


def _strip_reasoning_blocks(content: str) -> str:
    """Remove <think> and Cohere thinking blocks, as orchestrator.extract_reasoning does."""
    return _COHERE_THINK_RE.sub("", _THINK_RE.sub("", content)).strip()


def query_omlx_context_window(model_name: str, base_url: str) -> int | None:
    """
    Query the oMLX admin API for settings.max_context_window of one model.

    Builds the admin URL by stripping a trailing '/v1' from base_url and
    appending '/admin/api/models?model_id=<model_name>'. Never raises.
    """
    try:
        admin_root = base_url.rstrip("/")
        if admin_root.endswith("/v1"):
            admin_root = admin_root[:-3]
        url = f"{admin_root}/admin/api/models?model_id={urllib.parse.quote(model_name, safe='')}"
        log.debug("querying oMLX admin API: %s", url)
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for entry in data.get("models", []):
            if entry.get("id") == model_name:
                ctx = entry.get("settings", {}).get("max_context_window")
                return int(ctx) if ctx is not None else None
        log.debug("oMLX admin query: no matching model entry for '%s'", model_name)
        return None
    except Exception as exc:
        log.warning("oMLX admin query failed for '%s': %s", model_name, exc)
        return None


# ---------------------------------------------------------------------------
# OpenAI-compatible provider (oMLX, Mistral API)
# ---------------------------------------------------------------------------

class OpenAICompatProvider:
    """Provider for OpenAI-compatible chat completion endpoints."""

    def __init__(self, kind: str = "omlx", base_url: str = "", api_key: str = "",
                 client: Any = None):
        self.kind = kind
        self.base_url = base_url
        if client is None:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.client = client

    async def complete(self, model: str, messages: list[dict], tools: list[dict] | None,
                       max_tokens: int | None = None) -> Completion:
        kwargs: dict[str, Any] = {"model": model, "messages": messages,
                                  "tools": tools or None, "stream": False}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        response = await self.client.chat.completions.create(**kwargs)
        return self.normalise(response)

    @staticmethod
    def normalise(response: Any) -> Completion:
        """Convert a chat completion response into a Completion."""
        choices = getattr(response, "choices", None)
        if not choices:
            # backlog §3.0-5: raised inside the bounded retry instead of crashing run_phase
            raise ProviderError("completion response contains no choices")
        choice = choices[0]
        message = choice.message
        content = message.content or ""
        tool_calls: list[ToolCall] = []
        if getattr(message, "tool_calls", None):
            for tc in message.tool_calls:
                try:
                    arguments = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    arguments = {}
                tool_calls.append(ToolCall(id=tc.id or new_tool_call_id(),
                                           name=tc.function.name, arguments=arguments))
        else:
            # Mistral / Cohere plain-text tool calls, parsed outside reasoning blocks
            for tc in parse_tool_calls(_strip_reasoning_blocks(content)):
                tool_calls.append(ToolCall(id=new_tool_call_id(), name=tc["name"],
                                           arguments=tc.get("arguments") or {}))
        usage = getattr(response, "usage", None)
        usage_dict = None
        if usage is not None:
            usage_dict = {"input_tokens": getattr(usage, "prompt_tokens", None),
                          "output_tokens": getattr(usage, "completion_tokens", None)}
        finish = getattr(choice, "finish_reason", None) or ("tool_calls" if tool_calls else "stop")
        return Completion(text=content, tool_calls=tool_calls, finish_reason=finish,
                          usage=usage_dict,
                          reasoning_content=getattr(message, "reasoning_content", None))

    async def await_ready(self, model: str, timeout: float = 60.0, interval: float = 2.0,
                          echo: Callable[[str], None] = lambda s: None) -> None:
        """
        Poll the models endpoint until reachable.

        kind 'omlx': an unlisted model is accepted (oMLX loads on first request).
        kind 'openai_compatible': the model must be listed, else ProviderError.
        """
        deadline = time.monotonic() + timeout
        attempt = 0
        while True:
            attempt += 1
            try:
                models = await self.client.models.list()
                ids = [m.id for m in models.data]
            except Exception as e:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(
                        f"inference endpoint not reachable after {timeout}s: {e}") from e
                echo(f"waiting for endpoint (attempt {attempt}, {remaining:.0f}s remaining): {e}")
                await asyncio.sleep(interval)
                continue
            if model in ids:
                echo(f"model ready: {model}")
                return
            if self.kind == "omlx":
                echo(f"endpoint ready; '{model}' not listed — proceeding")
                return
            raise ProviderError(f"model '{model}' is not available at {self.base_url}")

    def live_context_window(self, model: str) -> int | None:
        """Tier 2 of context resolution: live query for kind 'omlx' only."""
        if self.kind == "omlx" and self.base_url:
            return query_omlx_context_window(model, self.base_url)
        return None


# ---------------------------------------------------------------------------
# Anthropic provider (native Messages API)
# ---------------------------------------------------------------------------

def to_anthropic_tools(tools: list[dict] | None, strict: bool) -> list[dict]:
    """Convert OpenAI tool definitions; cache_control on the last tool (FR-04-04)."""
    out = []
    for t in tools or []:
        fn = t.get("function", t)
        entry = {
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters") or {"type": "object", "properties": {}},
        }
        if strict:
            entry["strict"] = True
        out.append(entry)
    if out:
        out[-1]["cache_control"] = {"type": "ephemeral"}
    return out


def to_anthropic_messages(messages: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Convert OpenAI chat messages to (system_blocks, messages) for the Messages API.

    system messages become text blocks (cache_control on the last one);
    assistant tool_calls become tool_use blocks; tool messages become
    tool_result blocks in a user message; consecutive same-role messages merge.
    """
    system: list[dict] = []
    out: list[dict] = []

    def append(role: str, blocks: list[dict]) -> None:
        if out and out[-1]["role"] == role:
            out[-1]["content"].extend(blocks)
        else:
            out.append({"role": role, "content": list(blocks)})

    for m in messages:
        role = m.get("role")
        content = m.get("content") or ""
        if role == "system":
            if content:
                system.append({"type": "text", "text": content})
        elif role == "user":
            append("user", [{"type": "text", "text": content or "(empty)"}])
        elif role == "assistant":
            blocks: list[dict] = [{"type": "text", "text": content}] if content else []
            for tc in m.get("tool_calls") or []:
                fn = tc["function"]
                try:
                    arguments = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    arguments = {}
                blocks.append({"type": "tool_use", "id": tc["id"], "name": fn["name"],
                               "input": arguments})
            append("assistant", blocks or [{"type": "text", "text": "(no content)"}])
        elif role == "tool":
            append("user", [{"type": "tool_result", "tool_use_id": m["tool_call_id"],
                             "content": content or "(empty)"}])
    if system:
        system[-1]["cache_control"] = {"type": "ephemeral"}
    return system, out


_STOP_REASONS = {"end_turn": "stop", "stop_sequence": "stop", "tool_use": "tool_calls",
                 "max_tokens": "length"}


def from_anthropic_response(response: Any) -> Completion:
    """Convert a Messages API response into a Completion."""
    texts: list[str] = []
    thinking: list[str] = []
    tool_calls: list[ToolCall] = []
    for block in getattr(response, "content", None) or []:
        btype = getattr(block, "type", "")
        if btype == "text":
            texts.append(block.text)
        elif btype == "thinking":
            thinking.append(getattr(block, "thinking", "") or "")
        elif btype == "tool_use":
            tool_calls.append(ToolCall(id=block.id, name=block.name,
                                       arguments=dict(block.input or {})))
    usage = getattr(response, "usage", None)
    usage_dict = None
    if usage is not None:
        usage_dict = {"input_tokens": getattr(usage, "input_tokens", None),
                      "output_tokens": getattr(usage, "output_tokens", None)}
    stop = getattr(response, "stop_reason", None) or "end_turn"
    return Completion(text="\n".join(texts), tool_calls=tool_calls,
                      finish_reason=_STOP_REASONS.get(stop, stop), usage=usage_dict,
                      reasoning_content="\n".join(thinking) or None)


class AnthropicProvider:
    """Provider for the Anthropic Messages API."""

    kind = "anthropic"

    def __init__(self, api_key: str = "", max_tokens: int = _ANTHROPIC_DEFAULT_MAX_TOKENS,
                 strict_tools: bool = True, base_url: str | None = None, client: Any = None):
        """
        base_url: optional Anthropic-compatible endpoint other than the Anthropic
        API, for example a local oMLX server (change-43091424). Omitted, the SDK
        default (the Anthropic API) applies.
        """
        self.base_url = base_url or None
        if client is None:
            from anthropic import AsyncAnthropic  # optional dependency, needed only here
            kwargs: dict[str, Any] = {"api_key": api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            client = AsyncAnthropic(**kwargs)
        self.client = client
        self.max_tokens = max_tokens
        self.strict_tools = strict_tools

    async def complete(self, model: str, messages: list[dict], tools: list[dict] | None,
                       max_tokens: int | None = None) -> Completion:
        system, converted = to_anthropic_messages(messages)
        kwargs: dict[str, Any] = {"model": model, "messages": converted,
                                  "max_tokens": max_tokens or self.max_tokens}
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = to_anthropic_tools(tools, self.strict_tools)
        response = await self.client.messages.create(**kwargs)
        return from_anthropic_response(response)

    async def await_ready(self, model: str, timeout: float = 60.0, interval: float = 2.0,
                          echo: Callable[[str], None] = lambda s: None) -> None:
        """
        Anthropic API: the model must be retrievable from the Models API.
        Custom base_url (local server): the endpoint must answer the model list;
        an unlisted model is accepted, as for kind omlx.
        """
        deadline = time.monotonic() + timeout
        attempt = 0
        while True:
            attempt += 1
            if self.base_url:
                try:
                    page = await self.client.models.list()
                    ids = [getattr(m, "id", None) for m in getattr(page, "data", None) or []]
                except Exception as e:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError(f"endpoint {self.base_url} not reachable after {timeout}s: {e}") from e
                    echo(f"waiting for {self.base_url} (attempt {attempt}, {remaining:.0f}s remaining): {e}")
                    await asyncio.sleep(interval)
                    continue
                echo(f"model ready: {model}" if model in ids
                     else f"endpoint ready; '{model}' not listed — proceeding")
                return
            try:
                await self.client.models.retrieve(model)
                echo(f"model ready: {model}")
                return
            except Exception as e:
                if getattr(e, "status_code", None) == 404:
                    raise ProviderError(f"model '{model}' is not available on the Anthropic API") from e
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"Anthropic API not reachable after {timeout}s: {e}") from e
                echo(f"waiting for Anthropic API (attempt {attempt}, {remaining:.0f}s remaining): {e}")
                await asyncio.sleep(interval)

    def live_context_window(self, model: str) -> int | None:
        return None


# ---------------------------------------------------------------------------
# Role bindings
# ---------------------------------------------------------------------------

@dataclass
class Binding:
    role: str
    provider_name: str
    provider: Any
    model: str


_LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1", "[::1]")


def _is_local(base_url: str | None) -> bool:
    """True for an endpoint on this machine, where a literal key is no secret."""
    if not base_url:
        return False
    host = urllib.parse.urlparse(base_url).hostname or ""
    return host in _LOCAL_HOSTS


def _api_key(name: str, pcfg: dict, kind: str) -> str:
    env = pcfg.get("api_key_env")
    if env:
        value = os.environ.get(env)
        if not value:
            raise ConfigError(f"providers.{name}: environment variable {env} is not set")
        return value
    if "api_key" in pcfg:
        if kind != "omlx" and not _is_local(pcfg.get("base_url")):
            raise ConfigError(f"providers.{name}: api_key is accepted only for kind omlx or a "
                              f"local base_url; use api_key_env")
        return str(pcfg["api_key"])
    if kind == "omlx":
        return "local"
    raise ConfigError(f"providers.{name}: api_key_env is required for kind {kind}")


def make_provider(name: str, pcfg: dict) -> Any:
    """Build one provider from its configuration block."""
    if not isinstance(pcfg, dict):
        raise ConfigError(f"providers.{name}: must be a mapping")
    kind = pcfg.get("kind")
    if kind not in KINDS:
        raise ConfigError(f"providers.{name}.kind: '{kind}' is not one of {', '.join(KINDS)}")
    key = _api_key(name, pcfg, kind)
    if kind == "anthropic":
        return AnthropicProvider(api_key=key,
                                 max_tokens=int(pcfg.get("max_tokens") or _ANTHROPIC_DEFAULT_MAX_TOKENS),
                                 strict_tools=bool(pcfg.get("strict_tools", True)),
                                 base_url=pcfg.get("base_url"))
    base_url = pcfg.get("base_url")
    if not base_url:
        raise ConfigError(f"providers.{name}.base_url: required for kind {kind}")
    return OpenAICompatProvider(kind=kind, base_url=base_url, api_key=key)


def build_role_bindings(config: dict, args: Any = None,
                        factory: Callable[[str, dict], Any] = make_provider) -> dict[str, Binding]:
    """
    Resolve the worker and reviewer bindings.

    With 'roles:': each role names a provider in 'providers:' (or the legacy
    'omlx' block) and a model. CLI precedence: --worker-model / --reviewer-model,
    then --model, then the role's model.

    Without 'roles:' (legacy, FR-04-08): both roles use the 'omlx:' block;
    worker = --worker-model or omlx.worker_model or --model or omlx.default_model,
    reviewer likewise.
    """
    cli_model = getattr(args, "model", None)
    cli_role = {"worker": getattr(args, "worker_model", None),
                "reviewer": getattr(args, "reviewer_model", None)}
    providers_cfg = dict(config.get("providers") or {})
    omlx_cfg = config.get("omlx")
    if "omlx" not in providers_cfg and isinstance(omlx_cfg, dict):
        providers_cfg["omlx"] = {"kind": "omlx", "base_url": omlx_cfg.get("base_url"),
                                 "api_key": omlx_cfg.get("api_key", "local")}

    roles_cfg = config.get("roles")
    instances: dict[str, Any] = {}

    def provider_for(name: str) -> Any:
        if name not in providers_cfg:
            raise ConfigError(f"provider '{name}' is not defined under providers:")
        if name not in instances:
            instances[name] = factory(name, providers_cfg[name])
        return instances[name]

    bindings: dict[str, Binding] = {}
    if roles_cfg is None:
        if not isinstance(omlx_cfg, dict):
            raise ConfigError("configuration needs a roles: block or the legacy omlx: block")
        default = cli_model or omlx_cfg.get("default_model")
        for role in ROLES:
            model = cli_role[role] or omlx_cfg.get(f"{role}_model") or default
            if not model:
                raise ConfigError(f"omlx.default_model: required when roles: is absent")
            bindings[role] = Binding(role, "omlx", provider_for("omlx"), model)
        return bindings

    if not isinstance(roles_cfg, dict):
        raise ConfigError("roles: must be a mapping")
    for role in ROLES:
        rcfg = roles_cfg.get(role)
        if not isinstance(rcfg, dict) or not rcfg.get("provider"):
            raise ConfigError(f"roles.{role}.provider: required")
        model = cli_role[role] or cli_model or rcfg.get("model")
        if not model:
            raise ConfigError(f"roles.{role}.model: required")
        bindings[role] = Binding(role, rcfg["provider"], provider_for(rcfg["provider"]), model)
    return bindings


def as_provider(client_or_provider: Any) -> Any:
    """Wrap a raw OpenAI-style client so existing callers of run_phase keep working."""
    if client_or_provider is None or hasattr(client_or_provider, "complete"):
        return client_or_provider
    return OpenAICompatProvider(kind="omlx", client=client_or_provider)
