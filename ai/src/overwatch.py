#!/usr/bin/env python3
"""
overwatch — read-only governance monitoring, rendered to a browser page.

Project Overwatch FR-01 (design-project-overwatch.md §7.1): the three
govwatch panels (Workflow State, Compliance Alerts, Document Registry)
ported from a Textual TUI to a single self-contained HTML file. The data
layer (Scanner, PhaseInference, ComplianceEngine, AlertWriter and their
supporting types) is carried over from ai/src/govwatch.py unmodified; only
the presentation layer is new.

Each scan cycle writes two files and reads everything else read-only:
    <project>/overwatch.html          rendered dashboard (overwritten)
    <project>/ai/dashboard-alerts.md  alert summary (overwritten)

Usage:
    python ai/src/overwatch.py [--project PATH] [--interval N]

The rendered page carries a <meta http-equiv="refresh"> tag matching the
scan interval, so an open browser tab re-reads the file as it is rewritten.
No server process, no socket, no port (design §3.1).
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import html
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_INTERVAL: int = 5
"""Default polling interval in seconds."""

CLASS_DIRS: dict[str, str] = {
    "issue": "issues",
    "change": "change",
    "prompt": "prompt",
    "test": "test",
    "result": "test/result",
    "audit": "audit",
    "trace": "trace",
    "requirements": "requirements",
    "design": "design",
}
"""Map from document class name to workspace subdirectory."""

_FILENAME_RE = re.compile(
    r"^(issue|change|prompt|test|result|audit|trace|requirements|design)"
    r"-([0-9a-f]{8})-(.+)\.md$"
)
_MASTER_RE = re.compile(
    r"^(issue|change|prompt|test|result|audit|trace|requirements|design)"
    r"-(.+)-master\.md$"
)
_HEX8_RE = re.compile(r"[0-9a-f]{8}")

_REQUIRED_CHANGE: frozenset[str] = frozenset(
    {"id", "title", "date", "status", "iteration", "coupled_docs"}
)
_REQUIRED_ISSUE: frozenset[str] = frozenset(
    {"id", "title", "date", "status", "severity", "type", "iteration"}
)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved filesystem paths for an overwatch project."""

    root: Path
    """Absolute project root directory."""
    workspace: Path
    """ai/workspace/ directory under root."""
    ael_state: Path
    """ai/state/ralph/ state directory under root."""
    alerts_file: Path
    """ai/dashboard-alerts.md (alert-summary write target)."""


@dataclass
class DocumentRecord:
    """Parsed snapshot of a single open governance document."""

    cls: str
    """Document class: issue, change, prompt, test, result, audit, trace,
    requirements, design, or 'unknown'."""
    uuid: Optional[str]
    """8-hex UUID from filename; None for master documents or malformed names."""
    name: str
    """Descriptive part of the filename (after UUID)."""
    path: str
    """Absolute filesystem path to the document."""
    iteration: Optional[int] = None
    """Iteration number parsed from the document body."""
    coupled_ref: Optional[str] = None
    """Raw coupled-document reference parsed from the body."""
    coupled_iteration: Optional[int] = None
    """Iteration number of the coupled document, parsed from the body."""
    is_master: bool = False
    """True if the document is a master (exempt from UUID and coupling checks)."""
    parse_ok: bool = True
    """False if the document body could not be fully parsed."""
    body_uuid: Optional[str] = None
    """Raw `id` value from the document's yaml block."""
    has_tactical_brief: bool = False
    """True if a yaml block contains a valid non-placeholder tactical_brief."""
    required_fields_present: bool = True
    """False if any required field is absent, empty, or a placeholder."""
    missing_fields: list[str] = field(default_factory=list)
    """Names of required fields that are absent or placeholder."""
    target_profile: Optional[str] = None
    """prompt_info.target_profile value (ael, claude_code, claude_omlx), or None if absent."""
    is_design_sourced: bool = False
    """True if prompt_info.source_ref matches the design-<uuid> pattern."""


@dataclass
class AelState:
    """AEL runtime state derived from .ael/ralph/ state files."""

    status: str = "idle"
    """idle | running | ship | blocked"""
    iteration: Optional[int] = None
    """Current iteration number from iteration.txt, if available."""
    blocked_detail: Optional[str] = None
    """Content of RALPH-BLOCKED.md when status is blocked."""
    task_ref: Optional[str] = None
    """Leading content of task.md (first non-empty line)."""


@dataclass
class BudgetState:
    """Context budget state derived from context-budget.md."""

    present: bool = False
    """True if context-budget.md was found."""
    status: str = "unknown"
    """ok | warn | abort | unknown"""
    initial_pct: Optional[float] = None
    """Initial context-load percentage parsed from the report."""


@dataclass
class Alert:
    """A single compliance or parse alert."""

    severity: str
    """violation | warning | ok"""
    code: str
    """Short alert code such as FR-02-01 or PARSE-WARN."""
    message: str
    """Human-readable description of the condition."""
    document: Optional[str] = None
    """Filename or UUID of the affected document, if applicable."""


