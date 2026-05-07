Created: 2026 May 06

# Change: Fix macOS Beach Ball and Ctrl+C Deadlock

---

```yaml
change_info:
  id: "change-c3e5a7b9"
  title: "Fix macOS main-thread stall on mouse click and SIGINT deadlock"
  date: "2026-05-06"
  author: "William Watson"
  status: "approved"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-c3e5a7b9"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-c3e5a7b9-macos-click-beachball-ctrlc-deadlock.md"
  description: >
    macOS: clicking in pygame window causes beach ball; Ctrl+C requires force quit.
    Root: gesture dispatch blocks the Cocoa main thread; SIGINT handler cannot
    cleanly interrupt a blocked display loop.

scope:
  summary: >
    Two targeted changes to manager.py:
    1. Move gesture dispatch off the event-processing path into a background thread
       via a thread-safe queue, so the main thread never blocks on gesture logic.
    2. Inject a pygame QUIT event from the SIGINT handler so Ctrl+C cleanly exits
       the display loop without requiring a blocked join.
  affected_components:
    - name: "DisplayManager._display_loop"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager.__init__"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "GTachApplication._signal_handler"
      file_path: "src/gtach/app.py"
      change_type: "modify"
  out_of_scope:
    - "NavigationGestureHandler internals"
    - "Pi display path (not affected by macOS Cocoa constraint)"

rational:
  problem_statement: >
    The Cocoa run loop and the pygame event pump share the macOS main thread.
    Any synchronous call within pygame.event.get() processing that stalls
    (gesture handler lock contention, logging, I/O) prevents Cocoa from
    receiving its periodic run-loop tick, triggering the beach ball.
    SIGINT cannot cleanly interrupt a thread blocked inside C extension code
    (pygame/Cocoa), and the shutdown path attempts joins that deadlock against
    the blocked main thread.
  proposed_solution: >
    BEACH BALL: Post mouse events to a queue; return from event processing
    immediately. A daemon worker thread dequeues and calls gesture handler
    logic, then posts results back via a thread-safe flag/queue for the
    display loop to act on.

    CTRL+C: In _signal_handler, after setting _shutdown_event, call
    pygame.event.post(pygame.event.Event(pygame.QUIT)) so the display loop
    exits through its normal QUIT branch on the very next event.get() call,
    regardless of what the gesture worker is doing.
  alternatives_considered:
    - option: "pygame.event.pump() on a timer"
      reason_rejected: "Does not unblock a stalled synchronous gesture call"
    - option: "Increase watchdog timeout"
      reason_rejected: "Masks symptom; does not fix the stall"
  benefits:
    - "Clicking in window no longer causes beach ball"
    - "Ctrl+C cleanly exits the application from the terminal"
    - "No change to gesture handling logic or Pi runtime path"
  risks:
    - risk: "Gesture results arrive one event loop iteration later (~16ms)"
      mitigation: "Imperceptible; acceptable latency for a touch/mouse gesture"
    - risk: "Queue accumulation if gestures fire faster than worker processes"
      mitigation: "Queue is bounded (maxsize=1 with get_nowait/discard pattern)"

technical_details:
  current_behavior: >
    MOUSEBUTTONDOWN → _dispatch_mouse_gesture() called synchronously in event loop.
    SIGINT → _signal_handler sets _shutdown_event; display loop may not observe it
    if blocked.
  proposed_behavior: >
    MOUSEBUTTONDOWN → mouse event posted to _mouse_event_queue; event loop returns
    immediately. Worker thread dequeues, calls gesture dispatch, posts result.
    SIGINT → _signal_handler sets _shutdown_event AND posts pygame.QUIT event.
  implementation_approach: >
    In DisplayManager.__init__ (macOS path): create _mouse_event_queue = queue.Queue(maxsize=4)
    and start _gesture_worker_thread (daemon=True).

    In _display_loop event processing (macOS path): replace direct _dispatch_mouse_gesture()
    call with _mouse_event_queue.put_nowait(...) wrapped in try/except Full.

    Add _gesture_worker() method: loops on _mouse_event_queue.get(), calls
    _dispatch_mouse_gesture(), until _shutdown_event is set.

    In GTachApplication._signal_handler: after self.shutdown(), if pygame is available
    and initialized, call pygame.event.post(pygame.event.Event(pygame.QUIT)).
  code_changes:
    - component: "DisplayManager.__init__"
      file: "src/gtach/display/manager.py"
      change_summary: "Add _mouse_event_queue and _gesture_worker_thread for macOS path"
      functions_affected: ["__init__"]
    - component: "DisplayManager._display_loop"
      file: "src/gtach/display/manager.py"
      change_summary: "Replace synchronous _dispatch_mouse_gesture call with queue put"
      functions_affected: ["_display_loop"]
    - component: "DisplayManager._gesture_worker (new)"
      file: "src/gtach/display/manager.py"
      change_summary: "Daemon worker: dequeue mouse events, call _dispatch_mouse_gesture"
      functions_affected: ["_gesture_worker"]
    - component: "GTachApplication._signal_handler"
      file: "src/gtach/app.py"
      change_summary: "Post pygame.QUIT event after setting shutdown event"
      functions_affected: ["_signal_handler"]
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
