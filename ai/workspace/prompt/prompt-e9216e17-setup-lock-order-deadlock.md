Created: 2026 October 07

# Prompt: Remove Call-Outs Under Lock in the Setup Path

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-e9216e17"
  task_type: "debug"
  source_ref: "change-e9216e17"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-e9216e17"
    change_iteration: 1

context:
  purpose: >
    Remove the setup-mode deadlock: the display and touch threads take
    _render_cache_lock, _touch_regions_lock and the coordinator's
    _state_lock in opposite orders because code calls out while holding
    each of them.
  integration: >
    src/gtach/display/setup_components/state/coordinator.py,
    src/gtach/display/setup.py, CLAUDE.md, one new test module.
  knowledge_references:
    - "ai/workspace/issues/issue-e9216e17-setup-lock-order-deadlock.md"
    - "ai/workspace/change/change-e9216e17-setup-lock-order-deadlock.md"
    - "ai/workspace/audit/audit-36b6ea95-full-codebase.md (D01, X01)"
  constraints:
    - "CRITICAL: after this change, no callback, no _handle_touch_action call and no _update_cached_screen_touch_regions call may occur while _state_lock, _touch_regions_lock or _render_cache_lock is held."
    - "Do not change lock types (all remain threading.Lock)."
    - "Do not change what callbacks do, what touch actions do, or what is cached."
    - "Do not modify _update_cached_screen_touch_regions or the DeviceStore read inside it (audit C06 is a later change)."
    - "Do not modify complete_setup or get_state."
    - "Do not modify src/gtach/display/manager_backup.py or setup_original_backup.py."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to D from the change document and add tests/test_setup_lock_order.py."
  requirements:
    functional:
      - "Screen-transition and state-change callbacks run after _state_lock is released, and only when something changed."
      - "render() holds _render_cache_lock only to read the cached surface."
      - "handle_touch_event() holds _touch_regions_lock only to find the hit region."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"
  performance: []