@dataclass
class Snapshot:
    """Aggregate result of a single scan cycle. Replaced wholesale each cycle."""

    documents: list[DocumentRecord] = field(default_factory=list)
    """All open (non-closed) documents found during this scan."""
    ael_state: AelState = field(default_factory=AelState)
    """AEL runtime state at scan time."""
    budget: BudgetState = field(default_factory=BudgetState)
    """Context budget status at scan time."""
    phase: str = "Idle"
    """Inferred workflow phase (plain-language string)."""
    alerts: list[Alert] = field(default_factory=list)
    """Combined list of parse warnings and compliance alerts."""
    scan_time: datetime.datetime = field(default_factory=datetime.datetime.now)
    """Timestamp at which this scan was completed."""


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def parse_filename(name: str) -> tuple:
    """Parse a governance document filename into (cls, uuid, base_name, is_master).

    Returns:
        (cls, uuid, base_name, is_master) where:
        - Normal file:  (cls_str, 8hex_str, desc_str, False)
        - Master file:  (cls_str, None, desc_str, True)
        - Unrecognised: (None, None, name, False)
    """
    m = _FILENAME_RE.match(name)
    if m:
        return m.group(1), m.group(2), m.group(3), False
    m = _MASTER_RE.match(name)
    if m:
        return m.group(1), None, m.group(2), True
    return None, None, name, False


def _extract_yaml_blocks(text: str) -> list[dict]:
    """Extract and parse all fenced ```yaml blocks from document text.

    Silently discards blocks that fail yaml.safe_load. Returns only blocks
    that parse to a dict.
    """
    blocks: list[dict] = []
    for raw in re.findall(r"```yaml\s*\n(.*?)```", text, re.DOTALL):
        try:
            parsed = yaml.safe_load(raw)
            if isinstance(parsed, dict):
                blocks.append(parsed)
        except yaml.YAMLError:
            pass
    return blocks


def _find_block_with_key(blocks: list[dict], key: str) -> Optional[dict]:
    """Return the first block that contains *key* at root level, or None."""
    for block in blocks:
        if key in block:
            return block
    return None


def _is_placeholder(value: object) -> bool:
    """Return True if *value* counts as absent, empty, or a placeholder.

    A value is a placeholder when it is None, an empty string, or a string
    that begins with '#'.
    """
    if value is None:
        return True
    if isinstance(value, str) and (value == "" or value.startswith("#")):
        return True
    return False


def _extract_hex8(raw: Optional[str]) -> Optional[str]:
    """Extract the first 8-hex substring from *raw*, or return None."""
    if not raw:
        return None
    m = _HEX8_RE.search(raw)
    return m.group() if m else None


def parse_document(path: str) -> DocumentRecord:
    """Parse a governance document at *path* into a DocumentRecord.

    Extracts filename fields, then scans fenced yaml blocks for the
    document's info root key (change_info / issue_info / prompt_info).
    On any parse failure, sets parse_ok=False. Never raises.
    """
    fname = os.path.basename(path)
    cls, uuid_val, base_name, is_master = parse_filename(fname)
    record = DocumentRecord(
        cls=cls or "unknown",
        uuid=uuid_val,
        name=base_name,
        path=path,
        is_master=is_master,
        parse_ok=False,
    )

    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()

        blocks = _extract_yaml_blocks(text)

        _ROOT_KEY = {
            "change": "change_info",
            "issue": "issue_info",
            "prompt": "prompt_info",
        }
        root_key = _ROOT_KEY.get(cls or "")
        info_block = _find_block_with_key(blocks, root_key) if root_key else None

        if info_block and root_key:
            info = info_block.get(root_key)
            if isinstance(info, dict):
                # Body UUID (raw; may be "<class>-<uuid>" or bare "<uuid>")
                record.body_uuid = str(info.get("id") or "")

                # Iteration
                raw_iter = info.get("iteration")
                if raw_iter is not None:
                    try:
                        record.iteration = int(raw_iter)
                    except (ValueError, TypeError):
                        pass

                # Coupled reference
                cd = info.get("coupled_docs")
                if isinstance(cd, dict):
                    if cls == "change":
                        record.coupled_ref = cd.get("issue_ref") or cd.get("issue_uuid")
                        ci = cd.get("issue_iteration")
                    else:  # issue or prompt
                        record.coupled_ref = cd.get("change_ref") or cd.get("change_uuid")
                        ci = cd.get("change_iteration")
                    if ci is not None:
                        try:
                            record.coupled_iteration = int(ci)
                        except (ValueError, TypeError):
                            pass

                # Prompt profile and lineage (cls == "prompt" only)
                if cls == "prompt":
                    tp = info.get("target_profile")
                    if isinstance(tp, str) and tp and not tp.startswith("#"):
                        record.target_profile = tp
                    src_ref = info.get("source_ref")
                    if isinstance(src_ref, str) and src_ref.startswith("design-"):
                        record.is_design_sourced = True

                # Required-field validation
                if cls == "change":
                    missing = [f for f in sorted(_REQUIRED_CHANGE) if _is_placeholder(info.get(f))]
                    record.missing_fields = missing
                    record.required_fields_present = len(missing) == 0
                elif cls == "issue":
                    missing = [f for f in sorted(_REQUIRED_ISSUE) if _is_placeholder(info.get(f))]
                    record.missing_fields = missing
                    record.required_fields_present = len(missing) == 0

        # Tactical brief detection for T03 (prompt)
        if cls == "prompt":
            for block in blocks:
                brief = block.get("tactical_brief")
                if isinstance(brief, str) and brief and not brief.startswith("#"):
                    record.has_tactical_brief = True
                    break

        record.parse_ok = True

    except Exception:  # noqa: BLE001 — must not propagate (NFR-04)
        record.parse_ok = False

    return record


