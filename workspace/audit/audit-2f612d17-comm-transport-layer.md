Created: 2026 June 03

# T04 Audit Prompt — GTach comm/

```yaml
prompt_info:
  id: "prompt-2f612d17"
  task_type: "audit"          # read-only; uses audit-work / audit-review recipes
  source_ref: "audit-index-2f612d17"   # .ael/ralph/audit-index.md + audit-uml.md
  date: "2026-06-03"
  iteration: 1
  coupled_docs: none          # audit originates its own UUID cycle; no T03/T02 coupling

context:
  purpose: "Read-only quality audit of the comm/ transport layer."
  scope: "src/gtach/comm/ only (19 items; see audit-index.md)."
  recipes: ["audit-work.yaml", "audit-review.yaml"]
  constraints:
    - "Read-only: no writes to any file under src/."
    - "One audit-index item per iteration, in listed order."
```

```yaml
tactical_brief: |
  Read-only quality audit of /Users/williamwatson/Documents/GitHub/GTach/src/gtach/comm/.
  State directory: /Users/williamwatson/Documents/GitHub/GTach/.ael/ralph/
  DO NOT write, edit, or delete any file under src/. Read-only.
  Audit one item per iteration, in order, from audit-index.md (next [ ] item).
  Criteria: style, complexity, error-handling, security, conformance, dead-code.
  Read audit-uml.md for structural context. Read each target source file once.
  Append findings to audit-report.md in the required format; then mark the item [x] in audit-index.md.
  Record the comm/bluetooth.py stub as a dead-code finding, not a skip.
```

notes: "First audit-loop run. Scope intentionally bounded (comm/) to validate the loop end-to-end before wider coverage."

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-06-03 | Initial audit prompt; scope src/gtach/comm/ |

---

Copyright (c) 2026 William Watson. MIT License.
