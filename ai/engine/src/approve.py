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
import locale
import os
import stat
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stages as ST  # noqa: E402
from manifest import ManifestError, load_manifest, locate_manifest  # noqa: E402

HEADER = ("# Operator approvals (design-14e05e35 §8.2). Written by ai/engine/src/approve.py.\n"
          "# Only committed entries count. Do not edit by hand.\n"
          "approvals:\n")


def _write_atomic(path: str, data: bytes) -> None:
    """
    change-d4f527e7 (audit-caab2052 L-10): write data to a temporary file
    beside the file and move it into place with os.replace, so a reader sees
    the previous content or the new content. A symlink at path is written
    through, as before. On any failure the temporary file is removed and the
    exception re-raised.
    """
    target = os.path.realpath(path)
    # change-f68d51c2 (audit-d4f527e7 F-01): the temporary file is created
    # exclusively with mkstemp, never at a predictable name; its mode is that
    # of an existing regular file at target, else 0o666 & ~umask.
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(target),
                                    prefix=f".{os.path.basename(target)}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        try:
            st = os.lstat(target)
        except OSError:
            st = None
        if st is not None and stat.S_ISREG(st.st_mode):
            mode = stat.S_IMODE(st.st_mode)
        else:
            umask = os.umask(0)
            os.umask(umask)
            mode = 0o666 & ~umask
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, target)
    except BaseException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


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
    # change-4b0a5592 (audit-caab2052 L-05): the file as it was before the
    # call, restored if git add or git commit fails.
    prior: bytes | None = None
    if os.path.exists(path):
        with open(path, "rb") as fh:
            prior = fh.read()
        with open(path) as fh:
            current = fh.read()
        if "approvals:" not in current:
            return 1, f"{ST.APPROVALS_FILE} has no 'approvals:' key; fix it before approving"
        if current and not current.endswith("\n"):
            current += "\n"
        content = current + entry
    else:
        content = HEADER + entry
    # Encoded as the text-mode read above decodes (the locale's encoding).
    _write_atomic(path, content.encode(locale.getpreferredencoding(False)))

    rel = ST.APPROVALS_FILE
    for cmd in (["git", "-C", project_root, "add", "--", rel],
                ["git", "-C", project_root, "commit", "-q", "-m", f"approve: {uuid} {stage}", "--", rel]):
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            # change-4b0a5592 (audit-caab2052 L-05): never an empty detail;
            # the file and its index entry are left as they were.
            detail = (proc.stderr.strip() or proc.stdout.strip()
                      or f"exit code {proc.returncode}")
            message = f"git failed ({' '.join(cmd[3:5])}): {detail}"
            # Write the prior bytes back, or remove the file the call created;
            # then reset its index entry to HEAD, or drop it when there is no HEAD.
            reasons: list[str] = []
            try:
                if prior is None:
                    if os.path.lexists(path):
                        os.remove(path)
                else:
                    _write_atomic(path, prior)
            except OSError as e:
                reasons.append(str(e))
            reset = subprocess.run(["git", "-C", project_root, "reset", "-q", "--", rel],
                                   capture_output=True, text=True)
            if reset.returncode != 0:  # no HEAD
                reset = subprocess.run(["git", "-C", project_root, "rm", "-q", "--cached",
                                        "--ignore-unmatch", "--", rel],
                                       capture_output=True, text=True)
                if reset.returncode != 0:
                    reasons.append(reset.stderr.strip() or reset.stdout.strip()
                                   or f"git rm exit code {reset.returncode}")
            if reasons:
                message += f"; {rel} could not be restored: {'; '.join(reasons)}"
            return 1, message
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