def validate_project(paths: ProjectPaths) -> bool:
    """Validate that *paths.root* is a plausible project root.

    Checks that workspace/ exists. Prints a diagnostic to stderr and returns
    False when validation fails; returns True otherwise (FR-05-04).
    """
    if not paths.workspace.is_dir():
        print(
            f"overwatch: ai/workspace/ not found at {paths.workspace}\n"
            f"Is '{paths.root}' a project root? "
            f"(expected 'ai/workspace/' subdirectory)",
            file=sys.stderr,
        )
        return False
    return True


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


class Scanner:
    """Produce a Snapshot from the project filesystem.

    All filesystem access is read-only. Per-document errors yield a WARNING
    alert and do not abort the scan (NFR-04).
    """

    def __init__(self, paths: ProjectPaths) -> None:
        """Initialise the Scanner with resolved project paths."""
        self.paths = paths

    def scan(self) -> Snapshot:
        """Walk the workspace, read AEL and budget state, return a Snapshot.

        The Snapshot is assembled, then PhaseInference and ComplianceEngine
        are applied before returning.
        """
        parse_alerts: list[Alert] = []
        documents: list[DocumentRecord] = []

        for cls, dirname in CLASS_DIRS.items():
            dirpath = self.paths.workspace / dirname
            if not dirpath.exists():
                continue
            for filepath in sorted(dirpath.rglob("*.md")):
                # Exclude closed/ subtrees and README files
                if "closed" in filepath.parts:
                    continue
                if filepath.name.upper() == "README.MD":
                    continue
                try:
                    doc = parse_document(str(filepath))
                    if not doc.parse_ok:
                        parse_alerts.append(Alert(
                            severity="warning",
                            code="PARSE-WARN",
                            message="Document could not be fully parsed",
                            document=filepath.name,
                        ))
                    documents.append(doc)
                except Exception as exc:  # noqa: BLE001
                    parse_alerts.append(Alert(
                        severity="warning",
                        code="PARSE-WARN",
                        message=f"Unhandled error reading document: {exc}",
                        document=filepath.name,
                    ))

        ael_state = self._read_ael_state()
        budget = self._read_budget()

        snapshot = Snapshot(
            documents=documents,
            ael_state=ael_state,
            budget=budget,
            scan_time=datetime.datetime.now(),
        )
        snapshot.phase = PhaseInference().infer(snapshot)
        compliance_alerts = ComplianceEngine().evaluate(snapshot)
        snapshot.alerts = parse_alerts + compliance_alerts
        return snapshot

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _read_ael_state(self) -> AelState:
        """Read .ael/ralph/ state files; return idle AelState when absent.

        Precedence: RALPH-BLOCKED.md → blocked; .ralph-complete → ship;
        task.md present → running; otherwise → idle (NFR-05).
        """
        state_dir = self.paths.ael_state
        if not state_dir.is_dir():
            return AelState(status="idle")

        def _read(name: str) -> Optional[str]:
            p = state_dir / name
            try:
                return p.read_text(encoding="utf-8", errors="replace").strip() if p.exists() else None
            except Exception:  # noqa: BLE001
                return None

        blocked_content = _read("RALPH-BLOCKED.md")
        complete_content = _read(".ralph-complete")
        task_content = _read("task.md")

        if blocked_content is not None:
            status = "blocked"
        elif complete_content is not None:
            status = "ship"
        elif task_content is not None:
            status = "running"
        else:
            status = "idle"

        iteration: Optional[int] = None
        iter_txt = _read("iteration.txt")
        if iter_txt:
            try:
                iteration = int(iter_txt)
            except ValueError:
                pass

        task_ref: Optional[str] = None
        if task_content:
            for line in task_content.splitlines():
                stripped = line.strip()
                if stripped:
                    task_ref = stripped[:160]
                    break

        return AelState(
            status=status,
            iteration=iteration,
            blocked_detail=blocked_content,
            task_ref=task_ref,
        )

    def _read_budget(self) -> BudgetState:
        """Derive BudgetState from context-budget.md in the AEL state dir.

        Parses initial-load %, warn %, and abort %; classifies accordingly.
        Absent file → unknown. File present but no initial-load → ok.
        """
        budget_file = self.paths.ael_state / "context-budget.md"
        if not budget_file.exists():
            return BudgetState(present=False, status="unknown")

        try:
            text = budget_file.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            return BudgetState(present=True, status="unknown")

        # Parse initial load percentage (dynamic report only)
        initial_pct: Optional[float] = None
        m = re.search(r"Estimated tokens at task start:.*?\((\d+(?:\.\d+)?)%", text)
        if m:
            try:
                initial_pct = float(m.group(1))
            except ValueError:
                pass

        if initial_pct is None:
            # Static budget report (no runtime data) — cannot classify
            return BudgetState(present=True, status="ok", initial_pct=None)

        warn_pct: Optional[float] = None
        m = re.search(r"Warn at:.*?\((\d+(?:\.\d+)?)%\)", text)
        if m:
            try:
                warn_pct = float(m.group(1))
            except ValueError:
                pass

        abort_pct: Optional[float] = None
        m = re.search(r"Abort at:.*?\((\d+(?:\.\d+)?)%\)", text)
        if m:
            try:
                abort_pct = float(m.group(1))
            except ValueError:
                pass

        if abort_pct is not None and initial_pct >= abort_pct:
            status = "abort"
        elif warn_pct is not None and initial_pct >= warn_pct:
            status = "warn"
        else:
            status = "ok"

        return BudgetState(present=True, status=status, initial_pct=initial_pct)


