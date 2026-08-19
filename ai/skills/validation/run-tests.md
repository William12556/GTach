Created: 2026 July 17

# Skill Template: Pytest Validation Hook

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Installation](<#2.0 installation>)
[3.0 Hook Configuration](<#3.0 hook configuration>)
[4.0 Hook Script](<#4.0 hook script>)
[5.0 Scope and Limitations](<#5.0 scope and limitations>)
[Version History](<#version history>)

---

## 1.0 Purpose

Canonical source for the PostToolUse validation hook specified in governance P06 §1.7.15 (Code validation: executes pytest for modified component). Provisioned into downstream projects during P01 §1.2.8 (Claude and claude-omlx profiles).

Mandatory for `claude_code` and `claude_omlx` target profiles. Not applicable to the `ael` profile — AEL has no Claude Code hook runtime; test execution for AEL-generated code remains a Strategic Domain review step.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Installation

- Copy this document's §4.0 script content to `<project-root>/.claude/hooks/run-tests.sh`
- `chmod +x .claude/hooks/run-tests.sh`
- Merge this document's §3.0 JSON block into `<project-root>/.claude/settings.json` under the top-level `hooks` key (create the file if absent)
- `.claude/settings.json` is git-tracked (team-shared); do not place this hook in `.claude/settings.local.json`

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Hook Configuration

Add under `.claude/settings.json` → `hooks` → `PostToolUse`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-tests.sh"
          }
        ]
      }
    ]
  }
}
```

If `.claude/settings.json` already has a `hooks` key, add `PostToolUse` as a sibling of existing event keys rather than replacing the object.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Hook Script

Save as `.claude/hooks/run-tests.sh`:

```bash
#!/bin/bash
# run-tests.sh — PostToolUse pytest validation (governance P06 §1.7.15)
# Runs targeted tests for the file Claude just modified. Does not block
# the write itself (PostToolUse cannot undo a completed tool call);
# reports failure back to Claude via decision:block so it can revise.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[[ -z "$FILE_PATH" ]] && exit 0

TARGET=""
if [[ "$FILE_PATH" == tests/* ]]; then
  TARGET="$FILE_PATH"
elif [[ "$FILE_PATH" == src/*/*.py ]]; then
  COMPONENT=$(echo "$FILE_PATH" | cut -d/ -f2)
  [[ -d "tests/${COMPONENT}" ]] && TARGET="tests/${COMPONENT}/"
fi

[[ -z "$TARGET" ]] && exit 0

RESULT=$(python -m pytest "$TARGET" -q 2>&1)
STATUS=$?

if [[ $STATUS -ne 0 ]]; then
  REASON=$(echo "$RESULT" | tail -n 20 | jq -Rs .)
  echo "{\"decision\": \"block\", \"reason\": ${REASON}}"
fi

exit 0
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Scope and Limitations

- File-level targeted validation only (per-modification). Iteration-level full-suite validation remains a Strategic Domain review step (governance P06 §1.7.15 Progressive Validation Strategy) and is not automated by this hook.
- `PostToolUse` cannot undo a write already made; a failing test surfaces as feedback for Claude to revise in a subsequent turn, not as a blocked edit.
- Requires `jq` on the tactical execution host.
- Test-to-component mapping assumes `tests/<component>/` layout per governance P06 §1.7.3/§1.7.7. Projects with a different layout must adapt §4.0 before provisioning.
- The other §1.1.18 example skills (`.claude/governance/validate-design.md`, `.claude/testing/generate-pytest.md`, `.claude/validation/coupling-check.md`, `.claude/audit/protocol-compliance.md`) remain illustrative only; not addressed by this template.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-17 | Initial canonical template — closes P06 §1.7.15 PostToolUse pytest gap for claude_code/claude_omlx profiles |

---

Copyright (c) 2026 William Watson. MIT License.
