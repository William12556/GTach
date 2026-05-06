Created: 2026 May 06

# Issue: macOS Window Click Causes Beach Ball; Ctrl+C Requires Force Quit

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Reproduction](<#4.0 reproduction>)
- [5.0 Behavior](<#5.0 behavior>)
- [6.0 Environment](<#6.0 environment>)
- [7.0 Analysis](<#7.0 analysis>)
- [Version History](<#version history>)

---

```yaml
issue_info:
  id: "issue-c3e5a7b9"
  title: "macOS: window click causes beach ball; Ctrl+C requires force quit"
  date: "2026-05-06"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "user_report"
  test_ref: ""
  description: >
    macOS visual test. Clicking in the GTach pygame window triggers the beach ball
    (spinning wait cursor). After beach ball appears, Ctrl+C in the terminal does not
    exit; process requires force quit.

affected_scope:
  components:
    - name: "DisplayManager._display_loop"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._dispatch_mouse_gesture"
      file_path: "src/gtach/display/manager.py"
    - name: "NavigationGestureHandler"
      file_path: "src/gtach/display/navigation_gestures.py"
    - name: "GTachApplication._signal_handler"
      file_path: "src/gtach/app.py"
  designs: []
  version: "current"

reproduction:
  prerequisites: "macOS development environment; GTach running via python -m gtach --macos --debug"
  steps:
    - "Run: python -m gtach --macos --debug"
    - "Wait for WELCOME screen to appear"
    - "Click anywhere inside the pygame window"
    - "Observe: beach ball cursor appears"
    - "Press Ctrl+C in terminal"
    - "Observe: process does not exit; requires force quit (Cmd+Option+Esc)"
  frequency: "always"
  reproducibility_conditions: "macOS only; click must occur after splash completes"
  preconditions: ""
  test_data: >
    Log shows WatchdogMonitor WARNING Thread display appears unresponsive (timeout: 16.4s)
    at 09:43:51. ThreadManager sync ops continue (op#700, #800, #900, #1000) confirming
    the main thread loop is running but the window is unresponsive to Cocoa.
  error_output: >
    2026-05-06 09:43:51,085 WatchdogMonitor WARNING Thread display appears unresponsive
    (timeout: 16.4s)

behavior:
  expected: >
    Click in pygame window dispatches a mouse gesture without blocking; Ctrl+C cleanly
    exits the application from the terminal.
  actual: >
    Click causes macOS to show beach ball (Cocoa considers main thread unresponsive).
    Ctrl+C signal is received but does not produce clean exit; force quit required.
  impact: >
    Application unusable for interactive macOS testing — clicking to test touch
    simulation locks the window. Development workflow significantly impaired.
  workaround: "Avoid clicking in the window; terminate with kill -9 from another terminal"

environment:
  python_version: "3.11"
  os: "macOS (Apple Silicon)"
  dependencies:
    - library: "pygame"
      version: "current"
  domain: "display"

analysis:
  root_cause: >
    Two related problems sharing a common root:

    BEACH BALL:
    The GTach display loop runs on the macOS main thread (Cocoa constraint, correctly
    implemented). pygame.event.get() is called at the top of each display loop iteration.
    On MOUSEBUTTONDOWN, _dispatch_mouse_gesture() is called synchronously within the
    event-processing block. If NavigationGestureHandler.start_gesture_tracking() or
    end_gesture_tracking() acquires a lock, performs I/O, or blocks for any reason,
    the main thread stalls. Cocoa's event pump runs on the same thread and will declare
    the application unresponsive if it does not receive its run loop iteration within
    ~2-5s. The beach ball is Cocoa's response to this stall.

    CTRL+C NOT WORKING:
    Python SIGINT (Ctrl+C) is registered via signal.signal(signal.SIGINT, _signal_handler).
    The signal handler sets _shutdown_event. However, if the main thread is blocked
    inside a gesture handler call (or even inside pygame.event.get() waiting for Cocoa),
    the Python bytecode interpreter cannot deliver the signal between bytecodes.
    Additionally, _signal_handler calling self.shutdown() may itself attempt to join
    threads or acquire locks that are held by the blocked call, creating deadlock.
    Even if the signal fires correctly, pygame.quit() on macOS requires the main thread
    to be in a yielding state.

  technical_notes: >
    Candidate fixes:

    1. BEACH BALL: Make _dispatch_mouse_gesture() non-blocking. Move gesture handling
       to a separate worker thread or use threading.Event/Queue to dispatch gesture
       events asynchronously. The display loop should post to a queue and return
       immediately; the gesture handler processes from the queue in a worker thread.
       NOTE: pygame rendering must remain on the main thread; only gesture dispatch
       can be offloaded.

    2. CTRL+C: In the SIGINT handler, call os.kill(os.getpid(), signal.SIGTERM) as a
       fallback after setting the shutdown event, or use pygame.event.post() to inject
       a QUIT event into the pygame event queue, which will be processed naturally on
       the next event loop iteration without requiring a blocking join.

    3. ALTERNATIVE APPROACH: Replace the synchronous gesture dispatch in the event
       loop with a lightweight threading.Event flag. The event loop sets the flag and
       stores the position; a dedicated gesture thread wakes on the flag, processes
       the gesture, and posts the result back via a thread-safe queue.

    The WatchdogMonitor correctly flagged the display thread as unresponsive at 16.4s,
    confirming the stall originated in the display loop itself, not in a background thread.

  related_issues:
    - issue_ref: "issue-a8f2c3e1-watchdog-display-restart-darwin.md"
      relationship: "related — prior fix routed watchdog recovery to graceful shutdown
        instead of restarting display thread on Darwin; this issue is a different
        manifestation of main-thread blocking on macOS"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial issue — macOS visual test observation |

---

Copyright (c) 2026 William Watson. MIT License.