# ---------------------------------------------------------------------------
# PhaseInference
# ---------------------------------------------------------------------------


class PhaseInference:
    """Derive a single workflow phase from a Snapshot using design §6.0 precedence."""

    def infer(self, snapshot: Snapshot) -> str:
        """Return a plain-language phase string.

        Precedence (first match wins):
          1. AEL running                           → Tactical execution
          2. Open prompt + AEL idle/ship           → Awaiting prompt execution
          3. Open change + issue, no prompt        → Change cycle
          4. Open issue, no change                 → Issue raised
          5. Open test or result                   → Test phase
          6. No open documents                     → Idle
        """
        docs = snapshot.documents
        ael = snapshot.ael_state
        open_classes = {d.cls for d in docs if not d.is_master}

        if ael.status == "running":
            return "Tactical execution"
        if "prompt" in open_classes and ael.status in ("idle", "ship"):
            return "Awaiting prompt execution"
        if "change" in open_classes and "issue" in open_classes and "prompt" not in open_classes:
            return "Change cycle"
        if "issue" in open_classes and "change" not in open_classes:
            return "Issue raised"
        if "test" in open_classes or "result" in open_classes:
            return "Test phase"
        return "Idle"


# ---------------------------------------------------------------------------
# ComplianceEngine
# ---------------------------------------------------------------------------


class ComplianceEngine:
    """Run Tier 1 (filename/structure) and Tier 2 (content) compliance checks.

    Tier 1 runs unconditionally. Tier 2 runs only over documents with
    parse_ok=True. Each tier is independently guarded by a try/except so
    that a single-document error yields a WARNING rather than an exception.
    """

    def evaluate(self, snapshot: Snapshot) -> list[Alert]:
        """Return the combined list of Tier 1 and Tier 2 alerts."""
        alerts: list[Alert] = []
        try:
            alerts.extend(self._tier1(snapshot))
        except Exception as exc:  # noqa: BLE001
            alerts.append(Alert("warning", "CE-T1-ERR", f"Tier 1 check error: {exc}"))
        try:
            alerts.extend(self._tier2(snapshot))
        except Exception as exc:  # noqa: BLE001
            alerts.append(Alert("warning", "CE-T2-ERR", f"Tier 2 check error: {exc}"))
        return alerts

    # ------------------------------------------------------------------
    # Tier 1 — filename and structure
    # ------------------------------------------------------------------

    def _tier1(self, snapshot: Snapshot) -> list[Alert]:
        """Run all Tier 1 (FR-02-01 through FR-02-07) checks."""
        alerts: list[Alert] = []
        docs = snapshot.documents
        ael = snapshot.ael_state

        # Group open non-master documents by filename UUID
        uuid_groups: dict[str, list[DocumentRecord]] = {}
        for doc in docs:
            if doc.is_master:
                continue
            key = doc.uuid or f"__no_uuid__{doc.path}"
            uuid_groups.setdefault(key, []).append(doc)

        uuid_classes: dict[str, set[str]] = {
            uid: {d.cls for d in grp} for uid, grp in uuid_groups.items()
        }

        for uid, grp_docs in uuid_groups.items():
            grp_cls = uuid_classes[uid]

            # FR-02-01: change with no coupled issue sharing UUID → VIOLATION
            for doc in grp_docs:
                if doc.cls == "change" and "issue" not in grp_cls:
                    alerts.append(Alert(
                        severity="violation",
                        code="FR-02-01",
                        message="Change document has no coupled issue with matching UUID",
                        document=os.path.basename(doc.path),
                    ))

            # FR-02-02: issue with no coupled change sharing UUID → WARNING
            for doc in grp_docs:
                if doc.cls == "issue" and "change" not in grp_cls:
                    alerts.append(Alert(
                        severity="warning",
                        code="FR-02-02",
                        message="Issue document has no coupled change with matching UUID",
                        document=os.path.basename(doc.path),
                    ))

            # FR-02-03: prompt with no coupled change sharing UUID → VIOLATION
            # (skipped for design-sourced prompts — P04.1 exception, no change document exists)
            for doc in grp_docs:
                if doc.cls == "prompt" and "change" not in grp_cls and not doc.is_design_sourced:
                    alerts.append(Alert(
                        severity="violation",
                        code="FR-02-03",
                        message="Prompt document has no coupled change with matching UUID",
                        document=os.path.basename(doc.path),
                    ))

        # FR-02-04: filename not matching naming convention (masters exempt) → WARNING
        for doc in docs:
            if doc.is_master:
                continue
            if not _FILENAME_RE.match(os.path.basename(doc.path)):
                # Show path relative to ai/workspace/ for clarity
                try:
                    idx = doc.path.index("ai/workspace")
                    rel = doc.path[idx:]
                except ValueError:
                    rel = os.path.basename(doc.path)
                alerts.append(Alert(
                    severity="warning",
                    code="FR-02-04",
                    message="Filename does not match governance naming convention",
                    document=rel,
                ))

        # FR-02-05: open documents present while AEL signals SHIP → WARNING
        if ael.status == "ship":
            open_non_master = [d for d in docs if not d.is_master]
            if open_non_master:
                alerts.append(Alert(
                    severity="warning",
                    code="FR-02-05",
                    message=(
                        f"AEL reports SHIP but {len(open_non_master)} "
                        f"open document(s) remain"
                    ),
                    document=None,
                ))

        # FR-02-06: task.md content not matching any open prompt → WARNING
        if ael.task_ref:
            open_prompts = [d for d in docs if d.cls == "prompt" and not d.is_master]
            if open_prompts:
                matched = any(
                    (doc.uuid and doc.uuid in ael.task_ref)
                    or os.path.basename(doc.path) in ael.task_ref
                    for doc in open_prompts
                )
                if not matched:
                    alerts.append(Alert(
                        severity="warning",
                        code="FR-02-06",
                        message="AEL task.md does not reference any open prompt document",
                        document=None,
                    ))

        # FR-02-07: context-budget.md absent while an AEL-targeted prompt is open → WARNING
        # (only relevant when target_profile is ael, or absent — default assumes ael)
        open_ael_prompts = [
            d for d in docs
            if d.cls == "prompt" and not d.is_master and d.target_profile in (None, "ael")
        ]
        if open_ael_prompts and not snapshot.budget.present:
            alerts.append(Alert(
                severity="warning",
                code="FR-02-07",
                message="context-budget.md absent while prompt document is open",
                document=None,
            ))

        return alerts

    # ------------------------------------------------------------------
    # Tier 2 — document content
    # ------------------------------------------------------------------

    def _tier2(self, snapshot: Snapshot) -> list[Alert]:
        """Run all Tier 2 (FR-02-08 through FR-02-12) checks."""
        alerts: list[Alert] = []
        parsed_docs = [d for d in snapshot.documents if d.parse_ok and not d.is_master]

        # Build UUID-keyed iteration map for change/issue pairs
        uuid_iters: dict[str, dict[str, Optional[int]]] = {}
        for doc in parsed_docs:
            if doc.cls in ("change", "issue") and doc.uuid:
                uuid_iters.setdefault(doc.uuid, {})[doc.cls] = doc.iteration

        # FR-02-08: coupled change/issue iteration numbers differ → VIOLATION
        for uid, cls_iters in uuid_iters.items():
            change_iter = cls_iters.get("change")
            issue_iter = cls_iters.get("issue")
            if change_iter is not None and issue_iter is not None:
                if change_iter != issue_iter:
                    alerts.append(Alert(
                        severity="violation",
                        code="FR-02-08",
                        message=(
                            f"Change/issue iteration mismatch: "
                            f"change={change_iter} issue={issue_iter} (UUID {uid})"
                        ),
                        document=uid,
                    ))

        for doc in parsed_docs:
            # FR-02-09: body id UUID differs from filename UUID → VIOLATION
            if doc.uuid and doc.body_uuid:
                body_hex = _extract_hex8(doc.body_uuid)
                if body_hex and body_hex != doc.uuid:
                    alerts.append(Alert(
                        severity="violation",
                        code="FR-02-09",
                        message=(
                            f"Body 'id' UUID '{body_hex}' differs from "
                            f"filename UUID '{doc.uuid}'"
                        ),
                        document=os.path.basename(doc.path),
                    ))

            # FR-02-10: prompt missing valid tactical_brief → VIOLATION
            # (only when target_profile is ael, or absent — default assumes ael
            # for prompts predating the target_profile field, P13.2)
            if (
                doc.cls == "prompt"
                and not doc.has_tactical_brief
                and doc.target_profile in (None, "ael")
            ):
                alerts.append(Alert(
                    severity="violation",
                    code="FR-02-10",
                    message=(
                        "Prompt missing valid tactical_brief "
                        "(absent, empty, or placeholder)"
                    ),
                    document=os.path.basename(doc.path),
                ))

            # FR-02-11: issue missing required fields → WARNING
            if doc.cls == "issue" and not doc.required_fields_present:
                alerts.append(Alert(
                    severity="warning",
                    code="FR-02-11",
                    message=f"Issue missing required fields: {', '.join(doc.missing_fields)}",
                    document=os.path.basename(doc.path),
                ))

            # FR-02-12: change missing required fields → WARNING
            if doc.cls == "change" and not doc.required_fields_present:
                alerts.append(Alert(
                    severity="warning",
                    code="FR-02-12",
                    message=f"Change missing required fields: {', '.join(doc.missing_fields)}",
                    document=os.path.basename(doc.path),
                ))

        return alerts


