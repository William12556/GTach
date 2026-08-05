Created: 2026 August 05

# Prompt: Ask the Link, Not the Thread

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-4d9e2f18"
  task_type: "debug"
  source_ref: "change-4d9e2f18"
  target_profile: "claude_code"
  date: "2026-08-05"
  iteration: 1
  coupled_docs:
    change_ref: "change-4d9e2f18"
    change_iteration: 1

context:
  purpose: >
    On the bench on 2026-08-05 the ELM327 emulator's battery went flat,
    taking the adapter off the air mid-session. The instrument continued
    to show a green connection indicator above a gauge holding its last
    RPM. The operator had no way to know the reading was dead.

    Both the indicator and the DISCONNECTED screen are gated on the
    obd_protocol thread's OS status. That thread stays RUNNING for the
    life of the process, because its transport retries indefinitely by
    design. So the indicator is green whenever the software is running,
    and the DISCONNECTED screen — which exists for exactly this
    condition and carries the Setup and Simulate controls — is
    unreachable.
  integration: >
    Two files: src/gtach/display/manager.py and src/gtach/app.py.
    Executor is Claude Code; AEL is not used.

    THE EVIDENCE, from logs/start.log of the 11:46 session, four
    milliseconds apart:

      11:46:23,985 RFCOMMTransport ERROR Failed to connect ...
                   [Errno 113] No route to host
      11:46:23,989 ThreadManager DEBUG Thread obd_protocol
                   transitioned to RUNNING

    Both statements are true. The display believed the second and drew
    a green dot.

    THIS IS THE HIGHEST-SEVERITY DEFECT RAISED IN THIS PROJECT. The
    instrument misreports its primary quantity while positively
    indicating the reading is good, on a device intended for use while
    driving. It does not crash, which is why it survived three sessions
    of logs before the operator met it.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py and src/gtach/app.py."
    - "Do NOT modify anything under src/gtach/comm/. The transport is asked through an injected callback; is_connected() already exists on the OBDTransport interface."
    - "Do NOT stop or restart the obd_protocol thread on transport loss. It must stay alive to reconnect; making the existing thread-status test 'correct' that way trades a display defect for a recovery defect."
    - "Do NOT gate the OPTIONS or ACKNOWLEDGEMENT screens on link state. Settings must remain reachable with the adapter down."
    - "Do NOT let simulation mode report a lost link, ever. Simulation is a display without an adapter and that is its purpose."
    - "Do NOT treat an absent callback as 'connected'. That reproduces the defect silently. Fall back to staleness alone."
    - "Do NOT set the sample timestamp in the simulation branch of the queue drain. A synthetic value is not evidence of a link."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Add a link-state test combining an injected transport connectivity
    callback with a data-staleness timeout, and gate the DISCONNECTED
    screen, the connection indicator and the view key on it instead of
    on thread status.
  requirements:
    functional:
      - "_link_lost() returns False whenever _sim_mode is set, unconditionally and first."
      - "_link_lost() returns True when the callback reports not connected."
      - "_link_lost() returns True when no sample has arrived within LINK_LOSS_TIMEOUT."
      - "_link_lost() returns True when no sample has ever arrived."
      - "Recovery requires LINK_RECOVERY_SAMPLES samples within LINK_LOSS_TIMEOUT of one another, not one sample."
      - "An absent or raising callback degrades to staleness alone."
      - "_render_normal_modes shows the DISCONNECTED screen when _link_lost()."
      - "_draw_status_indicator shows red when _link_lost(), green when data is flowing."
      - "_current_view_key's disconnected member is computed from _link_lost()."
      - "get_thread_status('obd_protocol') is no longer used to decide either."
      - "app.py injects a guarded connectivity callback at both injection sites."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.9)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Negligible. One monotonic read and a comparison per frame, replacing a locked thread-status lookup"
      metric: "time"

