#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Display Manager - Refactored for component-based architecture.

Orchestrates display rendering, touch handling, and performance monitoring
through extracted components for improved maintainability.
"""

import os
import sys
import math
import logging
import queue
import threading
import time
from enum import Enum, auto
from typing import Optional, Tuple, Dict, Any, Sequence, Callable, List

# Conditional imports for hardware dependencies
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

# Component imports
from .rendering import DisplayRenderingEngine, RenderTarget
from .input import TouchEventCoordinator, TouchAction, GestureType
from .performance import PerformanceMonitor

# Legacy imports for compatibility
from .models import (DisplayMode, DisplayConfig, ConnectionStatus,
                     Palette, DAY_PALETTE, NIGHT_PALETTE)
from .splash import SplashScreen
from .typography import (get_font_manager, get_title_font, get_medium_font, get_small_font, get_minimal_font,
                         get_rpm_large_font, get_rpm_medium_font, get_label_small_font, 
                         get_title_display_font, get_heading_font, TypographyConstants,
                         get_button_renderer, ButtonSize, ButtonState)
from ..core import ThreadManager
from ..utils import TerminalRestorer
from ..utils.ack_state import AcknowledgementStateManager

class DisplayManager:
    """
    Refactored display manager using component-based architecture.
    
    Orchestrates display rendering, touch handling, and performance monitoring
    through specialized components for improved maintainability and testing.
    """

    # The face and band colours that change-5014040c named as class
    # constants here now live in Palette (models.py), so day and night
    # are two instances rather than two sets of edits (change-5012004e).

    # How many pages the options menu holds. Named rather than written
    # as a literal in the paging modulo, so a third page is a data
    # change (change-8c5a1e73).
    OPTIONS_PAGE_COUNT = 2

    # A lost link is 40 to 100 consecutive missed samples at the
    # 20-50 Hz data rate, not a blip (issue-4d9e2f18).
    LINK_LOSS_TIMEOUT = 2.0
    LINK_RECOVERY_SAMPLES = 2

    def __init__(self, thread_manager: ThreadManager, terminal_restorer: TerminalRestorer = None, config_path: str = 'config.yaml'):
        self.logger = logging.getLogger('DisplayManager')
        self.thread_manager = thread_manager
        self.config_path = config_path
        self._shutdown_event = threading.Event()
        self.terminal_restorer = terminal_restorer
        self._sim_mode = False  # Session-only simulation mode flag
        self._debug_toggle_callback = None  # Set by app.py: Callable[[bool], None]
        self._debug_logging_on = False      # Reflects current debug logging state
        self._restart_callback = None       # Set by app.py: Callable[[], None]
        self._options_view = 'menu'         # 'menu' | 'update' | 'confirm_clear'

        # The mode OPTIONS was entered from, restored on exit.
        # Not simply RADIAL: OPTIONS is reachable from the
        # DISCONNECTED condition too, and returning to a gauge with
        # no data would be wrong (change-3e8b1d72).
        self._pre_options_mode = None

        # Which options page is displayed. Session state; not
        # persisted, so OPTIONS always opens on page 0
        # (change-8c5a1e73).
        self._options_page = 0

        # Link state. The obd_protocol thread stays RUNNING while its
        # transport retries indefinitely, so thread liveness cannot
        # answer "is the adapter delivering data" (issue-4d9e2f18).
        # These are what answers it instead.
        self._last_sample_ts = None          # monotonic time of the last real sample
        self._link_connected_callback = None  # injected by app.py; asks the transport
        # Also injected by app.py; asks the transport why the last
        # connect failed. A callback rather than a transport reference
        # so the display keeps no hard dependency on comm, matching
        # _link_connected_callback above (issue-5e7a03c4).
        self._link_cause_callback = None
        # Same pattern again; supplies the retry-countdown arc's
        # PERIOD only. The arc's phase never comes from here — see
        # _draw_retry_arc (issue-4f1e82b7).
        self._retry_interval_callback = None
        # Also injected by app.py. Reboots the Pi. When left unset the
        # Reset button is neither registered nor drawn, so the screen
        # degrades to its previous single-button form
        # (issue-4ab5ff88).
        self._reset_callback = None
        self._link_ok = False                # latch: data is confirmed flowing
        self._recovery_count = 0             # consecutive samples close enough together

        self._update_status = 'idle'        # checking|available|none|error|pending
        self._update_wheel = None
        self._update_version = None

        # RPM signal conditioning (change-4c038bed)
        self._rpm_display = 0.0          # EMA output — the displayed figure
        self._rpm_ema_tau = 0.150        # EMA time constant, seconds
        self._rpm_last_ts = None         # time.monotonic() of previous conditioning call
        self._active_band = 0            # sticky band index for hysteresis
        self._band_hysteresis = 75.0     # band transition margin, RPM
        self._frame_counter = 0          # monotonic frame counter, advanced in _display_loop

        # Touch-region registration is driven by a change in this key
        # rather than by the render path (display review §8.2,
        # recommendation 20).
        self._registered_view = None

        # Plain (SDL default) fonts keyed by size, used only by the
        # acknowledgement screen. Kept separate from FontManager, which
        # resolves Michroma for every size (change-bdac4f18).
        self._plain_font_cache = {}

        # Populated by _register_view_regions; read by the render
        # methods. None until the first registration pass.
        self._options_btn_clear = None
        self._options_btn_sim = None
        self._options_btn_debug = None
        self._options_btn_update = None
        self._update_btn_install = None
        self._update_btn_cancel = None
        self._disconnected_btn_setup = None
        self._disconnected_btn_reset = None
        self._ack_btn_dismiss = None
        self._confirm_btn_yes = None
        self._confirm_btn_no = None

        # Active palette. The panel's backlight cannot be dimmed in
        # software, so this is the only control over emitted light
        # at night (display review §7.9, recommendation 29).
        self._palette = DAY_PALETTE
        self._palette_notice_until = 0.0

        # Component initialization
        self._initialize_components()
        
        # Configuration
        self._load_config()

        # Performance monitor, built here rather than in
        # _initialize_components because it takes the frame rate in
        # its constructor and self.config does not exist until
        # _load_config has run. It was previously given a literal 60
        # for that reason, which made every dropped-frame figure
        # wrong at any other rate and reported a constant in the
        # startup line (issue-6a3b7c52).
        try:
            _fps = getattr(self.config, 'fps_limit', 0) or 0
            if _fps <= 0:
                _fps = DisplayConfig.fps_limit
            self.performance_monitor = PerformanceMonitor(target_fps=_fps)
            self.performance_monitor.start_monitoring()
        except Exception as e:
            self.logger.error(
                f'Performance monitor initialization failed: {e}',
                exc_info=True
            )

        # Legacy components
        self._initialize_legacy_components()
        
        # Display thread setup
        self.display_thread = threading.Thread(
            target=self._display_loop,
            name='DisplayManager',
            daemon=True
        )
        self.thread_manager.register_thread('display', self.display_thread)

    
    def _initialize_components(self) -> None:
        """Initialize the extracted components"""
        try:
            # Initialize rendering engine
            self.rendering_engine = DisplayRenderingEngine()
            if not self.rendering_engine.initialize((480, 480)):
                self.logger.error("Failed to initialize rendering engine")
                self.display_available = False
            else:
                self.display_available = True

            # Initialize touch coordinator
            self.touch_coordinator = TouchEventCoordinator((480, 480))
            self._setup_touch_callbacks()

            # Initialize acknowledgement state manager
            self._ack_state_manager = AcknowledgementStateManager()

            self.logger.info("Display components initialized successfully")

        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}", exc_info=True)
            self.display_available = False
    
    def _setup_touch_callbacks(self) -> None:
        """Setup touch gesture callbacks"""
        try:
            # Register gesture callbacks for navigation.
            # The two horizontal swipes moved between DIGITAL and RADIAL
            # and went with DIGITAL's retirement (change-378703da).
            #
            # OPTIONS is entered by a downward swipe and left by an
            # upward one. The long press that did both was a toggle
            # with no second route when one direction failed
            # (change-3e8b1d72). The coordinator already recognises
            # both gestures; only the callbacks were missing.
            self.touch_coordinator.register_gesture_callback(
                GestureType.SWIPE_DOWN, self._handle_swipe_down
            )
            self.touch_coordinator.register_gesture_callback(
                GestureType.SWIPE_UP, self._handle_swipe_up
            )

            # The palette toggle is NOT registered here. Gesture
            # callbacks registered with the coordinator are never
            # invoked: handle_touch_up and handle_touch_move, which
            # dispatch to them, are called by nothing
            # (issue-2b6f4d91). The registrations above are inert for
            # the same reason — the vertical swipes work because
            # TouchHandler calls the handlers directly at
            # touch.py:202-209, and the palette toggle is wired the
            # same way in TouchHandler._handle_long_press.

        except Exception as e:
            self.logger.error(f"Touch callback setup failed: {e}")
    
    def _toggle_palette(self) -> None:
        """Swap the active palette, notify, and persist the choice.

        A failed save leaves the palette as it was, so the display never
        shows a state the configuration does not describe.
        """
        try:
            self._palette = (
                NIGHT_PALETTE if self._palette is DAY_PALETTE
                else DAY_PALETTE
            )
            self._palette_notice_until = time.monotonic() + 2.0
            self._save_config()
            self.logger.info(
                f'Palette switched to {self._palette.name}'
            )
        except Exception as e:
            self.logger.error(
                f'Palette toggle error: {e}', exc_info=True
            )

    def _handle_long_press(self, start_pos: Tuple[int, int],
                           end_pos: Tuple[int, int]) -> TouchAction:
        """Toggle the day/night palette. Long press, RADIAL only.

        NOT the OPTIONS toggle. A method of this name existed on
        this class until change-3e8b1d72 moved OPTIONS to the
        vertical swipes and deleted it; a reader of the git history
        will otherwise assume it has returned. This is
        change-2b6f4d91's palette toggle, which took over the long
        press because that gesture was left unclaimed.

        Args:
            start_pos: Gesture start coordinates.
            end_pos: Gesture end coordinates. For a long press this
                is the same point as start_pos.

        Returns:
            SETTINGS_CHANGE when the palette was toggled, NONE
            otherwise.
        """
        try:
            if self._in_setup_mode:
                return TouchAction.NONE
            if self.config.mode != DisplayMode.RADIAL:
                return TouchAction.NONE
            self._toggle_palette()
            return TouchAction.SETTINGS_CHANGE
        except Exception as e:
            self.logger.error(f'Double tap handling error: {e}')
            return TouchAction.NONE

    def _handle_swipe_down(self, start_pos: Tuple[int, int],
                           end_pos: Tuple[int, int]) -> TouchAction:
        """Enter the OPTIONS screen.

        Paired with _handle_swipe_up. The long press that previously did
        both was a toggle, and when its leaving branch failed the
        operator had no second route (issue-3e8b1d72).

        The mode in use on entry is recorded so the exit returns there.
        The sub-view is reset so a confirmation abandoned by swipe is
        not waiting on the next entry (change-b02ed4ea), and the page
        with it, so OPTIONS always opens on page 0 rather than wherever
        the last visit left off (change-8c5a1e73).

        Args:
            start_pos: Gesture start coordinates.
            end_pos: Gesture end coordinates.

        Returns:
            NAVIGATION when OPTIONS was entered, NONE otherwise.
        """
        try:
            if self._in_setup_mode:
                self.logger.debug('Swipe down ignored: setup mode')
                return TouchAction.NONE
            if self.config.mode in (
                DisplayMode.OPTIONS,
                DisplayMode.SPLASH,
                DisplayMode.ACKNOWLEDGEMENT,
            ):
                self.logger.debug(
                    f'Swipe down ignored: mode {self.config.mode.name}'
                )
                return TouchAction.NONE
            self._pre_options_mode = self.config.mode
            self._options_view = 'menu'
            self._options_page = 0
            self.config.mode = DisplayMode.OPTIONS
            return TouchAction.NAVIGATION
        except Exception as e:
            self.logger.error(f'Swipe down handling error: {e}')
            return TouchAction.NONE

    def _handle_swipe_up(self, start_pos: Tuple[int, int],
                         end_pos: Tuple[int, int]) -> TouchAction:
        """Return to the screen OPTIONS was entered from.

        Restores the mode recorded by _handle_swipe_down rather than
        assuming RADIAL: OPTIONS is reachable from the DISCONNECTED
        condition, which is derived from the recorded mode and reasserts
        itself on return while the condition holds (change-3e8b1d72).

        Args:
            start_pos: Gesture start coordinates.
            end_pos: Gesture end coordinates.

        Returns:
            NAVIGATION when OPTIONS was left, NONE otherwise.
        """
        try:
            if self._in_setup_mode:
                self.logger.debug('Swipe up ignored: setup mode')
                return TouchAction.NONE
            if self.config.mode != DisplayMode.OPTIONS:
                self.logger.debug(
                    f'Swipe up ignored: mode {self.config.mode.name}'
                )
                return TouchAction.NONE
            self._options_view = 'menu'
            self.config.mode = (
                self._pre_options_mode or DisplayMode.RADIAL
            )
            self._pre_options_mode = None
            return TouchAction.NAVIGATION
        except Exception as e:
            self.logger.error(f'Swipe up handling error: {e}')
            return TouchAction.NONE

    def _handle_swipe_left(self, start_pos: Tuple[int, int],
                           end_pos: Tuple[int, int]) -> TouchAction:
        """Page forward through the options menu, wrapping.

        Args:
            start_pos: Gesture start coordinates.
            end_pos: Gesture end coordinates.

        Returns:
            NAVIGATION when the page changed, NONE otherwise.
        """
        return self._page_options(+1)

    def _handle_swipe_right(self, start_pos: Tuple[int, int],
                            end_pos: Tuple[int, int]) -> TouchAction:
        """Page back through the options menu, wrapping.

        Args:
            start_pos: Gesture start coordinates.
            end_pos: Gesture end coordinates.

        Returns:
            NAVIGATION when the page changed, NONE otherwise.
        """
        return self._page_options(-1)

    def _page_options(self, delta: int) -> TouchAction:
        """Move the options menu on by delta pages, wrapping both ways.

        Paging acts only on the options menu itself. The update and
        confirmation sub-views are single screens, and setup owns the
        display outright, so a horizontal swipe in any of them is
        ignored rather than silently changing a page underneath them.

        Args:
            delta: Pages to advance; negative to go back.

        Returns:
            NAVIGATION when the page changed, NONE otherwise.
        """
        try:
            if self._in_setup_mode:
                self.logger.debug('Options paging ignored: setup mode')
                return TouchAction.NONE
            if self.config.mode != DisplayMode.OPTIONS:
                self.logger.debug(
                    f'Options paging ignored: mode {self.config.mode.name}'
                )
                return TouchAction.NONE
            if self._options_view != 'menu':
                self.logger.debug(
                    f'Options paging ignored: sub-view {self._options_view}'
                )
                return TouchAction.NONE

            # Modulo gives the wrapping in both directions, and the
            # named count means a third page is a data change.
            self._options_page = (
                self._options_page + delta
            ) % self.OPTIONS_PAGE_COUNT
            self.logger.debug(f'Options page -> {self._options_page}')
            return TouchAction.NAVIGATION
        except Exception as e:
            self.logger.error(f'Options paging error: {e}')
            return TouchAction.NONE

    def _initialize_legacy_components(self) -> None:
        """Initialize legacy components for backward compatibility"""
        try:
            # Touch handler compatibility
            try:
                from .touch import TouchHandler
                from .touch_interface import create_touch_interface
                _touch_interface = create_touch_interface()
                _touch_interface.start()
                self.touch_handler = TouchHandler(self, touch_interface=_touch_interface)
            except ImportError as e:
                self.logger.warning(f"TouchHandler not available: {e}")
                self.touch_handler = None
            
            # Setup mode components
            self._setup_manager = None
            self._in_setup_mode = False
            self._setup_entry_callback = None

            # Initialize splash screen
            try:
                splash_config = getattr(self.config, 'splash', None)
                self._splash_screen = SplashScreen(surface_size=(480, 480), duration=4.0, config=splash_config)
                self.logger.info("Splash screen initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize splash screen: {e}")
                self._splash_screen = None
            
            # Navigation gesture handler
            try:
                from .navigation_gestures import NavigationGestureHandler, GestureConfig
                
                gesture_config = GestureConfig(
                    swipe_threshold=getattr(self.config, 'gesture_swipe_threshold', 50),
                    velocity_threshold=getattr(self.config, 'gesture_velocity_threshold', 100),
                    edge_width=getattr(self.config, 'gesture_edge_width', 30),
                    max_gesture_time=getattr(self.config, 'gesture_max_time', 2.0),
                    edge_indicator_timeout=getattr(self.config, 'gesture_edge_timeout', 3.0),
                    enable_main_navigation=getattr(self.config, 'gesture_enable_main', True),
                    enable_setup_navigation=getattr(self.config, 'gesture_enable_setup', True),
                    enable_settings_gestures=getattr(self.config, 'gesture_enable_settings', True),  # Note: kept for config compat
                    debug_mode=getattr(self.config, 'gesture_debug_mode', False)
                )
                
                self.gesture_handler = NavigationGestureHandler(self, gesture_config)
                self.logger.info("Navigation gesture handler initialized")
                
            except ImportError as e:
                self.logger.error(f"Failed to initialize gesture handler: {e}")
                self.gesture_handler = None
            
        except Exception as e:
            self.logger.error(f"Legacy component initialization failed: {e}")
    
    def _load_config(self) -> None:
        """Load display configuration"""
        try:
            if YAML_AVAILABLE and os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    saved_mode_str = config_data.get('mode', 'RADIAL')

                    # DIGITAL was retired in v0.4.0 (display review
                    # §7.5/§7.6, recommendation 25; ai/task.md §7.3.14).
                    # Every system upgrading from an earlier build has it
                    # persisted, so this is the expected case rather than
                    # an error. RADIAL now shows the numeric readout
                    # DIGITAL existed for. The migration is read-side
                    # only — the operator's file is not rewritten.
                    if saved_mode_str == 'DIGITAL':
                        self.logger.info(
                            "Display mode DIGITAL was retired; using RADIAL, "
                            "which now shows the numeric readout"
                        )
                        saved_mode_str = 'RADIAL'

                    # Try to parse saved mode with GAUGE fallback to RADIAL
                    try:
                        saved_mode = DisplayMode[saved_mode_str]
                        # Transient modes must not be used as post-splash target
                        _transient = (DisplayMode.SPLASH, DisplayMode.OPTIONS, DisplayMode.ACKNOWLEDGEMENT)
                        if saved_mode in _transient:
                            saved_mode = DisplayMode.RADIAL
                    except KeyError:
                        self.logger.warning(f"Unknown display mode '{saved_mode_str}', using RADIAL")
                        saved_mode = DisplayMode.RADIAL

                    # An absent key yields day through the default and
                    # warns nothing — that is every installation
                    # predating change-5012004e, not an error.
                    palette_name = config_data.get('palette', 'day')
                    if palette_name == 'night':
                        self._palette = NIGHT_PALETTE
                    elif palette_name == 'day':
                        self._palette = DAY_PALETTE
                    else:
                        self.logger.warning(
                            f"Unknown palette '{palette_name}', using day"
                        )
                        self._palette = DAY_PALETTE

                    engine_profile = config_data.get('engine_profile', 'abarth_595_turismo')

                    # Load engine profile RPM bands
                    from ..utils.config import load_engine_profile
                    rpm_bands = load_engine_profile(engine_profile)

                    self.config = DisplayConfig(
                        mode=DisplayMode.SPLASH,  # Always start with splash
                        rpm_warning=config_data.get('rpm_warning', 6500),
                        rpm_danger=config_data.get('rpm_danger', 7000),
                        fps_limit=config_data.get('fps_limit', 60),
                        touch_long_press=config_data.get('touch_long_press', 1.0),
                        engine_profile=engine_profile,
                        rpm_bands=rpm_bands
                    )
                    self._post_splash_mode = saved_mode
            else:
                if not YAML_AVAILABLE:
                    self.logger.info("YAML not available - using default configuration")

                # Load default engine profile
                try:
                    from ..utils.config import load_engine_profile
                    rpm_bands = load_engine_profile('abarth_595_turismo')
                except Exception as e:
                    self.logger.warning(f"Failed to load engine profile: {e}")
                    from .models import RPMBands
                    rpm_bands = RPMBands()

                self.config = DisplayConfig(
                    mode=DisplayMode.SPLASH,
                    rpm_bands=rpm_bands
                )
                self._post_splash_mode = DisplayMode.RADIAL
                if YAML_AVAILABLE:
                    self._save_config()

        except Exception as e:
            self.logger.error(f"Config load failed: {e}", exc_info=True)

            # Fallback to defaults
            try:
                from ..utils.config import load_engine_profile
                rpm_bands = load_engine_profile('abarth_595_turismo')
            except Exception:
                from .models import RPMBands
                rpm_bands = RPMBands()

            self.config = DisplayConfig(
                mode=DisplayMode.SPLASH,
                rpm_bands=rpm_bands
            )
            self._post_splash_mode = DisplayMode.RADIAL
    
    def _save_config(self) -> None:
        """Save current configuration.

        Never persists SPLASH as the display mode — saves _post_splash_mode
        instead so that the next startup transitions correctly to the last
        active mode rather than looping the splash screen.
        """
        if not YAML_AVAILABLE:
            self.logger.debug("YAML not available - configuration will not be persisted")
            return

        try:
            # Do not persist transient modes: SPLASH, OPTIONS, ACKNOWLEDGEMENT
            _transient = (DisplayMode.SPLASH, DisplayMode.OPTIONS, DisplayMode.ACKNOWLEDGEMENT)
            mode_to_save = (
                self._post_splash_mode
                if self.config.mode in _transient
                else self.config.mode
            )
            config_data = {
                'mode': mode_to_save.name,
                'rpm_warning': self.config.rpm_warning,
                'rpm_danger': self.config.rpm_danger,
                'fps_limit': self.config.fps_limit,
                'touch_long_press': self.config.touch_long_press,
                'engine_profile': self.config.engine_profile,
                'palette': self._palette.name,
            }
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f)

        except Exception as e:
            self.logger.error(f"Config save failed: {e}")
    
    def start(self) -> None:
        """Start display manager."""
        self.start_splash()
        self.display_thread.start()
        self.logger.info("Display manager started")

    def run_main_thread_loop(self) -> None:
        """Retained for API compatibility."""
        pass
    
    def start_splash(self) -> None:
        """Start the splash screen"""
        try:
            if self._splash_screen:
                self._splash_screen.start()
                self.config.mode = DisplayMode.SPLASH
                self.logger.info("Splash screen started")
            else:
                self.logger.warning("No splash screen available - skipping to normal mode")
                self._enter_post_splash_mode()
        except Exception as e:
            self.logger.error(f"Failed to start splash screen: {e}")
            self._enter_post_splash_mode()
    
    def stop(self) -> None:
        """Stop display manager"""
        self._shutdown_event.set()
        self.display_thread.join(timeout=5.0)
        if self.display_thread.is_alive():
            self.logger.warning("Display thread did not stop cleanly within timeout")

        # Clean up components
        try:
            self.performance_monitor.stop_monitoring()
            self.rendering_engine.cleanup()
            self.logger.info("Display manager stopped")
        except Exception as e:
            self.logger.error(f"Error stopping display manager: {e}", exc_info=True)
    
    def _display_loop(self) -> None:
        """Main display loop using component architecture"""
        if not PYGAME_AVAILABLE:
            self.logger.warning("Pygame not available - display loop disabled")
            return
        
        self.logger.info("Display loop started with component architecture")
        
        while not self._shutdown_event.is_set():
            try:
                _frame_start = time.monotonic()
                # No event handling. SDL_VIDEODRIVER is 'dummy' and
                # set_mode is never called, so no window exists and no
                # window events are generated — the previous poll loop
                # and its QUIT path were unreachable (display review
                # §8.4, recommendation 22). Shutdown is driven entirely
                # by _shutdown_event. Reinstating a real SDL video
                # driver would require reinstating event handling.

                # Register touch regions once per view rather than per
                # frame (recommendation 20).
                _view = self._current_view_key()
                if _view != self._registered_view:
                    try:
                        self._register_view_regions()
                        self._registered_view = _view
                    except Exception:
                        # Logged in _register_view_regions. Leave
                        # _registered_view unchanged so the next frame
                        # retries rather than rendering unregistered.
                        pass

                # Record frame start for performance monitoring
                frame_id = self.performance_monitor.record_frame_start()
                
                self.thread_manager.update_heartbeat('display')

                self._frame_counter += 1

                # Clear back buffer
                self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER)
                
                # Render current mode
                if self.config.mode == DisplayMode.SPLASH:
                    self._draw_splash_mode()
                elif self._in_setup_mode and self._setup_manager:
                    self._render_setup_mode()
                else:
                    self._render_normal_modes()
                
                # Swap buffers and write to framebuffer
                self.rendering_engine.swap_buffers()
                self.rendering_engine.write_to_framebuffer()
                
                # Close the frame BEFORE the pacing sleep so the recorded
                # interval measures render cost, not the loop period
                # (display review §6.2, recommendation 15).
                self.performance_monitor.record_frame_end(frame_id)

                # Frame pacing.
                # pygame.time.Clock.tick() uses SDL_Delay which can block
                # indefinitely on macOS when the Cocoa run loop stalls.
                # Use time.sleep() for reliable frame pacing on all platforms.
                _frame_end = time.monotonic()
                _frame_elapsed = _frame_end - _frame_start
                _frame_target = 1.0 / self.config.fps_limit
                _sleep = _frame_target - _frame_elapsed
                if _sleep > 0:
                    time.sleep(_sleep)

                # Periodic performance logging. The monitor owns the
                # cadence test, so no metrics object is constructed on
                # ordinary frames (recommendation 16).
                if self.performance_monitor.should_log_periodic():
                    metrics = self.performance_monitor.get_current_metrics()
                    self.logger.info(
                        f"Performance: {metrics.fps:.1f} FPS, "
                        f"{metrics.frame_time_ms:.1f}ms frame, "
                        f"{metrics.memory_usage_mb:.1f}MB mem"
                    )
                
            except Exception as e:
                self.logger.error(f"Display loop error: {e}", exc_info=True)
                time.sleep(0.1)
        
        self.logger.info("Display loop ended")
    
    def _draw_splash_mode(self) -> None:
        """Draw splash screen"""
        try:
            if not self._splash_screen:
                self._enter_post_splash_mode()
                return
            
            # Get back buffer surface for splash rendering
            back_surface = self.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)
            if back_surface:
                splash_success = self._splash_screen.render(back_surface)
                
                if self._splash_screen.is_complete():
                    self._enter_post_splash_mode()
                    self.logger.info(f"Splash completed - transitioning to {self.config.mode.name}")

                    self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER)
                    self.rendering_engine.swap_buffers()

                    try:
                        self._splash_screen.reset()
                    except Exception as e:
                        self.logger.error(f"Error resetting splash screen: {e}")
                        
        except Exception as e:
            self.logger.error(f"Splash mode error: {e}", exc_info=True)
            self._enter_post_splash_mode()

    def _enter_post_splash_mode(self) -> None:
        """Enter normal operation, gated on acknowledgement state.

        Called from start_splash(), _draw_splash_mode(), and
        exit_setup_mode() — every route out of a transient state
        (SPLASH or SETUP) into normal operation. When the current RPM
        bands and engine profile have not been acknowledged, sets
        DisplayMode.ACKNOWLEDGEMENT instead of self._post_splash_mode.

        Any failure of the acknowledgement check resolves toward showing
        the notice rather than skipping it. The sole exception is a
        missing state manager, which resolves to self._post_splash_mode
        because a dismissal could not be persisted without one.

        _on_acknowledgement_dismissed() is the only path back out of
        ACKNOWLEDGEMENT and is intentionally not gated.
        """
        try:
            ack_manager = getattr(self, '_ack_state_manager', None)
            if ack_manager is None:
                self.config.mode = self._post_splash_mode
                return

            if not ack_manager.is_acknowledged(
                self.config.rpm_bands,
                self.config.engine_profile
            ):
                self.config.mode = DisplayMode.ACKNOWLEDGEMENT
                return
        except Exception as e:
            self.logger.error(f"Acknowledgement state check failed: {e}", exc_info=True)
            self.config.mode = DisplayMode.ACKNOWLEDGEMENT
            return

        self.config.mode = self._post_splash_mode

    def _render_setup_mode(self) -> None:
        """Render setup mode using setup manager"""
        try:
            back_surface = self.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)
            if back_surface and self._setup_manager:
                self._setup_manager.render(back_surface)
        except Exception as e:
            self.logger.error(f"Setup mode render error: {e}")
            self._draw_setup_mode_fallback()
    
    def _drain_samples(self) -> None:
        """Consume queued RPM samples and record their arrival.

        Keeps only the latest value, to avoid display lag.

        CALLED FROM _render_normal_modes, BEFORE THE LINK TEST — not
        from _draw_radial_mode, where the drain used to live. The
        DISCONNECTED screen pre-empts the gauge, so draining only while
        the gauge is drawn would mean that once the link was declared
        lost no sample could ever be consumed, no arrival could ever be
        recorded, and the link could never recover: the instrument
        would sit on the DISCONNECTED screen until restart while the
        adapter delivered perfectly good data (issue-4d9e2f18).

        Returns immediately in simulation mode, so no synthetic value
        is ever mistaken for evidence of an adapter.
        """
        if self._sim_mode:
            return
        try:
            while True:
                rpm_data = self.thread_manager.message_queue.get_nowait()
                self._last_rpm = (
                    (256 * rpm_data.data[0]) + rpm_data.data[1]
                ) / 4
                self._note_sample()
        except queue.Empty:
            pass
        except Exception as e:
            self.logger.debug(f'Queue drain error: {e}')

    def _note_sample(self) -> None:
        """Record the arrival of one real sample from the adapter.

        Called for every message drained from the queue, and never for a
        synthetic value: a simulated RPM is not evidence that an adapter
        exists (issue-4d9e2f18).

        Recovery deliberately requires LINK_RECOVERY_SAMPLES samples
        arriving within LINK_LOSS_TIMEOUT of one another rather than a
        single sample. A link delivering one sample every few seconds
        would otherwise alternate between the gauge and the DISCONNECTED
        screen once per sample, which is worse than either state.
        """
        now = time.monotonic()
        if (self._last_sample_ts is not None
                and now - self._last_sample_ts <= self.LINK_LOSS_TIMEOUT):
            self._recovery_count += 1
        else:
            # A gap longer than the timeout is itself a loss condition,
            # so the latch is dropped here and not left to _link_lost to
            # notice. This method refreshes _last_sample_ts below, which
            # would otherwise hide the gap from the staleness test: a
            # link delivering one sample every few seconds would then
            # read as up. _link_lost does clear the latch during the gap
            # when it is polled each frame, but the guarantee should not
            # depend on the render cadence.
            self._recovery_count = 1
            self._link_ok = False
        self._last_sample_ts = now
        if self._recovery_count >= self.LINK_RECOVERY_SAMPLES:
            if not self._link_ok:
                self.logger.info('Link restored')
            self._link_ok = True

    def _link_lost(self) -> bool:
        """Whether the adapter has stopped delivering data.

        Two signals, because neither alone suffices. The transport's own
        view catches a clean disconnect at once. Staleness catches an
        adapter that vanishes without closing its socket — a flat
        battery — which is the failure this method exists for and the
        one the previous thread-status proxy could never see: the
        obd_protocol thread stays RUNNING while its transport retries
        indefinitely, so that proxy reported a live connection whenever
        the software was running (issue-4d9e2f18).

        EVERY FAILURE PATH RETURNS True. The asymmetry is the safety
        property of this method. A false 'disconnected' costs the
        operator a screen they can leave in one swipe; a false
        'connected' puts a stale needle and a green light in front of a
        driver. An absent or raising callback therefore means 'socket
        state unavailable', never 'connected'.

        Called from the render path at 30 Hz, so it stays cheap and logs
        only on a transition.

        Returns:
            True when the link is lost or its state cannot be
            established; False only while data is confirmed flowing, or
            in simulation mode.
        """
        try:
            # FIRST, and unconditionally. Simulation is a display
            # without an adapter; that is its purpose, so it must never
            # report a lost link.
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
                    self.logger.info('Link lost — no data for %.1fs', age)
                self._link_ok = False
                self._recovery_count = 0
                return True

            return not self._link_ok

        except Exception as e:
            self.logger.error(f'Link state error: {e}', exc_info=True)
            return True

    def _render_normal_modes(self) -> None:
        """Render normal display modes"""
        try:
            # Consume samples first, whatever is about to be drawn.
            # This is what lets a lost link recover: the drain is the
            # only place an arrival is recorded, and the gauge that
            # used to host it is exactly what stops being drawn when
            # the link is declared lost (issue-4d9e2f18).
            self._drain_samples()

            # Link state, not thread liveness. The obd_protocol thread
            # stays RUNNING while its transport retries indefinitely,
            # so the old test reported a live connection whenever the
            # software was running (issue-4d9e2f18). _link_lost is
            # already False in simulation mode, so the _sim_mode clause
            # is subsumed rather than duplicated.
            #
            # RADIAL only. The DISCONNECTED screen replaces the GAUGE,
            # which is the thing a lost link falsifies — not the
            # settings screens. Ungated, this would make OPTIONS
            # unreachable exactly when the adapter is down, which is
            # when Simulate and Clear settings are most wanted. The old
            # test could never fire, so it never needed the gate; this
            # one fires routinely.
            if self._link_lost() and self.config.mode == DisplayMode.RADIAL:
                self._render_disconnected()
                return

            if self.config.mode == DisplayMode.RADIAL:
                self._draw_radial_mode()
            elif self.config.mode == DisplayMode.OPTIONS:
                self._draw_options_mode()
            elif self.config.mode == DisplayMode.ACKNOWLEDGEMENT:
                self._draw_acknowledgement_mode()
            # Always draw status indicator
            self._draw_status_indicator()

        except Exception as e:
            self.logger.error(f"Normal mode render error: {e}")

    def _condition_rpm(self, raw: float) -> float:
        """Smooth the raw RPM sample for display.

        Applies a first-order exponential moving average with the time
        constant self._rpm_ema_tau, computed against the measured interval
        since the previous call so the time constant holds regardless of
        frame rate. The raw value is not modified; self._last_rpm continues
        to hold it.

        Args:
            raw: Raw RPM sample as drained from the OBD message queue.

        Returns:
            Smoothed RPM for display consumers. Returns raw unchanged if
            conditioning fails.
        """
        try:
            now = time.monotonic()
            if self._rpm_last_ts is None:
                self._rpm_last_ts = now
                self._rpm_display = float(raw)
                return self._rpm_display

            dt = now - self._rpm_last_ts
            dt = min(0.5, max(0.001, dt))
            self._rpm_last_ts = now

            alpha = 1.0 - math.exp(-dt / self._rpm_ema_tau)
            self._rpm_display += alpha * (float(raw) - self._rpm_display)
            return self._rpm_display

        except Exception as e:
            self.logger.error(f'RPM conditioning error: {e}', exc_info=True)
            return raw

    # RETAINED DELIBERATELY. This method has no caller after DIGITAL's
    # retirement (change-378703da) and a dead-code analysis will
    # correctly report it as unreachable. It is kept because task 7.3.11
    # (change-5014040c, the annular band indicator) requires exactly this
    # band selection, including the hysteresis added by change-4c038bed.
    # Do not remove it before that change lands.
    def _get_band_colour(self, rpm: float) -> Tuple[int, Tuple[int, int, int]]:
        """Get the active band index and its colour for the given RPM.

        Owns the band identity for the whole gauge. The hysteresis below
        is change-4c038bed's contribution; routing the fill arc through
        this method (change-5014040c) applies it to the arc for the
        first time, so a value oscillating about a threshold no longer
        flips the leading segment's colour.

        Args:
            rpm: Current RPM value

        Returns:
            Tuple of (band index, RGB colour) for the active band.
        """
        try:
            bands = self.config.rpm_bands

            # The text-colour column that stood beside these was
            # consumed only by _draw_digital_mode, which
            # change-378703da removed; the RADIAL readout is
            # unconditionally white, so the pairing has no remaining
            # consumer (ai/task.md §7.3.14).
            palette = self._palette.bands

            # Ascending thresholds; threshold[i] separates band i from i+1.
            thresholds = (
                bands.idle_max,
                bands.torque_start,
                bands.caution_start,
                bands.warning_start,
                bands.danger_start,
            )

            # Clamp the hysteresis margin below half the narrowest gap so
            # a closely spaced RPMBands cannot make a band unreachable.
            gaps = [
                thresholds[i + 1] - thresholds[i]
                for i in range(len(thresholds) - 1)
            ]
            narrowest = min(gaps) if gaps else self._band_hysteresis
            margin = min(self._band_hysteresis, 0.49 * narrowest)

            # Sticky selection: at most one step per call, and only when
            # the value clears the threshold by the margin in the
            # direction of travel.
            band = self._active_band
            if band < len(thresholds) and rpm > thresholds[band] + margin:
                band += 1
            elif band > 0 and rpm < thresholds[band - 1] - margin:
                band -= 1

            self._active_band = band

            return (band, palette[band])

        except Exception as e:
            self.logger.error(f'Band colour calculation error: {e}', exc_info=True)
            # Fallback to band 0, black
            return (0, (0, 0, 0))

    def _draw_radial_mode(self) -> None:
        """Draw radial arc RPM display using rendering engine"""
        try:
            # Use synthetic RPM in simulation mode
            if self._sim_mode:
                rpm = int(3000 + 3000 * math.sin(time.time()))
                self._last_rpm = rpm
                rpm = self._condition_rpm(rpm)
            else:
                # The queue is drained by _drain_samples, called from
                # _render_normal_modes before the link test rather than
                # here. See that method for why.
                rpm = self._condition_rpm(getattr(self, '_last_rpm', 0))
            # Clamp RPM to valid range
            rpm = max(0, min(7000, rpm))

            # Get back buffer surface
            surface = self.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)
            if not surface:
                return

            # Read the palette ONCE per frame. A toggle landing between
            # two drawing calls would otherwise render half the frame in
            # each palette (change-5012004e).
            palette = self._palette

            # One lookup each per frame. _get_band_colour's sticky
            # selection advances at most one band per call, so a second
            # call would halve the effective hysteresis — which now
            # governs the whole sweep and the centre disc, not one
            # segment (change-64d8d8fc).
            active_band, band_colour = self._get_band_colour(rpm)
            # The centre disc carries what the engine IS DOING. The
            # shift cue that used to colour the rim, and flash this disc
            # against it, went with the rim (issue-950128c0), so the
            # band colour is now read directly and unconditionally.
            centre_colour = palette.band_centres[active_band]

            # Arc geometry constants. The arcs stop at r=232, where
            # they used to butt against the inner edge of the 12 px
            # rim; the rim is gone (issue-950128c0) but the arc
            # geometry is deliberately unchanged, so the sweep is
            # exactly as before. border_radius was read only by the
            # removed border and is gone with it.
            center = (240, 240)
            outer_radius = 232
            inner_radius = 100
            max_rpm = 7000

            # Angle conversion: clock degrees to canvas radians
            # Active arc: 210 deg (7 o'clock) to 150 deg (5 o'clock) via top = 300 deg sweep
            start_clock_deg = 210
            end_clock_deg = 150
            active_sweep_deg = 300

            def clock_to_canvas_rad(clock_deg):
                """Convert clock angle to canvas radians"""
                return math.radians(clock_deg - 90)

            def rpm_to_angle_rad(rpm_val):
                """Convert RPM to canvas angle in radians"""
                clock_deg = start_clock_deg + (rpm_val / max_rpm) * active_sweep_deg
                return clock_to_canvas_rad(clock_deg)

            def draw_donut_arc(color, start_angle_rad, end_angle_rad):
                """Draw a donut arc segment using polygon approximation"""
                num_points = 60
                angle_step = (end_angle_rad - start_angle_rad) / num_points

                points = []
                # Outer arc points
                for i in range(num_points + 1):
                    angle = start_angle_rad + i * angle_step
                    x = center[0] + outer_radius * math.cos(angle)
                    y = center[1] + outer_radius * math.sin(angle)
                    points.append((x, y))

                # Inner arc points (reverse order)
                for i in range(num_points, -1, -1):
                    angle = start_angle_rad + i * angle_step
                    x = center[0] + inner_radius * math.cos(angle)
                    y = center[1] + inner_radius * math.sin(angle)
                    points.append((x, y))

                if len(points) > 2:
                    pygame.draw.polygon(surface, color, points)

            # 1. Fill corners black (outside circular viewport), then
            #    fill the whole circular face at r=244. The face stopped
            #    at r=232 while a 12 px rim occupied the space out to
            #    r=244; with the rim removed it extends to fill that
            #    space, so no unpainted ring is left (issue-950128c0).
            surface.fill((0, 0, 0))
            pygame.draw.circle(surface, palette.ground, center, 244)

            # 2. Draw headroom arc (full active zone, unfilled track)
            start_angle_rad = clock_to_canvas_rad(start_clock_deg)
            end_angle_rad = clock_to_canvas_rad(start_clock_deg + active_sweep_deg)
            draw_donut_arc(palette.track, start_angle_rad, end_angle_rad)

            # 3. Draw inert bottom arc (5 o'clock to 7 o'clock, 60 deg, track)
            # 5 o'clock = 150 deg, 7 o'clock = 210 deg, short path clockwise
            inert_start_rad = clock_to_canvas_rad(150)
            inert_end_rad = clock_to_canvas_rad(210)
            draw_donut_arc(palette.track, inert_start_rad, inert_end_rad)

            # 4. Draw the filled sweep in the active band's colour.
            #    One colour, not six: reading the zone from a graduated
            #    arc means localising the sweep's leading edge and then
            #    judging which band it falls in, and both stages degrade
            #    in peripheral vision. A uniform sweep makes it a single
            #    colour judgement. The headroom cue the graduation
            #    carried moves to the bolded boundary marks at step 9
            #    (change-64d8d8fc; withdraws prompt-5014040c's
            #    graduated-arc constraint).
            bands = self.config.rpm_bands
            if rpm > 0:
                draw_donut_arc(
                    band_colour,
                    rpm_to_angle_rad(0),
                    rpm_to_angle_rad(rpm),
                )

            # 5. Draw zone boundary lines at 5 o'clock and 7 o'clock
            for boundary_deg in [150, 210]:
                angle_rad = clock_to_canvas_rad(boundary_deg)
                inner_x = center[0] + inner_radius * math.cos(angle_rad)
                inner_y = center[1] + inner_radius * math.sin(angle_rad)
                outer_x = center[0] + outer_radius * math.cos(angle_rad)
                outer_y = center[1] + outer_radius * math.sin(angle_rad)
                pygame.draw.line(surface, palette.line, (inner_x, inner_y), (outer_x, outer_y), 2)

            # 6. Draw inner arc edge ring (subtle dark stroke)
            pygame.draw.circle(surface, palette.edge, center, inner_radius, 2)

            # 7. Draw major tick marks and numerals (1000-7000 RPM)
            tick_font = self._get_cached_font(52)
            for rpm_tick in range(1000, 8000, 1000):
                if rpm_tick <= max_rpm:
                    angle_rad = rpm_to_angle_rad(rpm_tick)
                    # Tick mark - 28px long radial line on outer edge
                    tick_start_x = center[0] + (outer_radius - 28) * math.cos(angle_rad)
                    tick_start_y = center[1] + (outer_radius - 28) * math.sin(angle_rad)
                    tick_end_x = center[0] + outer_radius * math.cos(angle_rad)
                    tick_end_y = center[1] + outer_radius * math.sin(angle_rad)
                    pygame.draw.line(surface, palette.tick,
                                   (tick_start_x, tick_start_y), (tick_end_x, tick_end_y), 7)

                    # Numeral - positioned 58px inward from outer radius
                    if tick_font:
                        numeral = str(rpm_tick // 1000)
                        num_x = center[0] + (outer_radius - 58) * math.cos(angle_rad)
                        num_y = center[1] + (outer_radius - 58) * math.sin(angle_rad)
                        self.rendering_engine.render_text(
                            RenderTarget.BACK_BUFFER, numeral, tick_font, palette.tick,
                            (int(num_x), int(num_y)), center=True
                        )

            # 8. Draw band boundary marks at thresholds.
            #    7 px, matching the major ticks: with the sweep drawn in
            #    one colour these marks carry the whole of the
            #    anticipatory cue — where the next zone begins — and are
            #    distinguished from the major ticks by colour, not
            #    weight (change-64d8d8fc).
            # Each mark takes the colour of the band it opens, read from
            # the active palette rather than restated (change-5012004e).
            boundary_colors = [
                (bands.idle_max, palette.bands[1]),       # Blue
                (bands.torque_start, palette.bands[2]),   # Green
                (bands.caution_start, palette.bands[3]),  # Yellow
                (bands.warning_start, palette.bands[4]),  # Orange
                (bands.danger_start, palette.bands[5]),   # Red
                (bands.redline_rpm, palette.bands[5])     # Red
            ]

            for threshold_rpm, color in boundary_colors:
                if 0 < threshold_rpm <= max_rpm:
                    angle_rad = rpm_to_angle_rad(threshold_rpm)
                    # 28px long colored radial line
                    mark_start_x = center[0] + (outer_radius - 28) * math.cos(angle_rad)
                    mark_start_y = center[1] + (outer_radius - 28) * math.sin(angle_rad)
                    mark_end_x = center[0] + outer_radius * math.cos(angle_rad)
                    mark_end_y = center[1] + outer_radius * math.sin(angle_rad)
                    pygame.draw.line(surface, color,
                                   (mark_start_x, mark_start_y), (mark_end_x, mark_end_y), 7)

            # 9. Draw white indicator line at current RPM
            if rpm > 0:
                current_angle_rad = rpm_to_angle_rad(rpm)
                ind_inner_x = center[0] + inner_radius * math.cos(current_angle_rad)
                ind_inner_y = center[1] + inner_radius * math.sin(current_angle_rad)
                ind_outer_x = center[0] + outer_radius * math.cos(current_angle_rad)
                ind_outer_y = center[1] + outer_radius * math.sin(current_angle_rad)
                pygame.draw.line(surface, (255, 255, 255),
                               (ind_inner_x, ind_inner_y), (ind_outer_x, ind_outer_y), 3)

            # 10. Draw 'RPM x 1000' label in inert arc
            label_font = self._get_cached_font(16)
            if label_font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, "RPM \u00d7 1000", label_font, palette.label,
                    (240, 420), center=True
                )

            # 11-13. Draw centre circle in the active band's colour.
            #    centre_colour is resolved once at the top of the method
            #    from palette.band_centres (change-64d8d8fc,
            #    issue-950128c0).
            center_radius = 99
            pygame.draw.circle(surface, centre_colour, center, center_radius)

            # The numeric readout. The centre disc is the largest
            # uninterrupted region of the gauge and the point of highest
            # visual acuity for a centred gaze; it previously carried a
            # fixed brand string while the number the instrument exists
            # to show appeared only in DIGITAL (display review §7.5,
            # recommendation 25). White reads on every band centre
            # fill.
            #
            # 72 px, not FONT_RPM_LARGE's 180: the disc is r=99, which
            # admits a 198 px chord, and three glyphs at 72 px measure
            # roughly 120 x 72. The RPM is clamped to 7000 above, so the
            # string is never wider than three glyphs.
            readout_font = self._get_cached_font(72)
            if readout_font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, f"{rpm/1000:.1f}",
                    readout_font, (255, 255, 255), center, center=True
                )

            # Transient confirmation that the palette changed. Two
            # seconds is long enough to read and short enough not to
            # become part of the instrument (change-5012004e).
            if time.monotonic() < self._palette_notice_until:
                notice_font = self._get_cached_font(24)
                if notice_font:
                    self.rendering_engine.render_text(
                        RenderTarget.BACK_BUFFER,
                        'Night' if palette is NIGHT_PALETTE else 'Day',
                        notice_font, palette.tick, (240, 330),
                        center=True
                    )

            # The f-string is formatted before the call, so at 60 Hz
            # the cost was paid whether or not DEBUG was enabled —
            # and production configures a NullHandler
            # (display review §5.6, recommendation 14).
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f'Radial mode: RPM={rpm:.0f}')

        except Exception as e:
            self.logger.error(f"Radial display error: {e}", exc_info=True)
    
    def _draw_options_mode(self) -> None:
        """Draw options interface — menu, update or confirm sub-view."""
        try:
            if self._options_view == 'update':
                self._draw_update_view()
            elif self._options_view == 'confirm_clear':
                self._draw_confirm_view()
            else:
                self._draw_options_menu()
        except Exception as e:
            self.logger.error(f"Options display error: {e}")

    def _current_view_key(self) -> tuple:
        """Identify the view whose touch regions should be registered.

        Every piece of state a render method branches on when deciding
        which controls exist MUST appear here.

          - _update_status: _draw_update_view branches on it, and a
            worker thread writes it in _run_update_check. Omitting it
            would leave stale regions after an asynchronous change.
          - _options_view: selects menu or update sub-view.
          - disconnected: DISCONNECTED is NOT a DisplayMode. It is a
            derived condition — _render_normal_modes shows that screen
            in place of the gauge when _link_lost() (issue-4d9e2f18;
            it previously asked the obd_protocol thread's status, which
            never changed). Omitting it would mean the Setup and
            Simulate buttons were never registered when the link drops.
            The mode gate _render_normal_modes applies is not repeated
            here: config.mode is already a member, so no registration
            decision can change without this key changing.
          - _in_setup_mode: the setup subsystem owns its own regions.
            It is in the key so that leaving setup re-registers the
            normal view.
          - _options_page: the menu pages its controls, so the page
            is part of what determines which regions exist. Omitting
            it would register one page's regions and draw the
            other's.

        Returns:
            (mode, options sub-view, update status, disconnected,
            in setup mode, options page).
        """
        disconnected = self._link_lost()
        return (
            self.config.mode,
            self._options_view,
            self._update_status,
            disconnected,
            self._in_setup_mode,
            self._options_page,
        )

    def _register_view_regions(self) -> None:
        """Clear and register the touch regions for the current view.

        Called once when the view key changes, not per frame. The
        previous arrangement cleared and rebuilt the region map from
        inside the render path at 60 Hz; a touch acquiring the
        coordinator's lock in that window observed an empty or partial
        map and was discarded (display review §8.2).

        Also computes the button rectangles and stores them on self,
        so the render methods draw from the same geometry that was
        registered.
        """
        try:
            # The setup subsystem registers and owns its own regions.
            # Clearing here would destroy them.
            if self._in_setup_mode and self._setup_manager:
                return

            self.touch_coordinator.clear_regions()

            if self.config.mode == DisplayMode.SPLASH:
                return  # no controls

            # DISCONNECTED is a derived condition, not a DisplayMode,
            # and _render_normal_modes gives it precedence over the
            # mode. The dispatch must mirror that order exactly — so
            # this asks _link_lost, exactly as that method now does
            # (issue-4d9e2f18). Left on thread status it would register
            # the gauge's regions, which are none, while the
            # DISCONNECTED screen was drawn: Setup and Simulate would
            # be visible and dead, and that screen is the operator's
            # only route out of a lost link.
            disconnected = (
                self._link_lost() and self.config.mode == DisplayMode.RADIAL
            )
            if disconnected:
                self._register_disconnected_regions()
                return

            if self.config.mode == DisplayMode.OPTIONS:
                if self._options_view == 'update':
                    self._register_update_view_regions()
                elif self._options_view == 'confirm_clear':
                    self._register_confirm_view_regions()
                else:
                    self._register_options_menu_regions()
            elif self.config.mode == DisplayMode.ACKNOWLEDGEMENT:
                self._register_acknowledgement_regions()
            # RADIAL registers nothing.

        except Exception as e:
            self.logger.error(f"Touch region registration error: {e}", exc_info=True)
            raise

    def _button_column(
        self,
        specs: Sequence[Tuple[str, TouchAction, Callable]],
        width: int,
        top: int,
        height: Optional[int] = None,
        separation: Optional[int] = None,
    ) -> List[pygame.Rect]:
        """Compute, validate and register a centred vertical stack of buttons.

        One owner for button geometry. The register methods call this;
        the render methods call _draw_button with what it returns. A
        single helper doing both would put touch registration back into
        the render path, which change-44bca479 removed
        (display review §8.2, recommendation 20).

        The returned rects are the VISUAL ones. The rects actually
        registered with the touch coordinator are larger — each is
        inflated by BUTTON_TOUCH_EXPANSION on every side, so the
        registered rect is 2 * BUTTON_TOUCH_EXPANSION wider and taller
        than the button that was designed. Drawing a registered rect
        would therefore draw a control 16 px larger than intended;
        draw the returned rect instead.

        Args:
            specs: (region_id, action, callback) per button, top to bottom.
            width: Button width in pixels.
            top: y of the first button's top edge.
            height: Button height. Defaults to BUTTON_MIN_TOUCH_HEIGHT
                and is clamped up to it.
            separation: Vertical gap between buttons. Defaults to and is
                clamped up to max(BUTTON_MIN_SEPARATION,
                2 * BUTTON_TOUCH_EXPANSION), so adjacent registered
                rects touch but never overlap.

        Returns:
            The visual rects, in the order given. Empty if specs is empty.
        """
        expansion = TypographyConstants.BUTTON_TOUCH_EXPANSION
        min_height = TypographyConstants.BUTTON_MIN_TOUCH_HEIGHT
        min_separation = max(
            TypographyConstants.BUTTON_MIN_SEPARATION, 2 * expansion
        )

        if height is None:
            height = min_height
        elif height < min_height:
            self.logger.warning(
                f"Button height {height} below the {min_height} px minimum; "
                f"using {min_height}"
            )
            height = min_height

        if separation is None:
            separation = min_separation
        elif separation < min_separation:
            self.logger.warning(
                f"Button separation {separation} below the {min_separation} px "
                f"minimum; using {min_separation}"
            )
            separation = min_separation

        radius_sq = TypographyConstants.VIEWPORT_RADIUS ** 2
        rects: List[pygame.Rect] = []

        for index, (region_id, action, callback) in enumerate(specs):
            rect = pygame.Rect(
                240 - width // 2,
                top + index * (height + separation),
                width,
                height,
            )

            # A control outside the circular viewport is invisible but
            # still touch-sensitive. That is the failure mode of
            # display review §8.1, which went unnoticed until a review
            # found it, so it is logged at ERROR where it will be seen.
            # It is not raised: a layout fault must not crash the
            # instrument on a moving vehicle.
            for corner_x, corner_y in (
                rect.topleft, rect.topright, rect.bottomleft, rect.bottomright
            ):
                if (corner_x - 240) ** 2 + (corner_y - 240) ** 2 > radius_sq:
                    self.logger.error(
                        f"Button {region_id} falls outside the circular "
                        f"viewport: {rect}"
                    )
                    break

            self.touch_coordinator.register_button_region(
                region_id,
                rect.inflate(expansion * 2, expansion * 2),
                action,
                callback,
            )
            rects.append(rect)

        return rects

    def _register_options_menu_regions(self) -> None:
        """Compute and register the current options page's two button regions.

        The menu holds four controls and the circular viewport admits
        three targets at the 72 px ergonomic minimum, so the controls
        are paged two at a time (change-8c5a1e73):

          page 0 — simulation_mode, debug_toggle
          page 1 — clear_settings, check_updates

        clear_settings binds _on_clear_settings_requested, which enters
        the confirmation sub-view. It never binds _on_clear_settings:
        a control that erases the paired device must not be reachable
        in one tap (display review §7.3, recommendation 24).

        _options_page is a member of _current_view_key, so this method
        re-runs whenever the page changes and the registered regions
        cannot disagree with the drawn page.
        """
        # Every rect explicitly None first, so a reference to a control
        # on the other page is a visible None rather than a stale rect
        # from the page previously registered.
        self._options_btn_clear = None
        self._options_btn_sim = None
        self._options_btn_debug = None
        self._options_btn_update = None

        if self._options_page == 0:
            specs = (
                ("simulation_mode", TouchAction.SETTINGS_CHANGE,
                 lambda pos: self._on_simulation_mode()),
                ("debug_toggle", TouchAction.SETTINGS_CHANGE,
                 lambda pos: self._on_debug_toggle()),
            )
        else:
            specs = (
                ("clear_settings", TouchAction.SETTINGS_CHANGE,
                 lambda pos: self._on_clear_settings_requested()),
                ("check_updates", TouchAction.SETTINGS_CHANGE,
                 lambda pos: self._on_check_updates()),
            )

        # Two 72 px targets separated by 16 px span y 185 to 345,
        # inside the 55-425 band a 300 px width leaves on the r=238
        # viewport, and clear of the indicator at y 395. The column sits
        # 45 px lower than it did so the title clears the status
        # indicator (change-61c7ba7f).
        rects = self._button_column(specs, width=300, top=185)

        if self._options_page == 0:
            self._options_btn_sim, self._options_btn_debug = rects
        else:
            self._options_btn_clear, self._options_btn_update = rects

    def _register_confirm_view_regions(self) -> None:
        """Compute and register the clear-settings confirmation's two regions.

        Sited at y 250 so the consequence text above it is read before
        either control is reachable.
        """
        rects = self._button_column(
            (
                ("confirm_clear_yes", TouchAction.SETTINGS_CHANGE,
                 lambda pos: self._on_clear_settings()),
                ("confirm_clear_no", TouchAction.SETTINGS_CHANGE,
                 lambda pos: self._on_cancel_clear()),
            ),
            width=300,
            top=250,
        )
        self._confirm_btn_yes, self._confirm_btn_no = rects

    def _register_update_view_regions(self) -> None:
        """Compute and register the update sub-view's regions.

        Which controls exist depends on _update_status: install and cancel
        when an update is available, a single back button when the check
        finished with nothing or failed, and none at all while a check is
        in flight. Rects for controls this status does not present are
        cleared, so a render guard cannot draw a button that was never
        registered.
        """
        # Both cleared first: _draw_update_view guards on them, so a
        # status that does not present a control must not leave the
        # previous status' rect behind.
        self._update_btn_install = None
        self._update_btn_cancel = None

        if self._update_status == 'available':
            self._update_btn_install, self._update_btn_cancel = self._button_column(
                (
                    ("update_install", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_confirm_install()),
                    ("update_cancel", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_cancel_update()),
                ),
                width=280,
                top=240,
            )
        elif self._update_status in ('none', 'error'):
            (self._update_btn_cancel,) = self._button_column(
                (
                    ("update_back", TouchAction.SETTINGS_CHANGE,
                     lambda pos: self._on_cancel_update()),
                ),
                width=280,
                top=300,
            )

    def _register_acknowledgement_regions(self) -> None:
        """Register the full-screen tap region that dismisses the notice."""
        self._ack_btn_dismiss = pygame.Rect(0, 0, 480, 480)
        self.touch_coordinator.register_button_region(
            "acknowledgement_dismiss",
            self._ack_btn_dismiss,
            TouchAction.NAVIGATION,
            lambda pos: self._on_acknowledgement_dismissed()
        )

    def _register_disconnected_regions(self) -> None:
        """Compute and register the DISCONNECTED screen's one region.

        One control, Setup. Simulate was removed from here because it
        duplicates OPTIONS page 0's simulation_mode control, which is
        one downward swipe away and remains its home (issue-4f1e82b7).

        Height rises from 70 to the 72 px minimum and separation from
        20 to the 16 px floor, so the column now spans y 240 to 400
        rather than 240 to 400 — the same band, because a 240 px wide
        control has a wider usable band inside the r=238 viewport than
        the 300 px options column does.

        width and top are unchanged, and _button_column stacks
        downward from an explicit top, so the Setup button occupies
        exactly the rect it did when it was first of two.

        The slot change-4f1e82b7 left free now holds Reset, which
        reboots the Pi, registered only when its callback is set so the
        screen degrades to the single-button form without it
        (issue-4ab5ff88).

        _button_column stacks downward from an explicit top, so the
        Setup rect is identical whether one or two controls are
        registered.
        """
        specs = [
            ("disconnected_setup", TouchAction.NAVIGATION,
             lambda pos: self._enter_setup_from_disconnected()),
        ]
        if self._reset_callback is not None:
            specs.append(
                ("disconnected_reset", TouchAction.NAVIGATION,
                 lambda pos: self._reset_callback())
            )

        rects = self._button_column(specs, width=240, top=240)

        self._disconnected_btn_setup = rects[0]
        self._disconnected_btn_reset = rects[1] if len(rects) > 1 else None

    def _draw_button(
        self,
        rect: pygame.Rect,
        label: str,
        fill: Tuple[int, int, int],
        font,
        text_colour: Tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        """Draw one button in the style TypographyConstants declares.

        The corner radius and border width were declared by
        TypographyConstants but applied nowhere; every button in the
        main UI was a bare filled rectangle
        (display review §7.3, recommendation 27).

        BUTTON_PRESS_SCALE is deliberately not applied. No pressed
        state is tracked anywhere in DisplayManager, and adding one is
        outside this change.

        Args:
            rect: The VISUAL rect, as returned by _button_column. Not
                the larger registered rect.
            label: Text centred on the rect.
            fill: Interior colour.
            font: Font for the label; nothing is drawn if None.
            text_colour: Label colour.
        """
        surface = self.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)
        if surface is None:
            return

        radius = TypographyConstants.BUTTON_CORNER_RADIUS
        pygame.draw.rect(surface, fill, rect, border_radius=radius)
        pygame.draw.rect(
            surface, (140, 140, 160), rect,
            TypographyConstants.BUTTON_BORDER_WIDTH,
            border_radius=radius,
        )

        if font:
            self.rendering_engine.render_text(
                RenderTarget.BACK_BUFFER, label, font, text_colour,
                rect.center, center=True
            )

    def _draw_options_menu(self) -> None:
        """Draw the current options page and the page indicator.

        Two tappable items per page, paged by horizontal swipe
        (change-8c5a1e73). Clear settings is on page 1 and opens the
        'confirm_clear' sub-view rather than acting (change-b02ed4ea).

        The indicator is drawn only. It is not registered, so it
        consumes none of the screen's touch-target budget — the
        discoverability answer display review §7.6 asked for, at no
        ergonomic cost.
        """
        self.rendering_engine.clear_surface(
            RenderTarget.BACK_BUFFER, self._DISCONNECTED_BG_COLOUR
        )

        font = get_title_display_font()
        if font:
            self.rendering_engine.render_text(
                RenderTarget.BACK_BUFFER, "Options", font,
                self._DISCONNECTED_TEXT_COLOUR, (240, 100), center=True
            )

        # Geometry is owned by _register_options_menu_regions, so the
        # drawn control and the registered region cannot diverge. Labels
        # are positioned from the rect rather than from a repeated
        # constant, for the same reason.
        button_font = self._get_cached_font(26)
        sim_label = "Simulation mode" if self._sim_mode else "Bluetooth"
        debug_label = "Debug: On" if self._debug_logging_on else "Debug: Off"

        if self._options_page == 0:
            page_items = (
                (self._options_btn_sim, sim_label),
                (self._options_btn_debug, debug_label),
            )
        else:
            page_items = (
                (self._options_btn_clear, "Clear settings"),
                (self._options_btn_update, "Check for updates"),
            )

        for _btn, _label in page_items:
            if _btn is None:
                continue
            self._draw_button(_btn, _label, (80, 80, 100), button_font)

        # The page indicator. Read the palette once, as
        # _draw_radial_mode does, so a toggle mid-frame cannot draw one
        # dot in each palette. The active page is filled; the others
        # are outlined.
        surface = self.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)
        if surface is not None:
            palette = self._palette
            for i in range(self.OPTIONS_PAGE_COUNT):
                cx = 230 + i * 20
                if i == self._options_page:
                    pygame.draw.circle(surface, palette.tick, (cx, 395), 4)
                else:
                    pygame.draw.circle(surface, palette.tick, (cx, 395), 4, 1)

        small_font = get_label_small_font()
        if small_font:
            self.rendering_engine.render_text(
                RenderTarget.BACK_BUFFER, "Swipe up to return", small_font,
                self._DISCONNECTED_TEXT_COLOUR, (240, 445), center=True
            )

    def _draw_confirm_view(self) -> None:
        """Draw the clear-settings confirmation.

        States the consequence before offering either control. Clearing
        the device store erases the pairing, so the next start has
        nothing to connect to and must run setup — a result worth
        naming in plain words before it happens
        (display review §7.3, recommendation 24).
        """
        self.rendering_engine.clear_surface(
            RenderTarget.BACK_BUFFER, self._DISCONNECTED_BG_COLOUR
        )

        title_font = get_title_display_font()
        if title_font:
            self.rendering_engine.render_text(
                RenderTarget.BACK_BUFFER, "Clear settings?", title_font,
                self._DISCONNECTED_TEXT_COLOUR, (240, 100), center=True
            )

        body_font = self._get_cached_font(22)
        if body_font:
            for _text, _y in (
                ("This erases the paired device.", 170),
                ("Setup will run at the next start.", 205),
            ):
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, _text, body_font,
                    self._DISCONNECTED_TEXT_COLOUR, (240, _y), center=True
                )

        button_font = self._get_cached_font(26)

        # Geometry is owned by _register_confirm_view_regions. The
        # confirming control is filled red so the destructive choice is
        # not the visually neutral one.
        if self._confirm_btn_yes is not None:
            self._draw_button(
                self._confirm_btn_yes, "Clear", (140, 40, 40), button_font
            )
        if self._confirm_btn_no is not None:
            self._draw_button(
                self._confirm_btn_no, "Cancel", (80, 80, 100), button_font
            )

    def _draw_update_spinner(self) -> None:
        """Draw an indeterminate progress ring while a check runs.

        Eight dots on a circle of radius 34 centred at (240, 270),
        with one highlighted. The highlighted index advances from
        self._frame_counter rather than from wall-clock time, so
        the rate is equal by construction at any frame rate — the
        same construction as the shift-cue flash phase
        (manager.py:694-698, change-4c038bed).

        The ring is 30 px below the viewport centre and its
        outermost pixel is 70 px from that centre, inside the
        238 px radius. It occupies y 230 to 310, which is clear of
        the status message at y 180 and of the hint text at y 410.
        No button is registered while the status is 'checking'
        (_register_update_view_regions), so nothing else occupies
        that band.

        Drawn only while _update_status is 'checking'. The caller
        applies that test.
        """
        try:
            dot_count = 8
            ring_radius = 34
            dot_radius = 6
            centre_x, centre_y = 240, 270

            # One step per fps_limit/8 frames — a revolution in
            # approximately 1.07 s for any fps_limit of 8 or
            # more. Below that the max(1, ...) holds the step at
            # one frame and the ring simply turns faster than
            # once a second.
            step = max(1, int(round(self.config.fps_limit / 8.0)))
            active = (self._frame_counter // step) % dot_count

            for index in range(dot_count):
                # -pi/2 puts index 0 at the top of the ring.
                angle = (2.0 * math.pi * index / dot_count) - (math.pi / 2.0)
                dot_x = centre_x + int(round(ring_radius * math.cos(angle)))
                dot_y = centre_y + int(round(ring_radius * math.sin(angle)))
                colour = (255, 255, 255) if index == active else (90, 90, 110)
                self.rendering_engine.draw_circle(
                    RenderTarget.BACK_BUFFER, colour, (dot_x, dot_y), dot_radius
                )

        except Exception as e:
            self.logger.error(f"Update spinner error: {e}", exc_info=True)

    def _draw_update_view(self) -> None:
        """Draw the update check / install sub-view."""
        self.rendering_engine.clear_surface(
            RenderTarget.BACK_BUFFER, self._DISCONNECTED_BG_COLOUR
        )

        font = get_title_display_font()
        if font:
            self.rendering_engine.render_text(
                RenderTarget.BACK_BUFFER, "Update", font,
                self._DISCONNECTED_TEXT_COLOUR, (240, 80), center=True
            )

        if self._update_status == 'checking':
            msg = "Checking\u2026"
        elif self._update_status == 'available':
            msg = f"Available: v{self._update_version}"
        elif self._update_status == 'pending':
            msg = "Installing on restart\u2026"
        elif self._update_status == 'none':
            msg = "No update found"
        else:
            msg = "Check failed"

        status_font = self._get_cached_font(26)
        if status_font:
            self.rendering_engine.render_text(
                RenderTarget.BACK_BUFFER, msg, status_font,
                self._DISCONNECTED_TEXT_COLOUR, (240, 180), center=True
            )

        # A check has no reportable progress — find_available_update
        # publishes no intermediate state — so the indicator is
        # indeterminate. It exists to distinguish a running check
        # from a stalled application (display review §7.8,
        # recommendation 28).
        if self._update_status == 'checking':
            self._draw_update_spinner()

        button_font = self._get_cached_font(26)

        # Geometry is owned by _register_update_view_regions, which also
        # clears the rects a given status does not present, so nothing is
        # drawn that was not registered.
        if self._update_status == 'available':
            if self._update_btn_install is not None:
                self._draw_button(
                    self._update_btn_install, "Install", (0, 120, 0), button_font
                )
            if self._update_btn_cancel is not None:
                self._draw_button(
                    self._update_btn_cancel, "Cancel", (80, 80, 100), button_font
                )
        elif self._update_status in ('none', 'error'):
            if self._update_btn_cancel is not None:
                self._draw_button(
                    self._update_btn_cancel, "Back", (80, 80, 100), button_font
                )

        small_font = get_label_small_font()
        if small_font:
            self.rendering_engine.render_text(
                RenderTarget.BACK_BUFFER, "Swipe up to return", small_font,
                self._DISCONNECTED_TEXT_COLOUR, (240, 410), center=True
            )

    def _on_clear_settings_requested(self) -> None:
        """Enter the clear-settings confirmation rather than acting.

        Sets the sub-view and nothing else. It must not touch
        DeviceStore — that is _on_clear_settings, which this flow
        reaches only after the confirmation is accepted.

        Bound by the options menu's page 1 (change-8c5a1e73). Clear
        settings had been removed from the menu altogether, because the
        72 px ergonomic minimum of recommendation 24 leaves room for
        three controls and the screen had four, and this method was
        left deliberately unbound until a route was agreed. The route
        is paging, not the circular re-layout of display report §7.7
        that change-b02ed4ea anticipated: two pages of two controls are
        inside the same geometric budget.

        The budget still binds. Page 1 must keep offering this method
        rather than _on_clear_settings, and adding a fourth button to
        one page would fail the geometry requirement recommendation 24
        exists to satisfy.
        """
        self._options_view = 'confirm_clear'

    def _on_cancel_clear(self) -> None:
        """Abandon the confirmation and return to the options menu.

        Returns the sub-view and invokes nothing else. It must not
        reach DeviceStore or _on_clear_settings.
        """
        self._options_view = 'menu'

    def _on_clear_settings(self) -> None:
        """Clear DeviceStore and enter SETUP mode"""
        try:
            self.logger.info("Clearing device settings")
            from ..comm.device_store import DeviceStore
            ds = DeviceStore()
            device = ds.get_primary_device()
            if device:
                ds.remove_device(device.mac_address)
            if self._setup_entry_callback:
                self.logger.info("Device store cleared — invoking setup_entry_callback")
                self._setup_entry_callback()
            else:
                self.logger.warning("setup_entry_callback not registered")
        except Exception as e:
            self.logger.error(f"Clear settings error: {e}", exc_info=True)

    def _on_simulation_mode(self) -> None:
        """Toggle session-only simulation mode.

        Toggles synthetic RPM generation without changing the current
        layout. RADIAL is the only normal layout (change-378703da).
        """
        try:
            self._sim_mode = not self._sim_mode
            self.logger.info(f"Simulation mode {'on' if self._sim_mode else 'off'}")

        except Exception as e:
            self.logger.error(f"Simulation mode toggle error: {e}", exc_info=True)

    def _on_debug_toggle(self) -> None:
        """Toggle runtime debug logging via the application callback."""
        try:
            self._debug_logging_on = not self._debug_logging_on
            self.logger.info(f"Debug logging toggle -> {'on' if self._debug_logging_on else 'off'}")
            if self._debug_toggle_callback is not None:
                self._debug_toggle_callback(self._debug_logging_on)
            else:
                self.logger.warning("debug_toggle_callback not registered")
        except Exception as e:
            self.logger.error(f"Debug toggle error: {e}", exc_info=True)

    def _on_check_updates(self) -> None:
        """Enter the update view and start an async check."""
        try:
            self._options_view = 'update'
            self._update_status = 'checking'
            self._update_wheel = None
            self._update_version = None
            self.thread_manager.worker_pool.submit(self._run_update_check)
        except Exception as e:
            self.logger.error(f"Check updates error: {e}", exc_info=True)
            self._update_status = 'error'

    def _run_update_check(self) -> None:
        """Worker: scan for an available update and set view state."""
        try:
            from ..utils import updater
            result = updater.find_available_update()
            if result is None:
                self._update_status = 'none'
            else:
                self._update_wheel, self._update_version = result
                self._update_status = 'available'
        except Exception as e:
            self.logger.error(f"Update check worker error: {e}", exc_info=True)
            self._update_status = 'error'

    def _on_confirm_install(self) -> None:
        """Stage the pending wheel and request a restart."""
        try:
            from ..utils import updater
            if self._update_wheel and updater.stage_pending(self._update_wheel):
                self._update_status = 'pending'
                self.logger.info("Update staged — requesting restart")
                if self._restart_callback is not None:
                    self._restart_callback()
                else:
                    self.logger.warning("restart_callback not registered")
            else:
                self._update_status = 'error'
        except Exception as e:
            self.logger.error(f"Confirm install error: {e}", exc_info=True)
            self._update_status = 'error'

    def _on_cancel_update(self) -> None:
        """Return to the options menu."""
        self._options_view = 'menu'
        self._update_status = 'idle'

    def _register_rpm_sliders(self) -> None:
        """Register RPM sliders with touch coordinator"""
        try:
            # Warning RPM slider
            warning_rect = pygame.Rect(60, 120, 360, 55)
            self.touch_coordinator.register_slider_region(
                "warning_rpm", warning_rect,
                track_start_x=180, track_width=200,
                min_val=1000, max_val=8000, current_val=self.config.rpm_warning
            )
            
            # Danger RPM slider
            danger_rect = pygame.Rect(60, 170, 360, 55)
            self.touch_coordinator.register_slider_region(
                "danger_rpm", danger_rect,
                track_start_x=180, track_width=200,
                min_val=1000, max_val=9000, current_val=self.config.rpm_danger
            )
            
            # Render slider visuals (simplified)
            self._render_slider_visuals("Warning RPM:", self.config.rpm_warning, 120, (255, 165, 0))
            self._render_slider_visuals("Danger RPM:", self.config.rpm_danger, 170, (255, 50, 50))
            
        except Exception as e:
            self.logger.error(f"RPM sliders error: {e}")
    
    def _render_slider_visuals(self, label: str, value: int, y_pos: int, color: Tuple[int, int, int]) -> None:
        """Render slider visual elements"""
        try:
            # Label
            font = self._get_cached_font(16)
            if font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, label, font, (200, 200, 200),
                    (120, y_pos + 27), center=True
                )
            
            # Track
            track_rect = (180, y_pos + 25, 200, 4)
            self.rendering_engine.draw_rect(RenderTarget.BACK_BUFFER, (80, 80, 80), track_rect)
            
            # Thumb (simplified positioning)
            thumb_x = 180 + int((value - 1000) / 7000 * 200)  # Approximate positioning
            self.rendering_engine.draw_circle(RenderTarget.BACK_BUFFER, color, 
                                            (thumb_x, y_pos + 27), 10)
            
            # Value display
            if font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, str(value), font, color,
                    (420, y_pos + 27), center=True
                )
                
        except Exception as e:
            self.logger.error(f"Slider visuals error: {e}")
    
    def _register_save_button(self) -> None:
        """Register save button with touch coordinator"""
        try:
            # Calculate button position in circular layout
            save_rect = pygame.Rect(350, 300, 44, 44)

            self.touch_coordinator.register_button_region(
                "save", save_rect, TouchAction.SETTINGS_CHANGE,
                lambda pos: self._save_config()
            )

            # Draw save button
            self.rendering_engine.draw_circle(RenderTarget.BACK_BUFFER, (0, 150, 0),
                                            (372, 322), 22)

            # Checkmark (simplified)
            font = self._get_cached_font(20)
            if font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER, "\u2713", font, (255, 255, 255),
                    (372, 322), center=True
                )

        except Exception as e:
            self.logger.error(f"Save button error: {e}")

    def _draw_acknowledgement_mode(self) -> None:
        """Draw acknowledgement screen with blocking tap-to-dismiss interaction.

        Renders a safety acknowledgement screen with title, warning text,
        and instruction. Registers a full-screen tap region that triggers dismissal
        and saves acknowledgement state before transitioning to post-splash mode.
        """
        try:
            # Background matches the DISCONNECTED screen's treatment
            # (issue-ba2d5de2).
            self.rendering_engine.clear_surface(
                RenderTarget.BACK_BUFFER, self._DISCONNECTED_BG_COLOUR
            )

            # Render title text 'GTach' centered near top of circle
            title_font = self._get_cached_font(72)
            if title_font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    "GTach",
                    title_font,
                    self._DISCONNECTED_TEXT_COLOUR,
                    (240, 120),
                    center=True
                )

            # Render body disclaimer text. Line breaks and coordinates
            # are pinned to on-device measurements (change-bdac4f18
            # §technical_details); render_text() does not wrap.
            body_font = self._get_plain_font(18)
            if body_font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    'THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY',
                    body_font,
                    self._DISCONNECTED_TEXT_COLOUR,
                    (240, 266),
                    center=True
                )
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    "OF ANY KIND. THE AUTHOR IS NOT LIABLE FOR ANY CLAIM,",
                    body_font,
                    self._DISCONNECTED_TEXT_COLOUR,
                    (240, 290),
                    center=True
                )
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    "DAMAGES, OR OTHER LIABILITY ARISING FROM ITS USE.",
                    body_font,
                    self._DISCONNECTED_TEXT_COLOUR,
                    (240, 314),
                    center=True
                )

            # Render instruction text
            instruction_font = self._get_plain_font(20)
            if instruction_font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    "Tap to acknowledge and continue",
                    instruction_font,
                    self._DISCONNECTED_TEXT_COLOUR,
                    (240, 400),
                    center=True
                )

            self.logger.debug("Acknowledgement screen rendered")

        except Exception as e:
            self.logger.error(f"Acknowledgement mode render error: {e}", exc_info=True)

    def _on_acknowledgement_dismissed(self) -> None:
        """Handle acknowledgement screen dismissal.

        Saves acknowledgement state with current RPM bands and engine profile,
        clears touch regions, and transitions to the post-splash display mode.
        Called when operator taps anywhere on the acknowledgement screen.
        """
        try:
            # Save acknowledgement state
            self._ack_state_manager.set_acknowledged(
                self.config.rpm_bands,
                self.config.engine_profile
            )

            # Clear touch regions
            self.touch_coordinator.clear_regions()

            # Transition to post-splash mode
            self.config.mode = self._post_splash_mode

            self.logger.info(f"Acknowledgement dismissed — transitioning to {self._post_splash_mode.name}")

        except Exception as e:
            self.logger.error(f"Acknowledgement dismissal error: {e}", exc_info=True)
            # Fallback: transition anyway to prevent being stuck
            self.config.mode = self._post_splash_mode
    
    # Background and text colours for the DISCONNECTED screen. Changed
    # from red-on-black (issue-<pending>) — a saturated red field with
    # light-grey/red text scored poorly for readability. Pale dusty
    # yellow with black text raises the contrast while keeping the
    # screen visually distinct as an alert state.
    _DISCONNECTED_BG_COLOUR = (216, 200, 146)
    _DISCONNECTED_TEXT_COLOUR = (0, 0, 0)

    def _render_disconnected(self) -> None:
        """Render DISCONNECTED screen with Setup and Simulate button affordances"""
        try:
            # Background fill. Previously cleared to black, with the
            # circular face painted over it by the rim helper; with the
            # rim removed the clear carries the colour directly, so the
            # screen looks exactly as it did (issue-950128c0). The
            # corners this now paints lie outside the round panel's
            # r=238 viewport and cannot be seen.
            self.rendering_engine.clear_surface(
                RenderTarget.BACK_BUFFER, self._DISCONNECTED_BG_COLOUR
            )

            # Connection status dot. Previously drawn only in
            # _render_normal_modes, after the early return this screen
            # takes — the dot was never reached for DISCONNECTED and so
            # was never visible here (issue-<pending>).
            self._draw_status_indicator()

            # Title — font 36 at y=145 keeps text within circular viewport.
            # Raised from y=155 to open more space above the message at
            # y=180, which sat close enough to read as crowded.
            title_font = self._get_cached_font(36)
            if title_font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    "Disconnected",
                    title_font,
                    self._DISCONNECTED_TEXT_COLOUR,
                    (240, 145),
                    center=True
                )

            # Message
            msg_font = self._get_cached_font(20)
            if msg_font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    "OBD connection not available",
                    msg_font,
                    self._DISCONNECTED_TEXT_COLOUR,
                    (240, 180),
                    center=True
                )

            # Cause line — why the last connect failed, when known.
            # Drawn between the message at y=180 and the button column,
            # whose top is 240 (_register_disconnected_regions); the
            # buttons are not moved. Nothing is drawn when no connect
            # has failed, so the screen is unchanged from before
            # issue-5e7a03c4 until there is something to say.
            _cause = None
            if self._link_cause_callback:
                _cause = self._link_cause_callback()
            if _cause:
                cause_font = self._get_cached_font(18)
                if cause_font:
                    self.rendering_engine.render_text(
                        RenderTarget.BACK_BUFFER,
                        str(_cause),
                        cause_font,
                        self._DISCONNECTED_TEXT_COLOUR,
                        (240, 210),
                        center=True
                    )

            # Geometry is owned by _register_disconnected_regions, so the
            # drawn affordance and the registered region cannot diverge.
            button_font = self._get_cached_font(28)

            if self._disconnected_btn_setup is not None:
                self._draw_button(
                    self._disconnected_btn_setup, "Setup",
                    (60, 60, 80), button_font
                )

            if self._disconnected_btn_reset is not None:
                self._draw_button(
                    self._disconnected_btn_reset, "Reset",
                    (60, 60, 80), button_font
                )

            self._draw_reconnect_spinner()

            self.logger.debug("DISCONNECTED screen rendered")

        except Exception as e:
            self.logger.error(f"Disconnected screen render error: {e}", exc_info=True)

    # Fallback period, matching reconnect_indefinitely's retry_delay
    # default. Used whenever the interval callback cannot give a usable
    # positive number.
    _RETRY_ARC_DEFAULT_PERIOD = 5.0

    # Rotating-dot reconnect spinner geometry. Centred ON the status
    # dot's position (240, 60) — see _draw_status_indicator — so the
    # dot sits in the middle of the ring rather than beside it. Ring
    # radius 26 keeps the dots well clear of the title at y=155 and of
    # the viewport edge (206 px from the display centre at most, inside
    # the ~238 px viewport radius).
    _SPINNER_CENTRE = (240, 60)
    _SPINNER_RING_RADIUS = 26
    _SPINNER_DOT_RADIUS = 4
    _SPINNER_DOT_COUNT = 8

    def _draw_reconnect_spinner(self) -> None:
        """Draw a rotating ring of dots on the DISCONNECTED screen.

        Replaces the retry-countdown arc formerly drawn here
        (issue-<pending>). The arc's geometry — a ring centred on the
        screen with a 200 px outer radius, swept across the bottom —
        was sized for a DISCONNECTED screen with one button; adding BT
        Reset (issue-8a63d5f1) filled the band the arc assumed was
        free, and the arc clipped the button. Rather than re-fit an
        arc into the remaining space, the indicator was moved to the
        upper half of the screen and reduced to a small ring of dots
        surrounding the connection status dot.

        The phase comes from the display frame clock —
        ``time.monotonic()`` — and from NO transport attribute or
        transport-derived state, for the reason the arc's docstring
        gave: an indicator fed from the transport would freeze exactly
        when the transport thread blocks in ``connect()``, which is
        when the operator most needs to see the app is still alive.

        Only the rotation PERIOD is asked of the transport, through
        ``_retry_interval_callback``; a failure to obtain it falls
        back to ``_RETRY_ARC_DEFAULT_PERIOD``. One full rotation
        corresponds to one retry period, preserving the timing cue the
        arc gave without keeping its shape.
        """
        try:
            period = self._RETRY_ARC_DEFAULT_PERIOD
            if self._retry_interval_callback:
                try:
                    candidate = self._retry_interval_callback()
                    if (isinstance(candidate, (int, float))
                            and not isinstance(candidate, bool)
                            and candidate > 0):
                        period = float(candidate)
                except Exception as e:
                    self.logger.debug(
                        f"Retry interval callback failed: {e}", exc_info=True
                    )

            surface = self.rendering_engine.get_surface(RenderTarget.BACK_BUFFER)
            if surface is None:
                return

            # 0.0 at the start of each rotation, approaching
            # _SPINNER_DOT_COUNT at its end — one dot-position of travel
            # per iteration of the loop below.
            phase = (time.monotonic() % period) / period
            lead = phase * self._SPINNER_DOT_COUNT

            dim_colour = self._DISCONNECTED_BG_COLOUR
            bright_colour = self._DISCONNECTED_TEXT_COLOUR

            for i in range(self._SPINNER_DOT_COUNT):
                # Positions behind the lead fade toward the background
                # colour so the ring reads as a single moving point
                # rather than a static ring of dots.
                offset = (i - lead) % self._SPINNER_DOT_COUNT
                weight = 1.0 - (offset / self._SPINNER_DOT_COUNT)
                colour = tuple(
                    int(dim_colour[c] + (bright_colour[c] - dim_colour[c]) * weight)
                    for c in range(3)
                )
                angle = math.radians(
                    i * (360.0 / self._SPINNER_DOT_COUNT) - 90.0
                )
                x = (self._SPINNER_CENTRE[0]
                     + self._SPINNER_RING_RADIUS * math.cos(angle))
                y = (self._SPINNER_CENTRE[1]
                     + self._SPINNER_RING_RADIUS * math.sin(angle))
                pygame.draw.circle(
                    surface, colour, (int(x), int(y)), self._SPINNER_DOT_RADIUS
                )

        except Exception as e:
            self.logger.debug(f"Reconnect spinner render error: {e}", exc_info=True)

    def _enter_setup_from_disconnected(self) -> None:
        """Enter SETUP mode from DISCONNECTED screen"""
        try:
            if self._setup_entry_callback:
                self.logger.info("Invoking setup_entry_callback from DISCONNECTED")
                self._setup_entry_callback()
            else:
                self.logger.warning("setup_entry_callback not registered")

        except Exception as e:
            self.logger.error(f"Setup entry error: {e}", exc_info=True)

    def _draw_status_indicator(self) -> None:
        """Draw connection status indicator"""
        try:
            # The indicator names the link, so it is derived from the
            # link. It previously mapped ThreadStatus.RUNNING to
            # CONNECTED, which made it green whenever the software was
            # running (issue-4d9e2f18).
            #
            # CONNECTING is the honest state between a transport that
            # says it is connected and the two samples that confirm
            # data is actually flowing.
            if self._link_lost():
                status = ConnectionStatus.DISCONNECTED
            elif not self._link_ok:
                status = ConnectionStatus.CONNECTING
            else:
                status = ConnectionStatus.CONNECTED

            color = pygame.Color(status.value)
            # (20, 20) is 311 px from the viewport centre (240, 240),
            # which has radius 238 — the dot was drawn 73 px beyond the
            # edge of the circular panel and could never be seen. This
            # position is 180 px out, outside the RADIAL centre disc
            # and the numeric readout it now carries (display review
            # §8.1, recommendation 19).
            self.rendering_engine.draw_circle(RenderTarget.BACK_BUFFER,
                                            (color.r, color.g, color.b), (240, 60), 5)
            
        except Exception as e:
            self.logger.error(f"Status indicator error: {e}")
    
    def _draw_setup_mode_fallback(self) -> None:
        """Draw basic setup mode indicator"""
        try:
            font = get_heading_font()
            if font:
                self.rendering_engine.render_text(
                    RenderTarget.BACK_BUFFER,
                    "SETUP MODE",
                    font,
                    (255, 255, 0),
                    (240, 240),
                    center=True
                )

        except Exception as e:
            self.logger.error(f"Setup mode fallback error: {e}")
    
    def _get_cached_font(self, size: int, font_path: Optional[str] = None) -> Optional[pygame.font.Font]:
        """Get cached font (simplified version)"""
        try:
            font_manager = get_font_manager()
            return font_manager.get_font(size)
        except:
            try:
                return pygame.font.Font(font_path, size) if font_path else pygame.font.Font(None, size)
            except:
                return None

    def _get_plain_font(self, size: int) -> Optional[pygame.font.Font]:
        """Get a cached plain (SDL default) font for the given size.

        Bypasses FontManager, which resolves Michroma-Regular.ttf at
        every size — too wide for multi-word body text on the 480px
        circular panel. Used only by the acknowledgement screen
        (change-bdac4f18).

        Args:
            size: Font size in pixels.

        Returns:
            Cached font object, or None if font creation failed.
        """
        cache = getattr(self, '_plain_font_cache', None)
        if cache is None:
            cache = {}
            self._plain_font_cache = cache

        if size in cache:
            return cache[size]

        try:
            font = pygame.font.Font(None, size)
        except Exception as e:
            self.logger.error(f"Plain font creation failed for size {size}: {e}")
            return None

        cache[size] = font
        return font

    # Legacy compatibility methods
    def change_mode(self, mode: DisplayMode) -> None:
        """Change display mode"""
        self.config.mode = mode
        self._save_config()
    
    def set_setup_mode(self, setup_manager) -> None:
        """Enable setup mode"""
        self._setup_manager = setup_manager
        self._in_setup_mode = True
        self.logger.info(f"Entered setup mode")
    
    def exit_setup_mode(self) -> None:
        """Exit setup mode"""
        self._in_setup_mode = False
        self._setup_manager = None
        self._enter_post_splash_mode()
        self.logger.info(f"Exited setup mode")
    
    def is_in_setup_mode(self) -> bool:
        """Check if in setup mode"""
        return self._in_setup_mode

    def handle_touch_event(self, pos: Tuple[int, int]) -> Optional[object]:
        """Handle touch events using touch coordinator"""
        try:
            self.logger.info(f"Touch event at {pos}")
            
            if self._in_setup_mode and self._setup_manager:
                # Route to setup manager
                return self._setup_manager.handle_touch_event(pos)
            else:
                # Use touch coordinator
                action = self.touch_coordinator.handle_touch_down(pos)
                
                # Handle slider value updates
                if action == TouchAction.SLIDER_INTERACTION:
                    self._update_config_from_sliders()
                
                return action
                
        except Exception as e:
            self.logger.error(f"Touch event error: {e}")
            return None
    
    def _update_config_from_sliders(self) -> None:
        """Update configuration from slider values"""
        try:
            warning_value = self.touch_coordinator.get_slider_value("warning_rpm")
            if warning_value is not None:
                self.config.rpm_warning = warning_value
            
            danger_value = self.touch_coordinator.get_slider_value("danger_rpm")
            if danger_value is not None:
                self.config.rpm_danger = danger_value
                
        except Exception as e:
            self.logger.error(f"Config update error: {e}")
    
    # Performance and debugging methods
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        try:
            return {
                'rendering_stats': self.rendering_engine.get_stats(),
                'touch_stats': self.touch_coordinator.get_stats(),
                'performance_metrics': self.performance_monitor.get_current_metrics().to_dict(),
                'performance_summary': self.performance_monitor.get_performance_summary()
            }
        except Exception as e:
            self.logger.error(f"Performance stats error: {e}")
            return {}
    
    def get_display_state(self) -> Dict[str, Any]:
        """Get current display state"""
        try:
            return {
                'display_mode': self.config.mode.name,
                'in_setup_mode': self._in_setup_mode,
                'components_initialized': {
                    'rendering_engine': self.rendering_engine.is_initialized(),
                    'touch_coordinator': True,
                    'performance_monitor': self.performance_monitor._monitoring
                },
                'active_touch_regions': len(self.touch_coordinator.get_active_regions()),
                'timestamp': time.time()
            }
        except Exception as e:
            self.logger.error(f"Display state error: {e}")
            return {'error': str(e)}