# ---------------------------------------------------------------------------
# AlertWriter
# ---------------------------------------------------------------------------


class AlertWriter:
    """Render alert summaries and write to dashboard-alerts.md.

    dashboard-alerts.md is one of two permitted write targets (CON-07 /
    NFR-01, design §3.1 clarification). Each call to write() overwrites the
    file; no appending (FR-04-04).
    """

    def __init__(self, paths: ProjectPaths) -> None:
        """Initialise AlertWriter with resolved project paths."""
        self.paths = paths

    def payload(self, snapshot: Snapshot) -> str:
        """Build the plain-text alert summary payload (design §8.3/§8.4).

        The returned string is suitable for both dashboard-alerts.md and
        the clipboard.
        """
        project_name = self.paths.root.name
        ts = snapshot.scan_time.strftime("%Y-%m-%dT%H:%M:%S")
        ael = snapshot.ael_state
        budget = snapshot.budget

        ael_str = ael.status.upper()
        if ael.iteration is not None:
            ael_str += f" [iteration {ael.iteration}]"

        violations = [a for a in snapshot.alerts if a.severity == "violation"]
        warnings = [a for a in snapshot.alerts if a.severity == "warning"]

        lines: list[str] = [
            f"# govwatch alerts — {project_name}",
            "",
            f"Scan: {ts}",
            f"Phase: {snapshot.phase}",
            f"AEL: {ael_str}",
            f"Budget: {budget.status}",
            "",
            f"## Violations ({len(violations)})",
        ]
        if violations:
            for a in violations:
                doc_str = f" ({a.document})" if a.document else ""
                lines.append(f"- [{a.code}] {a.message}{doc_str}")
        else:
            lines.append("none")

        lines.append("")
        lines.append(f"## Warnings ({len(warnings)})")
        if warnings:
            for a in warnings:
                doc_str = f" ({a.document})" if a.document else ""
                lines.append(f"- [{a.code}] {a.message}{doc_str}")
        else:
            lines.append("none")

        return "\n".join(lines) + "\n"

    def write(self, snapshot: Snapshot) -> Optional[str]:
        """Overwrite dashboard-alerts.md with the current payload.

        Returns an error-message string on failure, None on success.
        """
        content = self.payload(snapshot)
        try:
            self.paths.alerts_file.write_text(content, encoding="utf-8")
            return None
        except Exception as exc:  # noqa: BLE001
            return f"dashboard-alerts.md write failed: {exc}"


