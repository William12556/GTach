#!/usr/bin/env python3
"""
Refactored setup mode display manager for OBDII display application.
Uses component-based architecture for improved maintainability.
"""

import logging
import math
import threading
import time
from typing import Optional, List, Tuple, Dict, Any

# Conditional import of pygame
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

from .setup_models import SetupScreen, SetupState, SetupAction, PairingStatus, BluetoothDevice, DeviceType
from .typography import (get_font_manager, get_title_display_font, get_heading_font, get_body_font, 
                         get_button_font, get_label_small_font, get_minimal_font, TypographyConstants,
                         get_button_renderer, render_standard_button, ButtonSize, ButtonState)
from .performance import get_performance_manager
from ..utils import ConfigManager
from .async_operations import get_async_manager, OperationType, OperationStatus

# Import extracted components
from .setup_components.bluetooth.interface import BluetoothSetupInterface
from .setup_components.layout.circular_positioning import CircularPositioningEngine
from .setup_components.rendering.device_surfaces import DeviceSurfaceRenderer
from .setup_components.state.coordinator import SetupStateCoordinator


class SetupDisplayManager:
    """Manages setup mode display rendering with component-based architecture
    
    This refactored version delegates responsibilities to specialized components:
    - BluetoothSetupInterface: Bluetooth operations
    - CircularPositioningEngine: Layout positioning
    - DeviceSurfaceRenderer: Device graphics
    - SetupStateCoordinator: State management
    """
    
    def __init__(self, surface, thread_manager, touch_handler):
        self.logger = logging.getLogger('SetupDisplayManager')
        self.surface = surface
        self.thread_manager = thread_manager
        self.touch_handler = touch_handler
        
        # Check pygame availability
        if not PYGAME_AVAILABLE:
            self.logger.warning("Pygame not available - setup display will use minimal functionality")
            self.display_available = False
        else:
            self.display_available = True
        
        # Initialize extracted components
        self.bluetooth_interface = BluetoothSetupInterface()
        self.positioning_engine = CircularPositioningEngine()
        self.device_renderer = DeviceSurfaceRenderer()
        self.state_coordinator = SetupStateCoordinator()
        
        # UI state and threading
        self.touch_regions = []  # Protected by _touch_regions_lock
        self._setup_thread = None
        self._shutdown_event = threading.Event()
        self._touch_regions_lock = threading.Lock()
        
        # Render state tracking
        self._screen_render_cache = {}
        self._last_rendered_screen = None
        self._screen_needs_refresh = True
        self._render_cache_lock = threading.Lock()
        
        # Colors for UI rendering
        self.colors = {
            'background': (20, 20, 30),
            'surface': (40, 40, 50),
            'primary': (100, 150, 250),
            'success': (50, 200, 50),
            'warning': (255, 165, 0),
            'danger': (255, 50, 50),
            'text': (255, 255, 255),
            'text_dim': (180, 180, 180),
            'border': (80, 80, 90)
        }
        
        # Register callbacks for component coordination
        self.state_coordinator.register_screen_transition_callback(self._on_screen_transition)
        self.state_coordinator.register_state_change_callback(self._on_state_change)
        
        self.logger.info("SetupDisplayManager initialized with component architecture")
    
    def _on_screen_transition(self, old_screen: SetupScreen, new_screen: SetupScreen) -> None:
        """Handle screen transitions from state coordinator"""
        self._invalidate_render_cache(new_screen)
        self.logger.debug(f"Screen transition handled: {old_screen.name} -> {new_screen.name}")
    
    def _on_state_change(self, changed_fields: List[str]) -> None:
        """Handle state changes from state coordinator"""
        # Invalidate cache for dynamic content changes
        if any(field in changed_fields for field in ['discovered_devices', 'pairing_status', 'selected_device']):
            self._invalidate_render_cache()
        self.logger.debug(f"State change handled: {changed_fields}")
    
    @property
    def state(self) -> SetupState:
        """Get current setup state from coordinator"""
        return self.state_coordinator.get_state()
    
    def start_setup(self) -> None:
        """Start the setup process"""
        self.logger.info("Starting Bluetooth setup")
        
        # Determine starting screen through state coordinator
        from ..comm.device_store import DeviceStore
        device_store = DeviceStore()
        if device_store.is_first_run():
            self.state_coordinator.transition_to_screen(SetupScreen.WELCOME)
        else:
            self.state_coordinator.transition_to_screen(SetupScreen.CURRENT_DEVICE)
        
        # Start setup thread
        self._setup_thread = threading.Thread(target=self._setup_loop, name='SetupManager')
        self._setup_thread.start()
    
    def stop_setup(self) -> None:
        """Stop the setup process and cancel all async operations"""
        self._shutdown_event.set()
        
        # Cancel Bluetooth operations
        self.bluetooth_interface.cancel_operations()
        
        if self._setup_thread:
            self._setup_thread.join()
        
        self.logger.info("Setup stopped - all operations cancelled")
    
    def _setup_loop(self) -> None:
        """Main setup processing loop"""
        while not self._shutdown_event.is_set():
            try:
                self.thread_manager.update_heartbeat('setup')
                
                # Update state coordinator animation
                self.state_coordinator.update_animation(0.05)
                
                # Handle auto-discovery if needed
                state = self.state_coordinator.get_state()
                if (state.current_screen == SetupScreen.DISCOVERY and 
                    state.pairing_status == PairingStatus.IDLE):
                    self.bluetooth_interface.start_discovery(
                        state, 
                        show_all_devices=self.state_coordinator.show_all_devices
                    )
                
                time.sleep(0.05)
                
            except Exception as e:
                self.logger.error(f"Setup loop error: {e}", exc_info=True)
                time.sleep(1.0)
    
    def render(self, target_surface=None) -> None:
        """Render the current setup screen"""
        if not self.display_available:
            return
        
        try:
            surface = target_surface or self.surface
            state = self.state_coordinator.get_state()
            
            # Check cache first
            if not self._screen_needs_refresh:
                with self._render_cache_lock:
                    if state.current_screen in self._screen_render_cache:
                        cached_surface = self._screen_render_cache[state.current_screen]
                        surface.blit(cached_surface, (0, 0))
                        self.logger.debug(f"Using cached render for {state.current_screen.name}")
                        self._update_cached_screen_touch_regions()
                        return
            
            # Create surface for rendering
            cache_surface = surface.copy()
            cache_surface.fill(self.colors['background'])
            
            # Render the appropriate screen
            self._render_screen(cache_surface, state)
            
            # Cache static screens
            should_cache = state.current_screen in [
                SetupScreen.WELCOME, SetupScreen.PAIRING, SetupScreen.TEST, 
                SetupScreen.COMPLETE, SetupScreen.CURRENT_DEVICE, SetupScreen.CONFIRMATION
            ]
            
            if should_cache:
                with self._render_cache_lock:
                    self._screen_render_cache[state.current_screen] = cache_surface.copy()
                    self._screen_needs_refresh = False
                    self._last_rendered_screen = state.current_screen
            
            # Copy to target surface
            surface.blit(cache_surface, (0, 0))
                
        except Exception as e:
            self.logger.error(f"Render error: {e}", exc_info=True)
    
    def _render_screen(self, surface, state: SetupState) -> None:
        """Render the appropriate screen based on current state"""
        if state.current_screen == SetupScreen.WELCOME:
            self._render_welcome_screen(surface)
        elif state.current_screen == SetupScreen.DISCOVERY:
            self._render_discovery_screen(surface, state)
        elif state.current_screen == SetupScreen.DEVICE_LIST:
            self._render_device_list_screen(surface, state)
        elif state.current_screen == SetupScreen.PAIRING:
            self._render_pairing_screen(surface, state)
        elif state.current_screen == SetupScreen.TEST:
            self._render_test_screen(surface, state)
        elif state.current_screen == SetupScreen.COMPLETE:
            self._render_complete_screen(surface, state)
        elif state.current_screen == SetupScreen.CURRENT_DEVICE:
            self._render_current_device_screen(surface, state)
        elif self.state_coordinator.manual_entry_mode:
            self._render_manual_entry_screen(surface)
        else:
            self._render_welcome_screen(surface)  # Fallback
    
    def _render_welcome_screen(self, surface) -> None:
        """Render the welcome screen"""
        new_regions = []
        
        # Title
        try:
            font_large = get_title_display_font()
            if font_large:
                title = font_large.render("Welcome", True, self.colors['text'])
                title_rect = title.get_rect(center=(240, 100))
                surface.blit(title, title_rect)
        except Exception as e:
            self.logger.error(f"Error rendering welcome title: {e}")
        
        # Description
        font_medium = get_body_font()
        if font_medium:
            desc_lines = [
                "Setup your Bluetooth",
                "ELM327 OBD-II adapter"
            ]
            
            y_pos = 160
            for line in desc_lines:
                text = font_medium.render(line, True, self.colors['text'])
                text_rect = text.get_rect(center=(240, y_pos))
                surface.blit(text, text_rect)
                y_pos += 30
        
        # Start button
        start_btn = pygame.Rect(140, 320, 200, 60)
        pygame.draw.rect(surface, self.colors['primary'], start_btn, border_radius=10)
        
        btn_font = get_button_font()
        if btn_font:
            btn_text = btn_font.render("Start Setup", True, (255, 255, 255))
            btn_text_rect = btn_text.get_rect(center=start_btn.center)
            surface.blit(btn_text, btn_text_rect)
        
        new_regions.append(("start", start_btn))
        self._update_touch_regions_safe(new_regions)
    
    def _render_discovery_screen(self, surface, state: SetupState) -> None:
        """Render the discovery screen"""
        new_regions = []
        
        # Title
        font_heading = get_heading_font()
        if font_heading:
            title = font_heading.render("Discovering Devices...", True, self.colors['text'])
            title_rect = title.get_rect(center=(240, 80))
            surface.blit(title, title_rect)
        
        # Progress info
        progress_info = self.bluetooth_interface.get_active_operation_progress()
        if progress_info['has_active_operations']:
            # Progress bar
            progress_rect = pygame.Rect(90, 180, 300, 20)
            pygame.draw.rect(surface, self.colors['border'], progress_rect, border_radius=10)
            
            progress_fill = pygame.Rect(90, 180, int(300 * progress_info['progress']), 20)
            pygame.draw.rect(surface, self.colors['primary'], progress_fill, border_radius=10)
            
            # Progress text
            font_small = get_minimal_font()
            if font_small and progress_info['message']:
                msg_text = font_small.render(progress_info['message'], True, self.colors['text_dim'])
                msg_rect = msg_text.get_rect(center=(240, 220))
                surface.blit(msg_text, msg_rect)
        
        # Cancel button
        cancel_btn = pygame.Rect(190, 350, 100, 40)
        pygame.draw.rect(surface, self.colors['warning'], cancel_btn, border_radius=8)
        
        btn_font = get_button_font()
        if btn_font:
            cancel_text = btn_font.render("Cancel", True, (255, 255, 255))
            cancel_text_rect = cancel_text.get_rect(center=cancel_btn.center)
            surface.blit(cancel_text, cancel_text_rect)
        
        new_regions.append(("cancel", cancel_btn))
        self._update_touch_regions_safe(new_regions)
    
    def _render_device_list_screen(self, surface, state: SetupState) -> None:
        """Render the device list screen using device renderer"""
        new_regions = []
        
        # Title
        font_heading = get_heading_font()
        if font_heading:
            title = font_heading.render("Select Device", True, self.colors['text'])
            title_rect = title.get_rect(center=(240, 50))
            surface.blit(title, title_rect)
        
        # Device list with curved layout
        if state.discovered_devices:
            layout_data = self.positioning_engine.calculate_curved_list_layout(
                len(state.discovered_devices), start_y=100
            )
            
            for i, device in enumerate(state.discovered_devices):
                if i < len(layout_data):
                    layout_item = layout_data[i]
                    
                    # Render device using device renderer
                    device_surface, touch_rect = self.device_renderer.create_curved_device_surface(
                        device, layout_item, i
                    )
                    
                    if device_surface:
                        # Calculate position for scaled surface
                        final_x = layout_item['x']
                        final_y = layout_item['y']
                        
                        if layout_item['scale'] < 1.0:
                            surface_width = device_surface.get_width()
                            surface_height = device_surface.get_height()
                            original_width = layout_item['width']
                            original_height = layout_item['height']
                            
                            # Center the scaled surface
                            final_x += (original_width - surface_width) // 2
                            final_y += (original_height - surface_height) // 2
                        
                        surface.blit(device_surface, (final_x, final_y))
                        new_regions.append(("device", touch_rect, device))
        else:
            # No devices found message
            font_body = get_body_font()
            if font_body:
                no_devices = font_body.render("No devices found", True, self.colors['text_dim'])
                no_devices_rect = no_devices.get_rect(center=(240, 200))
                surface.blit(no_devices, no_devices_rect)
        
        # Back and Retry buttons
        back_btn = pygame.Rect(90, 400, 100, 40)
        pygame.draw.rect(surface, self.colors['border'], back_btn, border_radius=8)
        
        retry_btn = pygame.Rect(290, 400, 100, 40)
        pygame.draw.rect(surface, self.colors['primary'], retry_btn, border_radius=8)
        
        btn_font = get_button_font()
        if btn_font:
            back_text = btn_font.render("Back", True, self.colors['text'])
            back_text_rect = back_text.get_rect(center=back_btn.center)
            surface.blit(back_text, back_text_rect)
            
            retry_text = btn_font.render("Retry", True, (255, 255, 255))
            retry_text_rect = retry_text.get_rect(center=retry_btn.center)
            surface.blit(retry_text, retry_text_rect)
        
        new_regions.extend([("back", back_btn), ("retry", retry_btn)])
        self._update_touch_regions_safe(new_regions)
    
    def _render_pairing_screen(self, surface, state: SetupState) -> None:
        """Render the pairing screen"""
        new_regions = []
        
        if not state.selected_device:
            self._update_touch_regions_safe(new_regions)
            return
        
        # Title
        font_heading = get_heading_font()
        if font_heading:
            title = font_heading.render("Pairing Device", True, self.colors['text'])
            title_rect = title.get_rect(center=(240, 80))
            surface.blit(title, title_rect)
        
        # Device name
        font_body = get_body_font()
        if font_body:
            device_text = font_body.render(state.selected_device.name, True, self.colors['text'])
            device_rect = device_text.get_rect(center=(240, 120))
            surface.blit(device_text, device_rect)
        
        # Status indicator
        center = (240, 220)
        if state.pairing_status == PairingStatus.PAIRING:
            # Animated spinner
            angle = self.state_coordinator.animation_time * 180
            for i in range(8):
                dot_angle = angle + (i * 45)
                dot_angle_rad = math.radians(dot_angle)
                dot_x = int(center[0] + 20 * math.cos(dot_angle_rad))
                dot_y = int(center[1] + 20 * math.sin(dot_angle_rad))
                alpha = 255 - (i * 30)
                color = (*self.colors['primary'][:3], alpha)
                pygame.draw.circle(surface, color, (dot_x, dot_y), 4)
        elif state.pairing_status == PairingStatus.SUCCESS:
            # Checkmark
            pygame.draw.circle(surface, self.colors['success'], center, 30, 4)
            pygame.draw.line(surface, self.colors['success'], 
                           (center[0] - 15, center[1]), (center[0] - 5, center[1] + 10), 4)
            pygame.draw.line(surface, self.colors['success'], 
                           (center[0] - 5, center[1] + 10), (center[0] + 15, center[1] - 10), 4)
        elif state.pairing_status == PairingStatus.FAILED:
            # X mark
            pygame.draw.circle(surface, self.colors['danger'], center, 30, 4)
            pygame.draw.line(surface, self.colors['danger'], 
                           (center[0] - 15, center[1] - 15), (center[0] + 15, center[1] + 15), 4)
            pygame.draw.line(surface, self.colors['danger'], 
                           (center[0] - 15, center[1] + 15), (center[0] + 15, center[1] - 15), 4)
        
        # Status text
        font_small = get_minimal_font()
        if font_small:
            status_messages = {
                PairingStatus.PAIRING: "Connecting...",
                PairingStatus.SUCCESS: "Connected successfully!",
                PairingStatus.FAILED: state.error_message or "Connection failed"
            }
            status_text = status_messages.get(state.pairing_status, "")
            if status_text:
                text = font_small.render(status_text, True, self.colors['text'])
                text_rect = text.get_rect(center=(240, 280))
                surface.blit(text, text_rect)
        
        # Action buttons
        if state.pairing_status == PairingStatus.SUCCESS:
            continue_btn = pygame.Rect(140, 380, 200, 60)
            pygame.draw.rect(surface, self.colors['success'], continue_btn, border_radius=10)
            
            btn_font = get_button_font()
            if btn_font:
                btn_text = btn_font.render("Continue", True, (255, 255, 255))
                btn_text_rect = btn_text.get_rect(center=continue_btn.center)
                surface.blit(btn_text, btn_text_rect)
            
            new_regions.append(("continue", continue_btn))
        elif state.pairing_status == PairingStatus.FAILED:
            retry_btn = pygame.Rect(90, 380, 120, 50)
            pygame.draw.rect(surface, self.colors['warning'], retry_btn, border_radius=8)
            
            back_btn = pygame.Rect(270, 380, 120, 50)
            pygame.draw.rect(surface, self.colors['border'], back_btn, border_radius=8)
            
            btn_font = get_button_font()
            if btn_font:
                retry_text = btn_font.render("Retry", True, (255, 255, 255))
                retry_text_rect = retry_text.get_rect(center=retry_btn.center)
                surface.blit(retry_text, retry_text_rect)
                
                back_text = btn_font.render("Back", True, self.colors['text'])
                back_text_rect = back_text.get_rect(center=back_btn.center)
                surface.blit(back_text, back_text_rect)
            
            new_regions.extend([("retry", retry_btn), ("back", back_btn)])
        
        self._update_touch_regions_safe(new_regions)
    
    def _render_test_screen(self, surface, state: SetupState) -> None:
        """Render the test screen"""
        new_regions = []
        
        font_heading = get_heading_font()
        if font_heading:
            title = font_heading.render("Testing Connection", True, self.colors['text'])
            title_rect = title.get_rect(center=(240, 120))
            surface.blit(title, title_rect)
        
        complete_btn = pygame.Rect(140, 320, 200, 60)
        pygame.draw.rect(surface, self.colors['success'], complete_btn, border_radius=10)
        
        btn_font = get_button_font()
        if btn_font:
            btn_text = btn_font.render("Complete", True, (255, 255, 255))
            btn_text_rect = btn_text.get_rect(center=complete_btn.center)
            surface.blit(btn_text, btn_text_rect)
        
        new_regions.append(("complete", complete_btn))
        self._update_touch_regions_safe(new_regions)
    
    def _render_complete_screen(self, surface, state: SetupState) -> None:
        """Render the completion screen"""
        new_regions = []
        
        font_heading = get_heading_font()
        if font_heading:
            title = font_heading.render("Setup Complete!", True, self.colors['success'])
            title_rect = title.get_rect(center=(240, 180))
            surface.blit(title, title_rect)
        
        self._update_touch_regions_safe(new_regions)
    
    def _render_current_device_screen(self, surface, state: SetupState) -> None:
        """Render the current device screen"""
        new_regions = []
        
        font_heading = get_heading_font()
        if font_heading:
            title = font_heading.render("Current Device", True, self.colors['text'])
            title_rect = title.get_rect(center=(240, 120))
            surface.blit(title, title_rect)
        
        self._update_touch_regions_safe(new_regions)
    
    def _render_manual_entry_screen(self, surface) -> None:
        """Render the manual entry screen"""
        new_regions = []
        
        font_heading = get_heading_font()
        if font_heading:
            title = font_heading.render("Manual Entry", True, self.colors['text'])
            title_rect = title.get_rect(center=(240, 120))
            surface.blit(title, title_rect)
        
        self._update_touch_regions_safe(new_regions)
    
    def handle_touch_event(self, pos: Tuple[int, int]) -> Optional[SetupAction]:
        """Handle touch events with state coordination"""
        try:
            # Register interaction for control visibility
            self.state_coordinator.register_interaction()
            
            # Check touch regions
            with self._touch_regions_lock:
                for region in self.touch_regions:
                    if len(region) >= 2 and isinstance(region[1], pygame.Rect):
                        if region[1].collidepoint(pos):
                            action = region[0]
                            return self._handle_touch_action(action, region)
        except Exception as e:
            self.logger.error(f"Error handling touch event: {e}")
        
        return None
    
    def _handle_touch_action(self, action: str, region: tuple) -> Optional[SetupAction]:
        """Handle specific touch actions with state coordinator"""
        try:
            if action == "start":
                self.state_coordinator.handle_setup_action(SetupAction.START_DISCOVERY)
                return SetupAction.START_DISCOVERY
            
            elif action == "device" and len(region) > 2:
                device = region[2]
                self.state_coordinator.handle_setup_action(SetupAction.SELECT_DEVICE, device=device)
                # Start pairing
                state = self.state_coordinator.get_state()
                self.bluetooth_interface.start_pairing(device, state)
                return SetupAction.SELECT_DEVICE
            
            elif action == "continue":
                self.state_coordinator.handle_setup_action(SetupAction.NEXT)
                return SetupAction.NEXT
            
            elif action == "back":
                self.state_coordinator.handle_setup_action(SetupAction.BACK)
                return SetupAction.BACK
            
            elif action == "retry":
                self.state_coordinator.handle_setup_action(SetupAction.RETRY)
                return SetupAction.RETRY
            
            elif action == "cancel":
                self.state_coordinator.handle_setup_action(SetupAction.CANCEL)
                return SetupAction.CANCEL
            
            elif action == "complete":
                self.state_coordinator.handle_setup_action(SetupAction.COMPLETE)
                return SetupAction.COMPLETE
            
        except Exception as e:
            self.logger.error(f"Error handling touch action {action}: {e}")
        
        return None
    
    def _update_touch_regions_safe(self, new_regions: List[tuple]) -> None:
        """Thread-safe update of touch regions"""
        try:
            with self._touch_regions_lock:
                self.touch_regions = new_regions.copy()
        except Exception as e:
            self.logger.error(f"Error updating touch regions: {e}")
    
    def _update_cached_screen_touch_regions(self) -> None:
        """Update touch regions for cached screens"""
        # For cached screens, we need to reconstruct touch regions
        # This is a simplified version - in production, you'd want to cache these too
        state = self.state_coordinator.get_state()
        if state.current_screen == SetupScreen.WELCOME:
            start_btn = pygame.Rect(140, 320, 200, 60)
            self._update_touch_regions_safe([("start", start_btn)])
    
    def _invalidate_render_cache(self, screen_type: SetupScreen = None) -> None:
        """Invalidate render cache for specific screen or all screens"""
        with self._render_cache_lock:
            if screen_type is None:
                self._screen_render_cache.clear()
                self._screen_needs_refresh = True
                self.logger.debug("Invalidated all screen render cache")
            else:
                if screen_type in self._screen_render_cache:
                    del self._screen_render_cache[screen_type]
                self._screen_needs_refresh = True
                self.logger.debug(f"Invalidated render cache for {screen_type.name}")
    
    def is_setup_complete(self) -> bool:
        """Check if setup is complete"""
        return self.state_coordinator.get_state().setup_complete