design:
  architecture: >
    A status indicator is derived from the thing it names. Two signals,
    because neither alone is sufficient: the socket's own view catches a
    clean disconnect at once, and staleness catches the adapter that
    vanishes without closing its socket — which is the failure actually
    met.
  components:
    - name: "DisplayManager constants"
      type: "constants"
      logic:
        - "LINK_LOSS_TIMEOUT = 2.0 — seconds without a sample before the link is considered lost. Data arrives at 20-50 Hz, so this is 40 to 100 consecutive missed samples. Not a blip."
        - "LINK_RECOVERY_SAMPLES = 2 — samples required within the timeout before the gauge returns."
    - name: "DisplayManager._link_lost"
      type: "function"
      purpose: "Whether the adapter is delivering data."
      interface:
        outputs:
          type: "bool"
      logic:
        - "if self._sim_mode: return False   # FIRST, before anything else"
        - "Read the callback inside try/except; a raise or a None callback means 'socket state unavailable', not 'connected'."
        - "If the callback answered and said not connected: clear the latch, return True."
        - "If self._last_sample_ts is None: return True."
        - "If time.monotonic() - self._last_sample_ts > LINK_LOSS_TIMEOUT: clear the latch, return True."
        - "Return not self._link_ok."
    - name: "DisplayManager sample bookkeeping"
      type: "attributes"
      logic:
        - "_last_sample_ts: monotonic time of the last real sample. None until the first."
        - "_link_ok: latch, set when LINK_RECOVERY_SAMPLES have arrived close enough together, cleared on any loss condition."
        - "_recovery_count: consecutive samples arriving within LINK_LOSS_TIMEOUT of the previous."
    - name: "GTachApplication"
      type: "class"
      purpose: "Supply the socket's view without giving the display a reference into comm."
      logic:
        - "Inject a lambda alongside the four existing callback assignments, guarded so a missing transport yields False rather than raising."
  dependencies:
    internal:
      - "OBDTransport.is_connected — already on the interface, implemented by all three transports. Read-only."
      - "_render_disconnected — reached far more often after this. Unmodified."
      - "change-44bca479's view key — its disconnected member is corrected, the mechanism unchanged."
    external: []

error_handling:
  strategy: >
    Every failure in link assessment must fall towards reporting a lost
    link rather than a good one. A false 'disconnected' costs the
    operator a screen they can leave; a false 'connected' is the defect
    this change removes.
  exceptions:
    - exception: "Exception"
      condition: "The injected callback raises."
      handling: "Treat socket state as unavailable and fall through to staleness. Log at DEBUG once, not per frame."
    - exception: "Exception"
      condition: "Anything in _link_lost."
      handling: "Log at ERROR and return True — assume the link is lost. Never return False from an error path."
  logging:
    level: "INFO on a link-state transition in either direction, so the log records when the operator would have seen the screen change"
    format: "self.logger.info('Link lost — no data for %.1fs', age) / self.logger.info('Link restored')"

testing:
  unit_tests:
    - scenario: "THE ACCEPTANCE TEST. Callback returns True, samples stop, clock advances past LINK_LOSS_TIMEOUT."
      expected: "_link_lost True; DISCONNECTED screen rendered; indicator red. This is the flat-battery case. Run it against the pre-change code too: it will show the gauge, and that is the discrimination."
    - scenario: "Callback True, samples at 20 Hz."
      expected: "_link_lost False after recovery; gauge; indicator green."
    - scenario: "Callback False, samples still arriving."
      expected: "_link_lost True."
    - scenario: "No sample ever, callback True."
      expected: "_link_lost True."
    - scenario: "_sim_mode True with callback False and no samples."
      expected: "_link_lost False. Assert this explicitly; it is the one case where every other signal says lost."
    - scenario: "Callback is None, samples arriving."
      expected: "_link_lost False — staleness alone."
    - scenario: "Callback is None, samples stopped."
      expected: "_link_lost True."
    - scenario: "Callback raises."
      expected: "No exception escapes; staleness alone; not treated as connected."
    - scenario: "_link_lost itself forced to raise internally."
      expected: "Returns True."
    - scenario: "FLAPPING. Samples every 3 s with a 2 s timeout."
      expected: "The screen does not alternate per sample. With recovery requiring two samples within the timeout, the link never recovers and the screen stays DISCONNECTED. Assert that outcome explicitly rather than leaving it to emerge."
    - scenario: "A single sample after a long gap, then nothing."
      expected: "No recovery."
    - scenario: "Recovery: samples resume at 20 Hz after a loss."
      expected: "Gauge returns after LINK_RECOVERY_SAMPLES."
    - scenario: "_current_view_key across a link-state change."
      expected: "The key differs."
    - scenario: "OPTIONS and ACKNOWLEDGEMENT with the link lost."
      expected: "Still drawn; not replaced by the DISCONNECTED screen."
    - scenario: "The simulation branch of the queue drain."
      expected: "Does not set _last_sample_ts."
    - scenario: "grep get_thread_status in manager.py."
      expected: "Not used for connection status or the disconnected decision. Other uses, if any, are unrelated and may remain."
  edge_cases:
    - "time.monotonic() is used, not time.time(). A wall-clock adjustment must not appear as a link loss."
    - "_link_lost is called from the render path at 30 Hz. Keep it cheap: one attribute read, one callback call, one subtraction. Do NOT log per call — log only on transition, or the debug log grows by 30 lines a second for nothing."
    - "The first frames after startup have no sample and no transport: _link_lost is True and the DISCONNECTED screen shows while connecting. That is correct and should be asserted, not worked around."
    - "The DISCONNECTED screen is also reached from the pre-existing condition in _render_normal_modes. After this change there is one condition, not two; make sure the old thread-status clause is removed rather than ANDed with the new one."
    - "app.py has TWO injection sites, at roughly lines 202-205 and 302-305. Both must get the callback or the setup-entry path will lack it."
    - "The transport may not exist when the callback fires — during setup, before select_transport. The guard must yield False, meaning 'not connected', which is correct at that moment."
  validation:
    - "grep confirms _sim_mode is tested first in _link_lost."
    - "grep confirms no per-frame log line was added."
    - "git diff confirms src/gtach/comm/ is untouched."

