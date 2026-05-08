Created: 2026 May 08

---

## Table of Contents

- [1. Prompt Information](<#1. prompt information>)
- [2. Tactical Brief](<#2. tactical brief>)
- [3. Version History](<#3. version history>)

---

## 1. Prompt Information

```yaml
prompt_info:
  id: "prompt-d2e4a1f9"
  task_type: "debug"
  source_ref: "change-d2e4a1f9"
  date: "2026-05-08"
  iteration: 1
  coupled_docs:
    change_ref: "change-d2e4a1f9"
    change_iteration: 1

context:
  purpose: >
    Fix data race in DisplayManager._draw_status_indicator by replacing
    direct unlocked access to ThreadManager.threads with the locked public
    accessor get_thread_status().
  integration: >
    DisplayManager (src/gtach/display/manager.py) reads ThreadManager.threads
    directly in _draw_status_indicator. ThreadManager (src/gtach/core/thread.py)
    protects threads with _state_lock. get_thread_status(name) is the correct
    locked accessor.
  knowledge_references: []
  constraints:
    - "Single function edit — _draw_status_indicator only"
    - "No changes to ThreadManager"
    - "get_thread_status returns Optional[ThreadStatus] — None maps to DISCONNECTED"

specification:
  requirements:
    functional:
      - "Replace direct self.thread_manager.threads access with get_thread_status('transport')"
      - "None return from get_thread_status maps to ConnectionStatus.DISCONNECTED"
      - "RUNNING maps to CONNECTED, STARTING maps to CONNECTING, all else DISCONNECTED"
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "No interface changes"

design:
  architecture: "Use existing locked public accessor"
  components:
    - name: "DisplayManager._draw_status_indicator"
      type: "method"
      purpose: "Replace unlocked dict access with get_thread_status()"
      logic:
        - "Remove: 'transport' not in self.thread_manager.threads check"
        - "Remove: self.thread_manager.threads['transport'].status"
        - "Add: thread_status = self.thread_manager.get_thread_status('transport')"
        - "Map: RUNNING -> CONNECTED, STARTING -> CONNECTING, None/other -> DISCONNECTED"

  dependencies:
    internal:
      - "src/gtach/display/manager.py"
    external: []

deliverables:
  - file: "src/gtach/display/manager.py"
    changes: "_draw_status_indicator — replace dict access with get_thread_status()"

success_criteria:
  - "No direct access to self.thread_manager.threads in _draw_status_indicator"
  - "Status indicator renders correctly in simbt session"
  - "No KeyError or AttributeError in log"
```

---

## 2. Tactical Brief

```yaml
tactical_brief: |
  Fix unlocked thread dict read in _draw_status_indicator.

  File to modify: src/gtach/display/manager.py

  In DisplayManager._draw_status_indicator, replace:

    try:
        # Check transport thread status
        if 'transport' not in self.thread_manager.threads:
            status = ConnectionStatus.DISCONNECTED
        else:
            thread_status = self.thread_manager.threads['transport'].status
            if thread_status == ThreadStatus.RUNNING:
                status = ConnectionStatus.CONNECTED
            elif thread_status == ThreadStatus.STARTING:
                status = ConnectionStatus.CONNECTING
            else:
                status = ConnectionStatus.DISCONNECTED

  With:

    try:
        # Check transport thread status via locked public accessor
        thread_status = self.thread_manager.get_thread_status('transport')
        if thread_status == ThreadStatus.RUNNING:
            status = ConnectionStatus.CONNECTED
        elif thread_status == ThreadStatus.STARTING:
            status = ConnectionStatus.CONNECTING
        else:
            status = ConnectionStatus.DISCONNECTED

  Hard constraints:
  - Only modify _draw_status_indicator
  - Do not change ThreadManager
  - get_thread_status returns None when thread not registered — this maps
    to the else branch (DISCONNECTED), which is correct

  Success: no direct access to self.thread_manager.threads in this function
```

---

## 3. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-05-08 | Initial prompt document |

---

Copyright (c) 2026 William Watson. MIT License.
