Created: 2026 October 07

# Change: Remove Call-Outs Under Lock in the Setup Path

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-e9216e17"
  title: "Notify coordinator callbacks after releasing _state_lock; hold _render_cache_lock only to read the cache; dispatch setup touch actions after releasing _touch_regions_lock; add a no-call-out-under-lock rule to CLAUDE.md"
  date: "2026-10-07"
  author: "William Watson"
  status: "approved"
  priority: "critical"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-e9216e17"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-e9216e17"
  description: "Resolves issue-e9216e17 (audit-36b6ea95 D01, X01)."

scope:
  summary: >
    Three edits remove every edge of the setup-mode lock cycle. A fourth
    records the rule in CLAUDE.md.
  affected_components:
    - name: "SetupStateCoordinator.transition_to_screen, update_state"
      file_path: "src/gtach/display/setup_components/state/coordinator.py"
      change_type: "modify"
    - name: "SetupDisplayManager.render"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
    - name: "SetupDisplayManager.handle_touch_event"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
    - name: "§4 Core Development Rules"
      file_path: "CLAUDE.md"
      change_type: "modify"
    - name: "Lock-release tests"
      file_path: "tests/test_setup_lock_order.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "The per-frame DeviceStore read in _update_cached_screen_touch_regions (audit C06, Phase 2b). This change moves it outside the render-cache lock but does not remove it."
    - "SetupStateCoordinator.complete_setup, which assigns current_screen without notification."
    - "Other call-out-under-lock sites (AsyncOperationManager, TouchCoordinator, HyperPixelTouchInterface), handled by change-fbe7e98a."
    - "SetupStateCoordinator.get_state returning the live state object (audit D04)."

rational:
  problem_statement: >
    Display thread: _render_cache_lock → _state_lock / _touch_regions_lock.
    Touch thread: _touch_regions_lock → _state_lock → (callback)
    _render_cache_lock. All three are non-reentrant. A tap during the
    display thread's cached-render window deadlocks both threads.
  proposed_solution: >
    EDIT A — coordinator notifications after release. In
    transition_to_screen, perform the state change and record
    (old_screen, new_screen) under _state_lock; call
    _notify_screen_transition_callbacks after the with-block, only if a
    transition occurred. In update_state, collect changed_fields under
    the lock; call _notify_state_change_callbacks after the with-block,
    only if fields changed. Add a docstring sentence to both
    _notify_* methods: "Must be called without _state_lock held."

    EDIT B — render cache lock scope. In SetupDisplayManager.render, in
    the cache-hit branch, take _render_cache_lock only to read
    `cached_surface = self._screen_render_cache.get(state.current_screen)`.
    After releasing it, if cached_surface is not None: blit it, log,
    call _update_cached_screen_touch_regions(), draw the border and
    return. The cache-store block below is unchanged (it calls nothing
    while holding the lock).

    EDIT C — touch dispatch after release. In handle_touch_event, under
    _touch_regions_lock find the first region whose rect contains pos
    and bind (action, region). After the with-block, if a hit was found,
    return self._handle_touch_action(action, region).

    EDIT D — CLAUDE.md §4 rule 8: "Never call out while holding a lock:
    no callbacks, no other component's methods that may take a lock, no
    blocking I/O. Snapshot under the lock, act after releasing it."
    Add a Version History row.
  alternatives_considered:
    - option: "Make all three locks one RLock."
      reason_rejected: "Hides the pattern, serialises unrelated work and keeps callbacks under a lock."
    - option: "Remove only one edge of the cycle."
      reason_rejected: "Leaves the pattern in place for the next change to recreate a cycle."
  benefits:
    - "The setup-mode deadlock is removed."
    - "The rule is documented for future work."
  risks:
    - risk: "Callbacks now observe state that may change again before they run."
      mitigation: >
        The only registered callbacks invalidate the render cache, which
        is idempotent; a later change triggers its own notification.
    - risk: "A cached surface is invalidated between read and blit."
      mitigation: "The reference stays valid; the next frame re-renders."

technical_details:
  current_behavior: "Callbacks, touch actions and cached-region updates run while a lock is held."
  proposed_behavior: "No lock in the setup path is held while another lock is taken or a callback runs."
  implementation_approach: "Narrow three with-blocks; move calls after them."
  code_changes:
    - component: "SetupStateCoordinator"
      file: "src/gtach/display/setup_components/state/coordinator.py"
      change_summary: "EDIT A"
      functions_affected:
        - "transition_to_screen"
        - "update_state"
      classes_affected:
        - "SetupStateCoordinator"
    - component: "SetupDisplayManager"
      file: "src/gtach/display/setup.py"
      change_summary: "EDITS B and C"
      functions_affected:
        - "render"
        - "handle_touch_event"
      classes_affected:
        - "SetupDisplayManager"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "SetupDisplayManager._on_screen_transition / _on_state_change"
      impact: "Now invoked without _state_lock held. They take _render_cache_lock only."
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Deterministic tests that assert lock state inside each call-out."
  test_cases:
    - scenario: "Register a screen-transition callback that tries coordinator._state_lock.acquire(blocking=False); call transition_to_screen to a new screen."
      expected_result: "The acquire succeeds (then release); the callback ran once."
    - scenario: "Same for a state-change callback via update_state with a changed field."
      expected_result: "The acquire succeeds; the callback received the changed field."
    - scenario: "transition_to_screen to the current screen; update_state with an unchanged value."
      expected_result: "No callback invoked."
    - scenario: "handle_touch_event on a registered region, with _handle_touch_action patched to test _touch_regions_lock.acquire(blocking=False)."
      expected_result: "The acquire succeeds; the patched action received the region."
    - scenario: "render() with a cached WELCOME surface and _update_cached_screen_touch_regions patched to test _render_cache_lock.acquire(blocking=False)."
      expected_result: "The acquire succeeds."
    - scenario: "Stress: one thread calls render() on a cached screen, another calls handle_touch_event on 'start'/'cancel' regions, 500 iterations each, with a 10 s join timeout."
      expected_result: "Both threads finish."
  regression_scope:
    - "tests/test_device_list_focus.py"
    - "Full tests/ suite."
  validation_criteria:
    - "No call to a _notify_* method occurs lexically inside a `with self._state_lock` block in coordinator.py."
    - "No call other than dict access occurs inside `with self._render_cache_lock` in render()."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "EDITS A to D and tests."
      owner: "tactical"
    - step: "On the Pi: tap Start Setup and Cancel on WELCOME repeatedly for one minute."
      owner: "human"
  rollback_procedure: "Revert the commit."
  deployment_notes: "None."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-fbe7e98a"
      relationship: "related. Applies the same rule at the remaining sites."
  related_issues:
    - issue_ref: "issue-e9216e17"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-e9216e17 iteration 1."

  - version: "1.1"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Approved for implementation by William Watson."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial change document. Remove all three edges of the setup lock cycle; CLAUDE.md lock rule. |
| 1.1 | 2026-10-07 | Approved for implementation. |

---

Copyright (c) 2026 William Watson. MIT License.