# ---------------------------------------------------------------------------
# JSON serialisation helpers
# ---------------------------------------------------------------------------


def to_jsonable(value: Any) -> Any:
    """Convert *value* into a structure the stdlib json encoder accepts.

    Handles the types the Snapshot graph actually contains: dataclass
    instances, pathlib.Path (rendered as str), datetime (ISO 8601), and the
    usual containers. Anything else falls through to str() rather than
    raising, so a rendering pass can never fail on an unexpected type.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_jsonable(v) for v in value]
    return str(value)


# ---------------------------------------------------------------------------
# HtmlRenderer
# ---------------------------------------------------------------------------


class HtmlRenderer:
    """Render a Snapshot as a single self-contained HTML document.

    Replaces govwatch's Textual App (design §3.1, §5.0). The rendered page
    carries inlined CSS, the serialised Snapshot as embedded JSON, and a
    meta-refresh tag matching the scan interval. Severity colour-coding is
    server-rendered as CSS classes, not applied client-side.
    """

    OUTPUT_NAME: str = "overwatch.html"
    """Filename written to the project root each scan cycle."""

    _SEVERITY_CLASS: dict[str, str] = {
        "violation": "severity-violation",
        "warning": "severity-warning",
        "ok": "severity-ok",
    }
    """Alert severity → CSS class name."""

    _CSS: str = """
    :root { color-scheme: light dark; }
    body {
      margin: 0; padding: 1.5rem;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px; line-height: 1.5;
      background: #16181d; color: #e6e6e6;
    }
    h1 { font-size: 1.25rem; margin: 0 0 0.25rem 0; }
    h2 { font-size: 1rem; margin: 0 0 0.75rem 0; text-transform: uppercase;
         letter-spacing: 0.08em; color: #9aa4b2; }
    h3 { font-size: 0.9rem; margin: 1rem 0 0.35rem 0; color: #c8d0da; }
    .meta { color: #9aa4b2; margin-bottom: 1.25rem; font-size: 0.85rem; }
    .panels { display: flex; flex-wrap: wrap; gap: 1rem; align-items: flex-start; }
    .panel {
      flex: 1 1 20rem; min-width: 18rem;
      border: 1px solid #333a45; border-radius: 6px;
      padding: 1rem; background: #1c1f26;
    }
    .field { margin-bottom: 0.75rem; }
    .label { color: #9aa4b2; font-size: 0.8rem; text-transform: uppercase;
             letter-spacing: 0.06em; }
    .value { font-size: 1.05rem; font-weight: 600; }
    ul.alerts, ul.docs { list-style: none; margin: 0; padding: 0; }
    ul.alerts li, ul.docs li { margin-bottom: 0.4rem; }
    .code { font-family: ui-monospace, Menlo, monospace; font-size: 0.8rem;
            color: #9aa4b2; }
    .doc-ref { color: #8f98a5; font-size: 0.8rem; }
    .uuid-group { margin-bottom: 0.9rem; }
    .uuid { font-family: ui-monospace, Menlo, monospace; font-weight: 600; }
    .empty { color: #7d8794; font-style: italic; }
    .severity-violation { color: #ff6b6b; }
    .severity-warning  { color: #ffc857; }
    .severity-ok       { color: #5ed18a; }
    .status-blocked, .status-abort { color: #ff6b6b; }
    .status-running, .status-ok, .status-ship { color: #5ed18a; }
    .status-warn { color: #ffc857; }
    .status-idle, .status-unknown { color: #9aa4b2; }
    footer { margin-top: 1.5rem; color: #7d8794; font-size: 0.8rem; }
    """
    """Inlined stylesheet for the rendered page."""

    def __init__(self, paths: ProjectPaths, interval: int = DEFAULT_INTERVAL) -> None:
        """Initialise the renderer with project paths and the scan interval."""
        self.paths = paths
        self.interval = interval

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render(self, snapshot: Snapshot) -> str:
        """Return the complete HTML document for *snapshot* as a string.

        Args:
            snapshot: The current scan result.

        Returns:
            A full HTML document: inlined <style>, embedded snapshot JSON,
            meta-refresh tag, and the three FR-01 panel sections.
        """
        interval = self.interval
        project = html.escape(self.paths.root.name)
        ts = snapshot.scan_time.strftime("%Y-%m-%d %H:%M:%S")
        violations = sum(1 for a in snapshot.alerts if a.severity == "violation")
        warnings = sum(1 for a in snapshot.alerts if a.severity == "warning")

        return (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<meta http-equiv="refresh" content="{interval}">\n'
            f"<title>overwatch — {project}</title>\n"
            f"<style>{self._CSS}</style>\n"
            "</head>\n"
            "<body>\n"
            f"<h1>Project Overwatch — {project}</h1>\n"
            f'<p class="meta">Last scan {html.escape(ts)} &middot; '
            f"refresh {interval}s &middot; "
            f"V: {violations} &nbsp; W: {warnings}</p>\n"
            '<div class="panels">\n'
            f"{self._render_workflow_state(snapshot)}\n"
            f"{self._render_compliance_alerts(snapshot)}\n"
            f"{self._render_document_registry(snapshot)}\n"
            "</div>\n"
            "<footer>Read-only view. Regenerated each scan cycle; "
            "the browser reloads this file automatically.</footer>\n"
            f"{self._render_snapshot_json(snapshot)}\n"
            "<script>\n"
            "// Embedded snapshot is available for inspection and for the\n"
            "// client-side panels added in later phases.\n"
            'window.OVERWATCH = JSON.parse('
            'document.getElementById("snapshot").textContent);\n'
            "</script>\n"
            "</body>\n"
            "</html>\n"
        )

    def write(
        self,
        snapshot: Snapshot,
        project_root: Optional[Path] = None,
        interval: Optional[int] = None,
    ) -> None:
        """Render *snapshot* and overwrite overwatch.html at the project root.

        Write failures are reported to stderr and swallowed: a transient
        filesystem error must not end the scan loop (design §10.0). The next
        cycle retries.

        Args:
            snapshot: The current scan result.
            project_root: Output directory; defaults to the configured root.
            interval: Meta-refresh interval; defaults to the configured one.
        """
        root = project_root if project_root is not None else self.paths.root
        if interval is not None:
            self.interval = interval
        target = Path(root) / self.OUTPUT_NAME
        try:
            content = self.render(snapshot)
            target.write_text(content, encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 — must not end the loop
            print(f"overwatch: {self.OUTPUT_NAME} write failed ({target}): {exc}",
                  file=sys.stderr)

    # ------------------------------------------------------------------
    # Panel renderers
    # ------------------------------------------------------------------

    def _render_workflow_state(self, snapshot: Snapshot) -> str:
        """Return the Workflow State panel: phase, AEL status, budget."""
        ael = snapshot.ael_state
        budget = snapshot.budget

        parts: list[str] = [
            '<section class="panel" id="workflow-state">',
            "<h2>Workflow State</h2>",
            '<div class="field"><div class="label">Phase</div>'
            f'<div class="value">{html.escape(snapshot.phase)}</div></div>',
            '<div class="field"><div class="label">AEL Status</div>'
            f'<div class="value status-{html.escape(ael.status)}">'
            f"{html.escape(ael.status.upper())}</div>",
        ]
        if ael.iteration is not None:
            parts.append(f'<div class="doc-ref">Iteration {ael.iteration}</div>')
        if ael.blocked_detail:
            preview = ael.blocked_detail[:160].replace("\n", " ")
            parts.append(
                f'<div class="severity-violation">Blocked: {html.escape(preview)}</div>'
            )
        parts.append("</div>")

        parts.append(
            '<div class="field"><div class="label">Budget</div>'
            f'<div class="value status-{html.escape(budget.status)}">'
            f"{html.escape(budget.status.upper())}</div>"
        )
        if budget.initial_pct is not None:
            parts.append(f'<div class="doc-ref">Initial load {budget.initial_pct:.1f}%</div>')
        if not budget.present:
            parts.append('<div class="empty">context-budget.md not found</div>')
        parts.append("</div>")
        parts.append("</section>")
        return "\n".join(parts)

    def _render_compliance_alerts(self, snapshot: Snapshot) -> str:
        """Return the Compliance Alerts panel, grouped by severity."""
        parts: list[str] = [
            '<section class="panel" id="compliance-alerts">',
            "<h2>Compliance Alerts</h2>",
        ]

        for severity, heading in (("violation", "Violations"), ("warning", "Warnings")):
            group = [a for a in snapshot.alerts if a.severity == severity]
            css = self._SEVERITY_CLASS.get(severity, "severity-ok")
            parts.append(f'<h3 class="{css}">{heading} ({len(group)})</h3>')
            if not group:
                parts.append(
                    f'<p class="severity-ok">No {heading.lower()}</p>'
                )
                continue
            parts.append('<ul class="alerts">')
            for alert in group:
                doc = (
                    f' <span class="doc-ref">({html.escape(alert.document)})</span>'
                    if alert.document else ""
                )
                parts.append(
                    f'<li class="{css}"><span class="code">[{html.escape(alert.code)}]</span> '
                    f"{html.escape(alert.message)}{doc}</li>"
                )
            parts.append("</ul>")

        others = [a for a in snapshot.alerts if a.severity not in ("violation", "warning")]
        if others:
            parts.append('<h3 class="severity-ok">Other (%d)</h3>' % len(others))
            parts.append('<ul class="alerts">')
            for alert in others:
                css = self._SEVERITY_CLASS.get(alert.severity, "severity-ok")
                parts.append(
                    f'<li class="{css}"><span class="code">[{html.escape(alert.code)}]</span> '
                    f"{html.escape(alert.message)}</li>"
                )
            parts.append("</ul>")

        parts.append("</section>")
        return "\n".join(parts)

    def _render_document_registry(self, snapshot: Snapshot) -> str:
        """Return the Document Registry panel, grouped by document UUID."""
        docs = [d for d in snapshot.documents if not d.is_master]
        parts: list[str] = [
            '<section class="panel" id="document-registry">',
            "<h2>Document Registry</h2>",
        ]

        if not docs:
            parts.append('<p class="empty">No open documents</p>')
            parts.append("</section>")
            return "\n".join(parts)

        by_uuid: dict[str, list[DocumentRecord]] = {}
        no_uuid: list[DocumentRecord] = []
        for doc in docs:
            if doc.uuid:
                by_uuid.setdefault(doc.uuid, []).append(doc)
            else:
                no_uuid.append(doc)

        for uid in sorted(by_uuid):
            parts.append('<div class="uuid-group">')
            parts.append(f'<div class="uuid">{html.escape(uid)}</div>')
            parts.append('<ul class="docs">')
            for doc in sorted(by_uuid[uid], key=lambda d: d.cls):
                parts.append(self._render_document_row(doc))
            parts.append("</ul>")
            parts.append("</div>")

        if no_uuid:
            parts.append('<div class="uuid-group">')
            parts.append('<div class="uuid">No UUID</div>')
            parts.append('<ul class="docs">')
            for doc in no_uuid:
                parts.append(self._render_document_row(doc))
            parts.append("</ul>")
            parts.append("</div>")

        parts.append("</section>")
        return "\n".join(parts)

    def _render_document_row(self, doc: DocumentRecord) -> str:
        """Return one <li> for *doc*: class, filename, iteration, coupling."""
        css = "severity-ok" if doc.parse_ok else "severity-warning"
        mark = "&#10003;" if doc.parse_ok else "!"
        bits: list[str] = [html.escape(doc.cls)]
        if doc.iteration is not None:
            bits.append(f"iteration {doc.iteration}")
        bits.append("coupled" if doc.coupled_ref else "uncoupled")
        detail = " &middot; ".join(bits)
        return (
            f'<li><span class="{css}">{mark}</span> '
            f"{html.escape(os.path.basename(doc.path))}"
            f'<div class="doc-ref">{detail}</div></li>'
        )

    # ------------------------------------------------------------------
    # Embedded JSON
    # ------------------------------------------------------------------

    def _render_snapshot_json(self, snapshot: Snapshot) -> str:
        """Return the <script type="application/json" id="snapshot"> block.

        The payload is escaped so that no substring can terminate the
        enclosing <script> element prematurely.
        """
        payload = json.dumps(to_jsonable(snapshot), indent=2)
        payload = payload.replace("<", "\\u003c").replace(">", "\\u003e")
        return (
            '<script type="application/json" id="snapshot">\n'
            f"{payload}\n"
            "</script>"
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def resolve_paths(root: Path) -> ProjectPaths:
    """Build a ProjectPaths for *root* using govwatch's layout conventions."""
    return ProjectPaths(
        root=root,
        workspace=root / "ai" / "workspace",
        ael_state=root / "ai" / "state" / "ralph",
        alerts_file=root / "ai" / "dashboard-alerts.md",
    )


def scan_cycle(
    scanner: Scanner,
    writer: AlertWriter,
    renderer: HtmlRenderer,
) -> Snapshot:
    """Run one scan cycle: scan, write dashboard-alerts.md, write overwatch.html.

    A dashboard-alerts.md write failure is surfaced both as a WARNING alert
    on the rendered page and on stderr; neither write failure aborts the
    cycle (design §10.0).

    Returns:
        The Snapshot produced by this cycle.
    """
    snapshot = scanner.scan()

    write_err = writer.write(snapshot)
    if write_err:
        snapshot.alerts.append(Alert(
            severity="warning",
            code="WRITE-WARN",
            message=write_err,
        ))
        print(f"overwatch: {write_err}", file=sys.stderr)

    renderer.write(snapshot)
    return snapshot


def main() -> None:
    """Parse CLI arguments, validate the project root, and run the scan loop."""
    parser = argparse.ArgumentParser(
        prog="overwatch",
        description="Read-only governance monitoring, rendered to overwatch.html.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Write targets:\n"
            "  <project>/overwatch.html           rendered dashboard\n"
            "  <project>/ai/dashboard-alerts.md   alert summary\n\n"
            "Open overwatch.html once in a browser; it reloads itself on the\n"
            "scan interval. Press Ctrl-C to stop."
        ),
    )
    parser.add_argument(
        "--project",
        default=os.getcwd(),
        metavar="PATH",
        help="Project root directory (default: current working directory)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        metavar="N",
        help=f"Polling interval in seconds (default: {DEFAULT_INTERVAL})",
    )
    args = parser.parse_args()

    root = Path(args.project).resolve()
    paths = resolve_paths(root)

    if not validate_project(paths):
        sys.exit(1)

    interval = max(1, args.interval)
    scanner = Scanner(paths)
    writer = AlertWriter(paths)
    renderer = HtmlRenderer(paths, interval=interval)

    print(
        f"overwatch: monitoring {root} every {interval}s\n"
        f"overwatch: open {(root / HtmlRenderer.OUTPUT_NAME).as_uri()} in a "
        f"browser (Ctrl-C to stop)",
        file=sys.stderr,
    )

    try:
        while True:
            scan_cycle(scanner, writer, renderer)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\noverwatch: stopped", file=sys.stderr)


if __name__ == "__main__":
    main()
