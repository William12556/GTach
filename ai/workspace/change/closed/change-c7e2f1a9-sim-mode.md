Created: 2026 April 30

# Change: Sim Mode — Hardware-Free Full Application Testing

---

## Table of Contents

- [1.0 Change Information](<#1.0 change information>)
- [2.0 Verification](<#2.0 verification>)
- [Version History](<#version history>)

---

```yaml
change_info:
  id: "change-c7e2f1a9"
  title: "Sim Mode — Hardware-Free Full Application Testing"
  date: "2026-04-30"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-c7e2f1a9"
    issue_iteration: 1
```

---

## 1.0 Change Information

Implemented two simulation transport modes (`--transport simtcp` and `--transport simbt`)
enabling full application testing without physical hardware or a running external emulator.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Verification

```yaml
verification:
  implemented_date: "2026-05-08"
  implemented_by: "AEL / Claude Code"
  verification_date: "2026-05-08"
  verified_by: "William Watson"
  test_results: >
    Code inspection confirmed. sim_transport.py and sim_bluetooth.py created.
    simtcp/simbt choices in transport.py and main.py. pairing_factory injection
    in interface.py. app.py simbt branch with SimBluetoothPairing factory.
  issues_found: []

traceability:
  related_issues:
    - issue_ref: "issue-c7e2f1a9"
      relationship: "source"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-04-30 | William Watson | Initial change document |
| 0.2 | 2026-05-08 | William Watson | Closed — implementation verified in source |

---

Copyright (c) 2026 William Watson. MIT License.
