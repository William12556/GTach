"""
Record an operator approval (design-14e05e35 §8.2; change-ee5357ec).

Usage (from the project root):
    python ai/engine/src/approve.py <uuid> <stage>

Appends one entry to ai/approvals.yaml and commits that file alone. The
engine counts only committed approvals (design §8.3). This command is for the
operator; no engine or engine-mcp tool runs it.

The entry records the git blob hash of each evidence document of the stage
(change-82dbf16a, H-02). After a document is edited or added, run the command
again: the new entry replaces the old one.
"""

from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stages as ST  # noqa: E402
from manifest import ManifestError, load_manifest, locate_manifest  # noqa: E402

HEADER = ("# Operator approvals (design-14e05e35 §8.2). Written by ai/engine/src/approve.py.\n"
          "# Only committed entries count. Do not edit by hand.\n"
          "approvals:\n")


def approve(project_root: str, uuid: str, stage: str, manifest=None,
            now: datetime.datetime | None = None) -> tuple[int, str]:
    """Record and commit one approval. Returns (exit_code, message)."""
    if not ST.UUID_RE.match(uuid):
        return 1, f"'{uuid}' is not an 8-character hexadecimal UUID"
    try:
        manifest = manifest or load_manifest(locate_manifest())
    except ManifestError as e:
        return 1, f"manifest error: {e}"
    ids = [s.id for s in manifest.stages]
    if stage not in ids:
        return 1, f"unknown stage '{stage}'; stages: {', '.join(ids)}"
    if not manifest.stage(stage).approval:
        approvable = [s.id for s in manifest.stages if s.approval]
        return 1, f"stage '{stage}' takes no approval; stages that do: {', '.join(approvable)}"
    if not ST.is_git_repository(project_root):
        return 1, f"{project_root} is not a git repository; approvals must be committed"
    report = ST.scan(project_root, manifest)
    if uuid not in report.work_items:
        return 1, f"work item {uuid}: no documents found in {ST.WORKSPACE}/"
    item = report.work_items[uuid]
    st = manifest.stage(stage)
    blobs = ST.stage_blobs(project_root, item, stage) if st.evidence else {}
    if st.evidence and not blobs:
        return 1, f"work item {uuid}: no {stage} document to approve"
    committed = ST.committed_approvals(project_root)
    if (uuid, stage) in committed and not ST.approval_mismatch(project_root, item, st, committed):
        return 0, f"{uuid} {stage}: already approved"

    path = os.path.join(project_root, ST.APPROVALS_FILE)
    stamp = (now or datetime.datetime.now(datetime.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    blob_map = ", ".join(f'"{n}": "{h}"' for n, h in sorted(blobs.items()))
    entry = (f'  - {{ uuid: "{uuid}", stage: "{stage}", date: "{stamp}", '
             f'blobs: {{ {blob_map} }} }}\n')
    if os.path.exists(path):
        with open(path) as fh:
            current = fh.read()
        if "approvals:" not in current:
            return 1, f"{ST.APPROVALS_FILE} has no 'approvals:' key; fix it before approving"
        if current and not current.endswith("\n"):
            current += "\n"
        content = current + entry
    else:
        content = HEADER + entry
    with open(path, "w") as fh:
        fh.write(content)

    rel = ST.APPROVALS_FILE
    for cmd in (["git", "-C", project_root, "add", "--", rel],
                ["git", "-C", project_root, "commit", "-q", "-m", f"approve: {uuid} {stage}", "--", rel]):
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            return 1, f"git failed ({' '.join(cmd[3:5])}): {proc.stderr.strip() or proc.stdout.strip()}"
    item = ST.scan(project_root, manifest).work_items[uuid]
    status = (f"current stage: {item.current_stage}" if item.current_stage
              else "all stages complete")
    missing = "".join(f"\n  missing: {m}" for m in item.missing)
    return 0, f"approved and committed: {uuid} {stage}\n{uuid} ({item.path}): {status}{missing}"


def main() -> None:
    p = argparse.ArgumentParser(description="Record and commit an operator approval.")
    p.add_argument("uuid", help="work-item UUID (8 hex characters)")
    p.add_argument("stage", help="stage to approve, as named in the governance model manifest")
    args = p.parse_args()
    code, message = approve(os.getcwd(), args.uuid, args.stage)
    print(message, file=sys.stderr if code else sys.stdout)
    sys.exit(code)


if __name__ == "__main__":
    main()
