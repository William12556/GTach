#!/usr/bin/env python3
"""
govwatch — read-only governance monitoring TUI for downstream projects.

Infers workflow phase, runs a two-tier compliance scan, lists open
documents by UUID, and emits an alert summary to the clipboard and to
dashboard-alerts.md each scan cycle.

Usage:
    python ai/src/govwatch.py [--project PATH] [--interval N]

Key bindings: C=copy alerts  R=refresh  Q=quit
Write target: <project>/dashboard-alerts.md (overwritten each scan)
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from rich.markup import escape
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Static

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
    """Resolved filesystem paths for a govwatch project."""

    root: Path
    """Absolute project root directory."""
    workspace: Path
    """workspace/ directory under root."""
    ael_state: Path
    """.ael/ralph/ state directory under root."""
    alerts_file: Path
    """dashboard-alerts.md in the project root (sole write target)."""


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

                # Required-field validation
                if cls == "change":
                    missing = [f for f in sorted(_REQUIRED_CHANGE) if _is_placeholder(info.get(f))]
                    record.missing_fields = missing
                    record.required_fields_present = len(missing) == 0
                elif cls == "issue":
                    missing = [f for f in sorted(_REQUIRED_ISSUE) if _is_placeholder(info.get(f))]
                    record.missing_fields = missing
                    record.required_fields_present = len(missing) == 0

        # Tactical brief detection for T04 (prompt)
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
            f"govwatch: workspace/ not found at {paths.workspace}\n"
            f"Is '{paths.root}' a project root? "
            f"(expected 'workspace/' subdirectory)",
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
            for doc in grp_docs:
                if doc.cls == "prompt" and "change" not in grp_cls:
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
                # Show path relative to workspace/ for clarity
                try:
                    idx = doc.path.index("workspace")
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

        # FR-02-07: context-budget.md absent while a prompt is open → WARNING
        open_prompts = [d for d in docs if d.cls == "prompt" and not d.is_master]
        if open_prompts and not snapshot.budget.present:
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
            if doc.cls == "prompt" and not doc.has_tactical_brief:
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

    dashboard-alerts.md is the sole write target (CON-07 / NFR-01).
    Each call to write() overwrites the file; no appending (FR-04-04).
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
        The caller should surface failures as in-TUI WARNINGs (design §10).
        """
        content = self.payload(snapshot)
        try:
            self.paths.alerts_file.write_text(content, encoding="utf-8")
            return None
        except Exception as exc:  # noqa: BLE001
            return f"dashboard-alerts.md write failed: {exc}"


# ---------------------------------------------------------------------------
# Panel renderers (Rich markup strings)
# ---------------------------------------------------------------------------


def _render_workflow_state(snapshot: Snapshot) -> str:
    """Build a Rich markup string for the Workflow State panel."""
    ael = snapshot.ael_state
    budget = snapshot.budget

    _phase_colours = {
        "Tactical execution": "green",
        "Awaiting prompt execution": "yellow",
        "Change cycle": "cyan",
        "Issue raised": "blue",
        "Test phase": "magenta",
        "Idle": "dim",
    }
    _ael_colours = {
        "running": "green",
        "ship": "bright_green",
        "blocked": "red",
        "idle": "dim",
    }
    _budget_colours = {
        "ok": "green",
        "warn": "yellow",
        "abort": "red",
        "unknown": "dim",
    }

    phase_col = _phase_colours.get(snapshot.phase, "white")
    ael_col = _ael_colours.get(ael.status, "white")
    bud_col = _budget_colours.get(budget.status, "white")

    lines: list[str] = [
        "[bold]Phase[/bold]",
        f"  [{phase_col}]{escape(snapshot.phase)}[/{phase_col}]",
        "",
        "[bold]AEL Status[/bold]",
        f"  [{ael_col}]{ael.status.upper()}[/{ael_col}]",
    ]
    if ael.iteration is not None:
        lines.append(f"  Iteration: {ael.iteration}")
    if ael.blocked_detail:
        preview = ael.blocked_detail[:100].replace("\n", " ")
        lines.append(f"  [red]Blocked:[/red] {escape(preview)}")

    lines += [
        "",
        "[bold]Budget[/bold]",
        f"  [{bud_col}]{budget.status.upper()}[/{bud_col}]",
    ]
    if budget.initial_pct is not None:
        lines.append(f"  Initial load: {budget.initial_pct:.1f}%")
    if not budget.present:
        lines.append("  [dim]context-budget.md not found[/dim]")

    return "\n".join(lines)


