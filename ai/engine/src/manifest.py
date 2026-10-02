"""
Governance model manifest loader (design-14e05e35 §5.0; change-e58fd295).

Each governance model ships ai/governance/<name>/manifest.yaml (D-04). One
model is installed per project (D-05). The engine locates the manifest next
to its own ai/engine/ folder, validates it, and reads run types, gates,
stages and paths from it. Every validation error names the file and field
and stops the engine before any model call (FR-01-05, NFR-04).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import yaml

OWNERS = ("planner", "loop", "human")
BUILT_IN_GATES = ("syntax", "reviewer")
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class ManifestError(Exception):
    """Missing or invalid manifest. The message names the file and field."""


@dataclass
class Stage:
    id: str
    owner: str
    gates: list[str] = field(default_factory=list)
    on_blocked: str | None = None
    approval: bool = False
    evidence: dict | None = None


@dataclass
class Manifest:
    path: str
    name: str
    version: str
    workspace_folders: list[str]
    writable_paths: list[str]
    run_types: dict[str, dict[str, str]]
    gates: dict[str, dict[str, Any]]
    stages: list[Stage]
    paths: dict[str, dict[str, Any]]

    @property
    def model_dir(self) -> str:
        return os.path.dirname(self.path)

    def stage(self, stage_id: str) -> Stage:
        return next(s for s in self.stages if s.id == stage_id)

    def loop_stage(self) -> Stage:
        """The first stage owned by the loop (FR-02-02)."""
        return next(s for s in self.stages if s.owner == "loop")

    def next_approval_stage(self, after: str) -> Stage | None:
        """The first stage after `after` that requires operator approval."""
        ids = [s.id for s in self.stages]
        for s in self.stages[ids.index(after) + 1:]:
            if s.approval:
                return s
        return None

    def recipe_paths(self, run_type: str) -> tuple[str, str]:
        """Resolve (worker, reviewer) recipe files for a run type."""
        if run_type not in self.run_types:
            raise ManifestError(f"{self.path}: run_types.{run_type}: not declared")
        rt = self.run_types[run_type]
        return (resolve_recipe(self.model_dir, rt["worker"]),
                resolve_recipe(self.model_dir, rt["reviewer"]))


def resolve_recipe(model_dir: str, rel: str) -> str:
    """A recipe path resolves against the model folder first, then ai/engine/recipes/."""
    for base in (model_dir, os.path.join(ENGINE_DIR, "recipes")):
        candidate = os.path.normpath(os.path.join(base, rel))
        if os.path.isfile(candidate):
            return candidate
    return ""


def locate_manifest(governance_dir: str | None = None) -> str:
    """Return the single ai/governance/<name>/manifest.yaml beside the engine."""
    root = governance_dir or os.path.normpath(os.path.join(ENGINE_DIR, "..", "governance"))
    found = []
    if os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            candidate = os.path.join(root, name, "manifest.yaml")
            if os.path.isfile(candidate):
                found.append(candidate)
    if not found:
        raise ManifestError(f"{root}: no governance model with a manifest.yaml")
    if len(found) > 1:
        raise ManifestError(f"{root}: more than one governance model installed "
                            f"({', '.join(os.path.basename(os.path.dirname(f)) for f in found)}); one is allowed")
    return found[0]


def _err(path: str, field_name: str, msg: str) -> ManifestError:
    return ManifestError(f"{path}: {field_name}: {msg}")


def _str_list(path: str, data: dict, key: str, required: bool) -> list[str]:
    value = data.get(key)
    if value is None:
        if required:
            raise _err(path, key, "required")
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise _err(path, key, "must be a list of non-empty strings")
    return list(value)


def load_manifest(path: str) -> Manifest:
    """Load and validate a manifest file."""
    try:
        with open(path) as fh:
            data = yaml.safe_load(fh)
    except OSError as e:
        raise ManifestError(f"{path}: cannot be read: {e}") from e
    except yaml.YAMLError as e:
        raise ManifestError(f"{path}: invalid YAML: {e}") from e
    if not isinstance(data, dict):
        raise ManifestError(f"{path}: must be a mapping")

    model = data.get("model")
    if not isinstance(model, dict) or not model.get("name") or model.get("version") in (None, ""):
        raise _err(path, "model", "name and version are required")

    folders = _str_list(path, data, "workspace_folders", required=True)
    for f in folders:
        if f.startswith("/") or ".." in f.split("/"):
            raise _err(path, "workspace_folders", f"'{f}' must be a relative path inside ai/workspace/")
    writable = _str_list(path, data, "writable_paths", required=False)
    for w in writable:  # change-82dbf16a (L-03)
        parts = [x for x in w.split("/") if x]
        if w.startswith("/") or ".." in parts or not parts or parts == ["."]:
            raise _err(path, "writable_paths", f"'{w}' must be a relative path below the project root")

    model_dir = os.path.dirname(path)
    run_types = data.get("run_types")
    if not isinstance(run_types, dict) or not run_types:
        raise _err(path, "run_types", "at least one run type is required")
    for rt_name, rt in run_types.items():
        if not isinstance(rt, dict):
            raise _err(path, f"run_types.{rt_name}", "must be a mapping with worker and reviewer")
        for role in ("worker", "reviewer"):
            rel = rt.get(role)
            if not isinstance(rel, str) or not rel:
                raise _err(path, f"run_types.{rt_name}.{role}", "required")
            if not resolve_recipe(model_dir, rel):
                raise _err(path, f"run_types.{rt_name}.{role}", f"recipe '{rel}' not found")

    gates = data.get("gates") or {}
    if not isinstance(gates, dict):
        raise _err(path, "gates", "must be a mapping")
    for g_name, g in gates.items():
        if g_name in BUILT_IN_GATES:
            raise _err(path, f"gates.{g_name}", "name is reserved for a built-in gate")
        if not isinstance(g, dict) or not isinstance(g.get("command"), str) or not g["command"].strip():
            raise _err(path, f"gates.{g_name}.command", "required")
        timeout = g.get("timeout_seconds", 300)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise _err(path, f"gates.{g_name}.timeout_seconds", "must be a positive number")

    raw_stages = data.get("stages")
    if not isinstance(raw_stages, list) or not raw_stages:
        raise _err(path, "stages", "at least one stage is required")
    stages: list[Stage] = []
    ids: list[str] = []
    for i, st in enumerate(raw_stages):
        where = f"stages[{i}]"
        if not isinstance(st, dict) or not isinstance(st.get("id"), str) or not st["id"]:
            raise _err(path, f"{where}.id", "required")
        if st["id"] in ids:
            raise _err(path, f"{where}.id", f"duplicate stage id '{st['id']}'")
        if st.get("owner") not in OWNERS:
            raise _err(path, f"{where}.owner", f"must be one of {', '.join(OWNERS)}")
        st_gates = st.get("gates") or []
        if not isinstance(st_gates, list):
            raise _err(path, f"{where}.gates", "must be a list")
        for g in st_gates:
            if g not in BUILT_IN_GATES and g not in gates:
                raise _err(path, f"{where}.gates", f"gate '{g}' is neither built in nor declared under gates")
        if st["owner"] == "loop" and "reviewer" not in st_gates:
            raise _err(path, f"{where}.gates", "a loop stage requires the reviewer gate")
        evidence = st.get("evidence")
        if evidence is not None:
            if not isinstance(evidence, dict) or not evidence.get("folder") or not evidence.get("prefix"):
                raise _err(path, f"{where}.evidence", "folder and prefix are required")
            if evidence["folder"] not in folders:
                raise _err(path, f"{where}.evidence.folder", f"'{evidence['folder']}' is not in workspace_folders")
            if "status_field" in evidence and not isinstance(evidence.get("complete_statuses"), list):
                raise _err(path, f"{where}.evidence.complete_statuses", "required with status_field")
        stages.append(Stage(id=st["id"], owner=st["owner"], gates=list(st_gates),
                            on_blocked=st.get("on_blocked"), approval=bool(st.get("approval", False)),
                            evidence=evidence))
        ids.append(st["id"])
    for i, st in enumerate(stages):
        if st.on_blocked is not None and st.on_blocked not in ids[:i]:
            raise _err(path, f"stages[{i}].on_blocked", f"'{st.on_blocked}' is not an earlier stage")
    if not any(s.owner == "loop" for s in stages):
        raise _err(path, "stages", "at least one stage owned by the loop is required")

    paths = data.get("paths") or {}
    if not isinstance(paths, dict):
        raise _err(path, "paths", "must be a mapping")
    for p_name, p in paths.items():
        where = f"paths.{p_name}"
        if not isinstance(p, dict) or not isinstance(p.get("stages"), list) or not p["stages"]:
            raise _err(path, f"{where}.stages", "required")
        unknown = [s for s in p["stages"] if s not in ids]
        if unknown:
            raise _err(path, f"{where}.stages", f"unknown stage(s): {', '.join(map(str, unknown))}")
        if [s for s in ids if s in p["stages"]] != p["stages"]:
            raise _err(path, f"{where}.stages", "must follow the stage order")
        if p.get("detect") not in p["stages"]:
            raise _err(path, f"{where}.detect", "must name a stage on the path")

    return Manifest(path=path, name=str(model["name"]), version=str(model["version"]),
                    workspace_folders=folders, writable_paths=writable, run_types=run_types,
                    gates=gates, stages=stages, paths=paths)