deliverable:
  format_requirements:
    - "Edit the two files in place. Create no new file."
    - "One commit."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        FIVE EDITS.

        EDIT 1 — constants and state. Class constants beside the others:

            # A lost link is 40 to 100 consecutive missed samples at the
            # 20-50 Hz data rate, not a blip (issue-4d9e2f18).
            LINK_LOSS_TIMEOUT = 2.0
            LINK_RECOVERY_SAMPLES = 2

        In __init__:

            self._last_sample_ts = None
            self._link_connected_callback = None
            self._link_ok = False
            self._recovery_count = 0

        EDIT 2 — timestamp the drain. In _draw_radial_mode's queue-drain
        branch, wherever self._last_rpm is assigned from a drained
        message, also record the arrival:

            now = time.monotonic()
            if (self._last_sample_ts is not None
                    and now - self._last_sample_ts <= self.LINK_LOSS_TIMEOUT):
                self._recovery_count += 1
            else:
                self._recovery_count = 1
            self._last_sample_ts = now
            if self._recovery_count >= self.LINK_RECOVERY_SAMPLES:
                if not self._link_ok:
                    self.logger.info('Link restored')
                self._link_ok = True

        Do NOT do this in the simulation branch. A synthetic RPM is not
        evidence of an adapter.

        EDIT 3 — _link_lost:

            def _link_lost(self) -> bool:
                """Whether the adapter has stopped delivering data.

                Two signals, because neither alone suffices. The
                transport's own view catches a clean disconnect at once.
                Staleness catches an adapter that vanishes without
                closing its socket — a flat battery — which is the
                failure this method exists for and the one the previous
                thread-status proxy could never see.
                """
                try:
                    if self._sim_mode:
                        return False

                    connected = None
                    cb = self._link_connected_callback
                    if cb is not None:
                        try:
                            connected = bool(cb())
                        except Exception:
                            connected = None   # unavailable, NOT connected

                    if connected is False:
                        self._link_ok = False
                        self._recovery_count = 0
                        return True

                    if self._last_sample_ts is None:
                        return True

                    age = time.monotonic() - self._last_sample_ts
                    if age > self.LINK_LOSS_TIMEOUT:
                        if self._link_ok:
                            self.logger.info(
                                'Link lost — no data for %.1fs', age
                            )
                        self._link_ok = False
                        self._recovery_count = 0
                        return True

                    return not self._link_ok

                except Exception as e:
                    self.logger.error(f'Link state error: {e}', exc_info=True)
                    return True

        Note the two log lines fire on transition only, guarded by the
        latch. Do not add an unguarded log line here; this runs 30 times
        a second.

        EDIT 4 — the two call sites and the key.

        In _render_normal_modes, replace:

            thread_status = self.thread_manager.get_thread_status('obd_protocol')
            if thread_status != ThreadStatus.RUNNING and not self._sim_mode:
                self._render_disconnected()
                return

        with:

            # Link state, not thread liveness. The obd_protocol thread
            # stays RUNNING while its transport retries indefinitely,
            # so the old test reported a live connection whenever the
            # software was running (issue-4d9e2f18). _link_lost is
            # already False in simulation mode, so the _sim_mode clause
            # is subsumed rather than duplicated.
            if self._link_lost():
                self._render_disconnected()
                return

        In _draw_status_indicator (manager.py:2158), replace the
        thread-status block with:

            if self._link_lost():
                status = ConnectionStatus.DISCONNECTED
            elif not self._link_ok:
                status = ConnectionStatus.CONNECTING
            else:
                status = ConnectionStatus.CONNECTED

        In _current_view_key, replace the computation of its
        'disconnected' member with self._link_lost(). This corrects an
        existing member; do not add a second one.

        EDIT 5 — remove any now-unused ThreadStatus import only if
        nothing else in the file uses it. Check rather than assume.
    - path: "src/gtach/app.py"
      content: |
        EDIT 6 — inject the callback at BOTH sites.

        Alongside the existing four assignments at approximately
        app.py:202-205 and again at 302-305, add:

            # The display asks the transport whether the link is up.
            # Guarded: during setup, and before select_transport has
            # run, there is no transport — and 'no transport' is
            # correctly 'not connected' (issue-4d9e2f18).
            self._display._link_connected_callback = (
                lambda: bool(
                    getattr(self, '_transport', None)
                    and self._transport.is_connected()
                )
            )

        Both sites. The setup-entry path uses the first block, and an
        operator who enters setup and returns must not lose link
        detection.

        Change nothing else in app.py.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py src/gtach/app.py passes."
  - "pytest tests/ passes with no new failures."
  - "The acceptance test — callback True, samples stopped, clock advanced — yields the DISCONNECTED screen after the change and the gauge before it. Both results recorded."
  - "_link_lost returns False whenever _sim_mode is set, tested first."
  - "_link_lost returns True from its exception handler."
  - "An absent or raising callback yields staleness-only behaviour, never an assumption of connected."
  - "Recovery requires two samples within LINK_LOSS_TIMEOUT; one sample after a long gap does not recover."
  - "The simulation branch of the queue drain does not set _last_sample_ts."
  - "_render_normal_modes, _draw_status_indicator and _current_view_key all use _link_lost."
  - "get_thread_status('obd_protocol') is not used to decide connection status or the disconnected screen."
  - "No log line is emitted per frame; link logging is on transition only."
  - "app.py assigns _link_connected_callback at both injection sites."
  - "src/gtach/comm/ is byte-identical."
  - "No file other than the two named above is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "app"
        path: "src/gtach/app.py"
      - name: "transport"
        path: "src/gtach/comm/transport.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "GTachApplication"
        module: "gtach.app"
      - name: "ConnectionStatus"
        module: "gtach.display.models"
      - name: "OBDTransport"
        module: "gtach.comm.transport"
    functions:
      - name: "_link_lost"
        module: "gtach.display.manager"
        signature: "_link_lost(self) -> bool"
      - name: "_render_normal_modes"
        module: "gtach.display.manager"
        signature: "_render_normal_modes(self) -> None"
      - name: "_draw_status_indicator"
        module: "gtach.display.manager"
        signature: "_draw_status_indicator(self) -> None"
      - name: "_current_view_key"
        module: "gtach.display.manager"
        signature: "_current_view_key(self) -> tuple"
      - name: "is_connected"
        module: "gtach.comm.transport"
        signature: "is_connected(self) -> bool"
    constants:
      - name: "LINK_LOSS_TIMEOUT"
        module: "gtach.display.manager"
      - name: "LINK_RECOVERY_SAMPLES"
        module: "gtach.display.manager"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-4d9e2f18-link-loss-detection.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results. Then, once you are finished, write
  a report of what you have done in the ai/workspace/report folder.

  Write the acceptance test first and run it against the unchanged
  file. The failure it reproduces — callback still reporting connected
  while samples have stopped — is the exact shape of the bench failure,
  and a test that cannot show the old code drawing a gauge in that
  state is not testing this defect.

  Every error path in _link_lost returns True. That asymmetry is
  deliberate and is the safety property of this change: a false
  'disconnected' costs the operator a screen they can leave in one
  swipe, while a false 'connected' is what put a stale needle and a
  green light in front of a driver. If you find yourself writing a
  path that returns False on failure, it is wrong.

  Do not be tempted to make the thread-status test correct by stopping
  the obd_protocol thread when the transport drops. The thread must
  survive to reconnect, and the watchdog would restart what it stopped.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial prompt document coupled to change-4d9e2f18. |

---

Copyright (c) 2026 William Watson. MIT License.
