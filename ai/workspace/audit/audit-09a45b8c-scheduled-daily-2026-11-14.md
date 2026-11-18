Created: 2026 November 14
# GTach Scheduled Daily Audit — 2026-11-14 (audit-09a45b8c)

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Method](<#2.0 method>)
[3.0 Activity Summary](<#3.0 activity summary>)
[4.0 Finding F1 — build.sh rejects pre-release versions](<#4.0 finding f1 — build.sh rejects pre-release versions>)
[5.0 Observations](<#5.0 observations>)
[6.0 Changes Reviewed Without Finding](<#6.0 changes reviewed without finding>)
[7.0 Recommendations](<#7.0 recommendations>)
[Version History](<#version history>)

---

## 1.0 Purpose

This audit reviews commits on the default branch (`main`) of William12556/GTach whose commit date falls between 2026-11-13 02:05 UTC and 2026-11-14 02:05 UTC (the 24 hours before the run at 2026-11-14 03:05 Europe/Berlin).

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Method

- The GitHub MCP route was used: `list_commits`, `get_commit`, `list_tags`, `get_file_contents`, `list_issues` and `list_pull_requests`.
- `get_commit` returned file lists and statistics but no patch text. All patches were therefore read with the local git fallback (`git_show`), for commits `904bf8f`, `97aef4d`, `cfbf605`, `b2077e6`, `55bdbd1`, `3b7b552` and `26f7ea6`. Files reviewed this way: `pyproject.toml`, `src/gtach/utils/updater.py`, `tests/test_update_version_ordering.py`, `src/gtach/comm/obd.py`, `tests/test_rpm_reply_decoding.py`, `bin/release.sh`, `tests/test_release_script.py`, `ai/approvals.yaml`.
- `bin/release.sh`, `bin/build.sh`, `bin/deploy.sh`, `bin/gtach-preflight.sh` and `bin/pi-install.sh` were read in full at `bb5087c` with `get_file_contents`, to check the effect of the version change to `1.0.0rc1` on unchanged scripts.
- Documentation (`*.md`) changes were counted, not reviewed.
- Open issues: none. Open pull requests: none.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Activity Summary

| Commits | Files changed | Insertions | Deletions | New tags |
|---|---|---|---|---|
| 21 (20 excluding merge `bb5087c`) | 78 file entries | 4,581 | 8,358 | None |

- Totals exclude the merge commit `bb5087c` (Merge pull request #1, release candidate 1.0.0rc1).
- Code-bearing commits: `904bf8f` (mypy pin), `97aef4d` and `cfbf605` (update version ordering), `b2077e6` (010C odd digit count), `55bdbd1` (release.sh pre-release, build-system requires), `3b7b552` (version 1.0.0rc1), `686b945`, `322c990`, `26f7ea6` (approval records).
- All other commits are documentation: design refresh (`efc785e`, `91e8033`, `d232eb3`), audit bce0d69a (`55e6f5d`, `0bc4871`), triple c41037ea (`206fb25`, `d0dac7c`), task register and run reports (`874df8e`, `bff72a3`, `dbe43ad`), proposal (`2f32b45`).
- The newest tag remains `v0.5.0` (`94c7ff0`), outside the window.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Finding F1 — build.sh rejects pre-release versions

- **Classification:** Confirmed. **Severity:** Low.
- **Location:** `bin/build.sh` (unchanged), in combination with `3b7b552` and `55bdbd1`.
- **Evidence:** `3b7b552` sets `version = "1.0.0rc1"`, and `55bdbd1` adds a pre-release path to `bin/release.sh` for versions that do not match `^[0-9]+\.[0-9]+\.[0-9]+$`. `bin/build.sh` still validates any newly entered version against the X.Y.Z form only:

```bash
SEMVER_RE='^[0-9]+\.[0-9]+\.[0-9]+$'
...
    if [[ "$VERSION" =~ $SEMVER_RE ]]; then
        break
    fi
    echo "ERROR: Version must be in X.Y.Z format"
```

- **Effect:** Pressing Enter keeps `1.0.0rc1`, and entering `1.0.0` is accepted. Entering a further release candidate such as `1.0.0rc2` at the prompt is refused, so the documented build path cannot produce the pre-release versions that `release.sh` and `updater.py` now support. The workaround is to edit `pyproject.toml` by hand before running `build.sh`.
- The refactor that introduced pre-release versions is incomplete in this one script.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Observations

- `_parse_version_str` pads releases to three components but does not strip trailing zeros beyond three, so `1.0.0.0` orders above `1.0.0`, although PEP 440 treats them as equal. `build.sh` permits only X.Y.Z, so the case does not arise in the current workflow. Not raised as a finding.
- `tests/test_rpm_reply_decoding.py` includes `"410C1AF"`, which the existing `len(response) >= 8` guard already rejects; that case does not exercise the new odd-count check. The other two cases do.
- The approval records `686b945`, `322c990` and `26f7ea6` are authored by Claude under the delegated approval of `proposal-f8d0064b`. This is recorded for the reader; it is not a code defect.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Changes Reviewed Without Finding

- `97aef4d`, `cfbf605` — `updater.py`: the regex-based order key ranks `a < b < rc < final`, returns `None` for dev, post, local and oversized forms, and the update check now logs an unrecognised installed version (WARNING) and skips unrecognised wheels (DEBUG). The `ValueError` guard in `cfbf605` covers the `int()` digit limit. Tests assert the intended ordering and logging.
- `b2077e6` — `obd.py`: `len(hex_str) % 2` drops an odd-length 010C reply before `bytes.fromhex`, which would otherwise raise.
- `55bdbd1` — `release.sh`: `RELEASE_KIND` is quoted and passed once; `gh release create --prerelease` keeps an rc out of `releases/latest`, which `pi-install.sh` resolves. `build>=0.10.0` removed from `build-system.requires`; `build.sh` still checks for the `build` module separately.
- `904bf8f` — `pyproject.toml`: the mypy pin `>=1.20,<2.0; python_version >= '3.10'` is a valid environment marker.
- `3b7b552` — version `1.0.0rc1`: `deploy.sh` (glob and `cut -d'-' -f2`), `gtach-preflight.sh` (wheel name from marker) and `release.sh` (wheel and tarball names) handle the rc form.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Recommendations

- F1: accept PEP 440 pre-release input in `bin/build.sh`, for example `^[0-9]+\.[0-9]+\.[0-9]+((a|b|rc)[0-9]+)?$`, matching the forms that `updater.py` accepts.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-14 | Scheduled daily audit of commits 2026-11-13 02:05 UTC to 2026-11-14 02:05 UTC. |

---

Copyright (c) 2026 William Watson. MIT License.
