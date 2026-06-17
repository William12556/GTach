Created: 2026 May 06

# Prompt: Fix macOS Beach Ball and Ctrl+C Deadlock

---

```yaml
prompt_info:
  id: "prompt-c3e5a7b9"
  task_type: "code_generation"
  source_ref: "change-c3e5a7b9"
  date: "2026-05-06"
  iteration: 1
  coupled_docs:
    change_ref: "change-c3e5a7b9"
    change_iteration: 1
```

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Task: fix macOS beach ball on window click and Ctrl+C deadlock (c3e5a7b9).

  FILES: src/gtach/display/manager.py, src/gtach/app.py

  ── FILE 1: src/gtach/display/manager.py ──────────────────────────────

  CHANGE 1 — DisplayManager.__init__, inside the macOS block
  (the block guarded by "if self._is_macos:"):
  After the existing mouse state attributes, add:
    import queue as _queue
    self._mouse_event_queue = _queue.Queue(maxsize=4)
    self._gesture_worker_thread = threading.Thread(
        target=self._gesture_worker, daemon=True, name='GestureWorker')
    self._gesture_worker_thread.start()

  CHANGE 2 — DisplayManager._display_loop, macOS event handling:
  Inside the "elif self._is_macos:" branch, locate the MOUSEBUTTONUP handler:
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._mouse_dragging:
        self._dispatch_mouse_gesture(event.pos)   # <-- THIS LINE
        self._mouse_dragging = False
        ...

  Replace:
    self._dispatch_mouse_gesture(event.pos)
  With:
    try:
        self._mouse_event_queue.put_nowait({
            'up_pos': event.pos,
            'down_pos': self._mouse_down_pos,
            'down_time': self._mouse_down_time,
        })
    except Exception:
        pass  # queue full — discard

  CHANGE 3 — Add new method _gesture_worker to DisplayManager:
  def _gesture_worker(self) -> None:
      """Daemon worker: dequeue mouse gesture events and dispatch off main thread."""
      while not self._shutdown_event.is_set():
          try:
              evt = self._mouse_event_queue.get(timeout=0.1)
              self._mouse_down_pos = evt['down_pos']
              self._mouse_down_time = evt['down_time']
              self._dispatch_mouse_gesture(evt['up_pos'])
          except Exception:
              pass  # timeout or queue empty — loop

  ── FILE 2: src/gtach/app.py ──────────────────────────────────────────

  CHANGE 4 — GTachApplication._signal_handler:
  After self.shutdown() (or the existing shutdown call), append:
    try:
        import pygame as _pg
        if _pg.get_init():
            _pg.event.post(_pg.event.Event(_pg.QUIT))
    except Exception:
        pass

  ── CONSTRAINTS ───────────────────────────────────────────────────────
  - Do not modify NavigationGestureHandler
  - _gesture_worker must be a daemon thread (daemon=True)
  - Queue maxsize=4; use put_nowait with silent discard on Full
  - All new code wrapped in try/except; no new imports at module level
    (use local imports inside methods)
  - Do not alter Pi or non-macOS code paths

  VERIFY:
    python -c "import ast; ast.parse(open('src/gtach/display/manager.py').read())"
    python -c "import ast; ast.parse(open('src/gtach/app.py').read())"
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial prompt |

---

Copyright (c) 2026 William Watson. MIT License.