def _render_compliance_alerts(snapshot: Snapshot) -> str:
    """Build a Rich markup string for the Compliance Alerts panel."""
    violations = [a for a in snapshot.alerts if a.severity == "violation"]
    warnings = [a for a in snapshot.alerts if a.severity == "warning"]
    ts = snapshot.scan_time.strftime("%H:%M:%S")

    lines: list[str] = []

    if violations:
        lines.append(f"[bold red]VIOLATIONS ({len(violations)})[/bold red]")
        for a in violations:
            doc_str = f" [dim]({escape(a.document)})[/dim]" if a.document else ""
            lines.append(f"  [red]• [{a.code}] {escape(a.message)}{doc_str}[/red]")
    else:
        lines.append("[green]No violations[/green]")

    lines.append("")

    if warnings:
        lines.append(f"[bold yellow]WARNINGS ({len(warnings)})[/bold yellow]")
        for a in warnings:
            doc_str = f" [dim]({escape(a.document)})[/dim]" if a.document else ""
            lines.append(f"  [yellow]• [{a.code}] {escape(a.message)}{doc_str}[/yellow]")
    else:
        lines.append("[green]No warnings[/green]")

    lines.append("")
    lines.append(
        f"[dim]Last scan: {ts}  |  "
        f"V: {len(violations)}  W: {len(warnings)}[/dim]"
    )
    return "\n".join(lines)