design:
  architecture: "Snapshot under the lock, act after releasing it."
  components:
    - name: "EDIT A — SetupStateCoordinator"
      type: "class"
      purpose: "Notify without holding _state_lock."
      logic:
        - "transition_to_screen: initialise `transitioned = None` before the with-block. Inside, keep all existing logic but replace the _notify_screen_transition_callbacks call with `transitioned = (old_screen, screen)`. After the with-block: `if transitioned: self._notify_screen_transition_callbacks(*transitioned)`."
        - "update_state: keep the changed_fields collection inside the lock; move the `if changed_fields: self._notify_state_change_callbacks(changed_fields)` after the with-block."
        - "Add to both _notify_* docstrings: 'Must be called without _state_lock held (issue-e9216e17).'"
    - name: "EDIT B — SetupDisplayManager.render"
      type: "function"
      purpose: "Narrow the render-cache lock."
      logic:
        - "Replace the cache-hit block with: `cached_surface = None`; `with self._render_cache_lock: cached_surface = self._screen_render_cache.get(state.current_screen)`; then `if cached_surface is not None:` blit, debug log, `self._update_cached_screen_touch_regions()`, `self._draw_circular_border(surface)`, `return`."
        - "Keep the outer `if not self._screen_needs_refresh:` condition."
        - "Leave the cache-store block unchanged."
    - name: "EDIT C — SetupDisplayManager.handle_touch_event"
      type: "function"
      purpose: "Dispatch outside the touch-regions lock."
      logic:
        - "Keep register_interaction() first."
        - "`hit = None`; under _touch_regions_lock iterate regions with the existing tests and on the first match set `hit = (region[0], region)` and break."
        - "After the with-block: `if hit is not None: return self._handle_touch_action(*hit)`."
        - "Keep the outer try/except and the final `return None`."
    - name: "EDIT D — CLAUDE.md"
      type: "module"
      purpose: "Record the rule."
      logic:
        - "In §4 Core Development Rules add rule 8: '**Locks**: never call out while holding a lock — no callbacks, no calls into another component that may take a lock, no blocking I/O. Snapshot under the lock, act after releasing it (issue-e9216e17).'"
        - "Add a Version History row: next minor version, today's date, 'Rule 8: no call-outs under a lock (change-e9216e17)'."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged. Existing try/except blocks are kept."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "SetupStateCoordinator; register a transition callback that records `coordinator._state_lock.acquire(blocking=False)` (releasing if acquired); transition_to_screen(SetupScreen.DISCOVERY) from WELCOME."
      expected: "Recorded value True; callback called once with (WELCOME, DISCOVERY)."
    - scenario: "Same pattern for a state-change callback; update_state(error_message='x')."
      expected: "Recorded True; callback received ['error_message']."
    - scenario: "transition_to_screen to the current screen; update_state with an unchanged value."
      expected: "No callback calls."
    - scenario: "SetupDisplayManager with touch_regions=[('start', pygame.Rect(0,0,10,10))]; patch _handle_touch_action to record _touch_regions_lock.acquire(blocking=False); handle_touch_event((5,5))."
      expected: "Recorded True; patched action received ('start', region)."
    - scenario: "SetupDisplayManager with a cached WELCOME surface and _screen_needs_refresh False; patch _update_cached_screen_touch_regions to record _render_cache_lock.acquire(blocking=False); render() onto a 480×480 surface."
      expected: "Recorded True."
    - scenario: "Stress: thread A calls render() 500 times on cached WELCOME; thread B calls handle_touch_event on a 'cancel' region 500 times with _handle_touch_action routed through state_coordinator.transition_to_screen alternating WELCOME/CURRENT_DEVICE; join both with timeout=10."
      expected: "Both threads finish."
  edge_cases:
    - "A callback that itself calls get_state() must not deadlock (it previously would have, under the non-reentrant lock)."
  validation:
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit existing files in place; add one test module."
    - "Construct SetupDisplayManager in tests as tests/test_device_list_focus.py does, or with lightweight stubs; patch get_async_manager if construction would start worker threads."
  files:
    - path: "src/gtach/display/setup_components/state/coordinator.py"
      content: "EDIT A"
    - path: "src/gtach/display/setup.py"
      content: "EDITS B and C"
    - path: "CLAUDE.md"
      content: "EDIT D"
    - path: "tests/test_setup_lock_order.py"
      content: "testing.unit_tests"

success_criteria:
  - "In coordinator.py, no _notify_* call lies inside a `with self._state_lock:` block."
  - "In setup.py render(), the `with self._render_cache_lock:` block in the cache-hit path contains only the dictionary read."
  - "In setup.py handle_touch_event(), _handle_touch_action is called outside the `with self._touch_regions_lock:` block."
  - "CLAUDE.md §4 contains rule 8."
  - "tests/test_setup_lock_order.py passes, including the stress test."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "coordinator"
        path: "src/gtach/display/setup_components/state/coordinator.py"
      - name: "setup"
        path: "src/gtach/display/setup.py"
    classes:
      - name: "SetupStateCoordinator"
        module: "gtach.display.setup_components.state.coordinator"
      - name: "SetupDisplayManager"
        module: "gtach.display.setup"
    functions:
      - name: "transition_to_screen"
        module: "gtach.display.setup_components.state.coordinator"
        signature: "(self, screen: SetupScreen, clear_cache: bool = True) -> None"
      - name: "update_state"
        module: "gtach.display.setup_components.state.coordinator"
        signature: "(self, **kwargs) -> None"
      - name: "render"
        module: "gtach.display.setup"
        signature: "(self, target_surface=None) -> None"
      - name: "handle_touch_event"
        module: "gtach.display.setup"
        signature: "(self, pos: Tuple[int, int]) -> Optional[SetupAction]"
    constants: []

notes: >
  On-target verification is a human step: enter setup, then tap Start
  Setup and Cancel on WELCOME repeatedly for one minute; the display must
  stay responsive and error.log must show no watchdog shutdown.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-e9216e17 iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
