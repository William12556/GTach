Created: 2026 October 07

# Issue: Setup-Mode Lock-Order Deadlock Between Display and Touch Threads

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-e9216e17"
  title: "SetupDisplayManager and SetupStateCoordinator take three locks in opposite orders on the display and touch threads, so a tap on a cached setup screen can deadlock both"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "closed"
  severity: "critical"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-e9216e17"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    Raised from audit-36b6ea95 finding D01 (critical) and the related
    cross-cutting finding X01. The lock cycle was confirmed by source
    review during audit remediation planning on 2026-10-07.

affected_scope:
  components:
    - name: "SetupDisplayManager.render (cached-screen branch)"
      file_path: "src/gtach/display/setup.py"
    - name: "SetupDisplayManager.handle_touch_event"
      file_path: "src/gtach/display/setup.py"
    - name: "SetupStateCoordinator.transition_to_screen / update_state"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
    - name: "CLAUDE.md §4 Core Development Rules (lock rule)"
      file_path: "CLAUDE.md"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: "GTach in setup mode showing WELCOME, CURRENT_DEVICE or COMPLETE (cached screens)."
  steps:
    - "Tap Start Setup, Cancel or New Setup repeatedly."
    - "A tap that lands while the display thread is inside the cached-render window deadlocks both threads."
  frequency: "intermittent"
  reproducibility_conditions: >
    The cycle is certain from source; the frequency depends on the
    interleaving. The display thread enters the window on every frame
    while a cached screen is shown, and the window includes a YAML file
    read (audit C06), which widens it.
  test_data: >
    Lock acquisition order, display thread (setup.py:204-211, 820-832):
      _render_cache_lock → get_state() takes coordinator _state_lock
      _render_cache_lock → _update_touch_regions_safe takes _touch_regions_lock

    Lock acquisition order, touch thread (setup.py:723-727,
    coordinator.py:93-114, setup.py:117-119, 834-836):
      _touch_regions_lock → _handle_touch_action
        → transition_to_screen takes _state_lock
          → _notify_screen_transition_callbacks (still under _state_lock)
            → SetupDisplayManager._on_screen_transition
              → _invalidate_render_cache takes _render_cache_lock

    All three are non-reentrant threading.Lock instances
    (setup.py:87,93; coordinator.py:53).
  error_output: "None. The display freezes; after 45 s the watchdog shuts the process down."

behavior:
  expected: "Taps on setup screens never block rendering."
  actual: >
    CONFIRMED IN SOURCE. The display thread holds _render_cache_lock and
    waits for _state_lock or _touch_regions_lock; the touch thread holds
    _touch_regions_lock and _state_lock and waits for _render_cache_lock.
    Both threads block permanently. The display heartbeat stops and the
    watchdog terminates the process after critical_timeout.
  impact: >
    A hang on the first screen a new user sees. The process is restarted
    by systemd, and the user returns to the same screen.
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    Code calls out while holding a lock: callbacks are invoked under the
    coordinator's state lock, touch actions are dispatched under the
    touch-regions lock, and the render path calls into the coordinator
    and the touch-region setter under the render-cache lock. Any one of
    these, combined with the others, forms the cycle. No project rule
    forbids the pattern (audit X01).
  technical_notes: >
    Removing any single edge breaks this particular cycle, but the same
    pattern exists at other sites (audit X01, D03, D06, C04). All three
    edges in this cycle are removed so that no lock in the setup path is
    held while another lock is taken or a callback is invoked. Other
    sites are handled by change-fbe7e98a.

    SetupStateCoordinator.complete_setup assigns current_screen directly
    without notifying callbacks. It is unaffected by this change and is
    recorded here only because a reviewer may notice the asymmetry.
  related_issues:
    - issue_ref: "issue-fbe7e98a"
      relationship: "related. Same pattern at other sites."

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    1. Coordinator: decide under _state_lock, notify callbacks after
    releasing it. 2. render: hold _render_cache_lock only to read the
    cached surface reference. 3. handle_touch_event: find the hit region
    under _touch_regions_lock, dispatch the action after releasing it.
    4. Add a rule to CLAUDE.md §4: no call-outs while holding a lock.
  change_ref: "change-e9216e17"
  resolved_date: "2026-10-08"
  resolved_by: "change-e9216e17"
  fix_description: "The setup state coordinator now notifies callbacks after releasing _state_lock, render holds _render_cache_lock only to read the cached surface, and handle_touch_event dispatches the touch action after releasing _touch_regions_lock, removing the three-lock cycle (commit f22640a18710bcce996835fe997979672ae6244b)."

verification:
  verified_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Session E (2026-10-08): 15 WELCOME/DISCOVERY Start Setup/Cancel cycles; each transition within ~3 ms of the tap; no watchdog record."
  closure_notes: "Closed at audit-36b6ea95 close-out after on-device verification."

prevention:
  preventive_measures: "CLAUDE.md §4 lock rule; tests asserting no lock is held at each call-out."
  process_improvements: "Reviews of threaded code check every call made while a lock is held."

verification_enhanced:
  verification_steps:
    - "Confirm the cycle from source. [DONE.]"
    - "After the fix: unit tests assert that callbacks, touch actions and cached-region updates run with the relevant locks released."
    - "After the fix: on the Pi, tap Start Setup and Cancel on WELCOME repeatedly for one minute; the display stays responsive."
  verification_results: "All verification steps complete; see verification.test_results."

traceability:
  design_refs: []
  change_refs:
    - "change-e9216e17"
  test_refs: []

notes: "Audit reference: audit-36b6ea95 D01, X01."

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial issue document from audit-36b6ea95 D01 and X01."

  - version: "1.1"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Fix implemented in f22640a18710bcce996835fe997979672ae6244b; awaiting on-device verification."
  - version: "1.2"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "On-device verification complete; closed at audit-36b6ea95 close-out."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial issue document. Three-lock cycle between display and touch threads in setup mode. |
| 1.1 | 2026-10-07 | Fix implemented in f22640a18710bcce996835fe997979672ae6244b; awaiting on-device verification. |
| 1.2 | 2026-10-08 | On-device verification complete; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