def _render_document_registry(snapshot: Snapshot) -> str:
    """Build a Rich markup string for the Document Registry panel."""
    docs = [d for d in snapshot.documents if not d.is_master]

    if not docs:
        return "[dim]No open documents[/dim]"

    # Group by filename UUID
    by_uuid: dict[str, list[DocumentRecord]] = {}
    no_uuid_docs: list[DocumentRecord] = []
    for doc in docs:
        if doc.uuid:
            by_uuid.setdefault(doc.uuid, []).append(doc)
        else:
            no_uuid_docs.append(doc)

    lines: list[str] = []
    for uid in sorted(by_uuid):
        grp = sorted(by_uuid[uid], key=lambda d: d.cls)
        lines.append(f"[bold]{uid}[/bold]")
        for doc in grp:
            status_mark = "[green]✓[/green]" if doc.parse_ok else "[red]![/red]"
            lines.append(
                f"  {status_mark} [dim]{doc.cls}[/dim] "
                f"{escape(os.path.basename(doc.path))}"
            )
        lines.append("")

    if no_uuid_docs:
        lines.append("[dim]── No UUID ──[/dim]")
        for doc in no_uuid_docs:
            lines.append(f"  [dim]{escape(os.path.basename(doc.path))}[/dim]")
        lines.append("")

    # Open-issue to-do list
    open_issues = [d for d in docs if d.cls == "issue"]
    if open_issues:
        lines.append("[bold]Open Issues[/bold]")
        for doc in open_issues:
            lines.append(f"  • {escape(os.path.basename(doc.path))}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# GovwatchApp
# ---------------------------------------------------------------------------


class GovwatchApp(App):
    """Governance monitoring TUI (textual.App subclass).

    Hosts three panels (Workflow State, Compliance Alerts, Document Registry),
    a polling timer, and key bindings for C / R / Q.
    """

    CSS = """
    Screen {
        layout: vertical;
    }
    #panels {
        layout: horizontal;
        height: 1fr;
    }
    .panel {
        border: round $primary;
        width: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }
    #workflow-state {
        border: round $success;
        width: 30%;
    }
    #compliance-alerts {
        border: round $warning;
        width: 45%;
    }
    #document-registry {
        border: round $accent;
        width: 25%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_scan", "Refresh"),
        Binding("c", "copy_alerts", "Copy alerts"),
    ]

    TITLE = "govwatch"
    SUB_TITLE = "Governance Monitor"

    def __init__(self, paths: ProjectPaths, interval: int = DEFAULT_INTERVAL) -> None:
        """Initialise the application with project paths and poll interval."""
        super().__init__()
        self.paths = paths
        self.interval = interval
        self._scanner = Scanner(paths)
        self._writer = AlertWriter(paths)
        self._snapshot: Optional[Snapshot] = None

    def compose(self) -> ComposeResult:
        """Compose the three-panel layout."""
        yield Header()
        with Horizontal(id="panels"):
            yield Static("", id="workflow-state", classes="panel")
            yield Static("", id="compliance-alerts", classes="panel")
            yield Static("", id="document-registry", classes="panel")
        yield Footer()

    def on_mount(self) -> None:
        """Set panel border titles, run the first scan, and start the timer."""
        self.query_one("#workflow-state", Static).border_title = "Workflow State"
        self.query_one("#compliance-alerts", Static).border_title = "Compliance Alerts"
        self.query_one("#document-registry", Static).border_title = "Document Registry"
        self._do_scan()
        self.set_interval(self.interval, self._do_scan)

    # ------------------------------------------------------------------
    # Scan and render
    # ------------------------------------------------------------------

    def _do_scan(self) -> None:
        """Perform one full scan cycle and refresh all panels."""
        snapshot = self._scanner.scan()
        self._snapshot = snapshot

        write_err = self._writer.write(snapshot)
        if write_err:
            snapshot.alerts.append(Alert(
                severity="warning",
                code="WRITE-WARN",
                message=write_err,
            ))

        self._update_panels(snapshot)

    def _update_panels(self, snapshot: Snapshot) -> None:
        """Push Rich markup into each panel widget."""
        self.query_one("#workflow-state", Static).update(
            _render_workflow_state(snapshot)
        )
        self.query_one("#compliance-alerts", Static).update(
            _render_compliance_alerts(snapshot)
        )
        self.query_one("#document-registry", Static).update(
            _render_document_registry(snapshot)
        )
        v = sum(1 for a in snapshot.alerts if a.severity == "violation")
        w = sum(1 for a in snapshot.alerts if a.severity == "warning")
        self.sub_title = (
            f"{self.paths.root.name}  |  "
            f"Phase: {snapshot.phase}  |  "
            f"V: {v}  W: {w}"
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_refresh_scan(self) -> None:
        """Force an immediate scan cycle (R key)."""
        self._do_scan()

    def action_copy_alerts(self) -> None:
        """Copy the alert summary payload to the clipboard (C key).

        Tries pyperclip first; falls back to macOS pbcopy; notifies on failure.
        """
        if self._snapshot is None:
            return
        payload = self._writer.payload(self._snapshot)
        # macOS pbcopy — reliable inside a textual alternate-screen session
        import subprocess
        try:
            proc = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
            )
            proc.communicate(input=payload.encode("utf-8"))
            self.notify("Alert summary copied to clipboard.", title="Copied")
            return
        except Exception:  # noqa: BLE001
            pass
        self.notify(
            "Clipboard copy failed: pbcopy not available on this platform.",
            title="Copy error",
            severity="error",
        )

    def action_quit(self) -> None:
        """Quit the application (Q key)."""
        self.exit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI arguments, validate the project root, and launch GovwatchApp."""
    parser = argparse.ArgumentParser(
        prog="govwatch",
        description="Read-only governance monitoring TUI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Key bindings:\n"
            "  C  copy alert summary to clipboard\n"
            "  R  force immediate refresh\n"
            "  Q  quit\n\n"
            "Write target: <project>/dashboard-alerts.md (overwritten each scan)"
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
    paths = ProjectPaths(
        root=root,
        workspace=root / "workspace",
        ael_state=root / ".ael" / "ralph",
        alerts_file=root / "dashboard-alerts.md",
    )

    if not validate_project(paths):
        sys.exit(1)

    app = GovwatchApp(paths=paths, interval=args.interval)
    app.run()


if __name__ == "__main__":
    main()
