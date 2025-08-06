#!/usr/bin/env python3
"""
Setup state coordinator for workflow management.
Handles setup workflow management and state transitions with thread safety.
"""

import logging
import threading
import time
from typing import Optional, List, Dict, Any, Callable
from ...setup_models import SetupScreen, SetupState, SetupAction, PairingStatus, BluetoothDevice


class SetupStateCoordinator:
    """Setup workflow management and state transitions with thread-safe coordination"""
    
    def __init__(self, initial_state: Optional[SetupState] = None):
        self.logger = logging.getLogger('SetupStateCoordinator')
        
        # Initialize setup state
        if initial_state:
            self.state = initial_state
        else:
            from ....comm.device_store import DeviceStore
            device_store = DeviceStore()
            self.state = SetupState(
                current_screen=SetupScreen.WELCOME,
                discovered_devices=[],
                selected_device=None,
                pairing_status=PairingStatus.IDLE,
                setup_complete=False,
                discovery_timeout=device_store.get_discovery_timeout()
            )
        
        # UI state management
        self.scroll_offset = 0
        self.max_scroll = 0
        self.animation_time = 0.0
        self.show_all_devices = False
        self.manual_entry_mode = False
        self.manual_mac_input = ""
        
        # Threading and state management
        self._state_lock = threading.Lock()
        self._screen_transition_callbacks = []
        self._state_change_callbacks = []
        
        # Control visibility state
        self._controls_visible = True
        self._last_interaction_time = time.time()
        self._control_auto_hide_delay = 3.0
        self._control_fade_duration = 0.5
        self._control_alpha = 255
        self._control_visibility_lock = threading.Lock()
        
        self.logger.info("SetupStateCoordinator initialized")
    
    def get_state(self) -> SetupState:
        """Get current setup state (thread-safe)"""
        with self._state_lock:
            return self.state
    
    def update_state(self, **kwargs) -> None:
        """Update setup state with thread safety"""
        with self._state_lock:
            changed_fields = []
            
            for key, value in kwargs.items():
                if hasattr(self.state, key):
                    old_value = getattr(self.state, key)
                    if old_value != value:
                        setattr(self.state, key, value)
                        changed_fields.append(key)
                        self.logger.debug(f"State updated: {key} = {value}")
                else:
                    self.logger.warning(f"Attempted to update unknown state field: {key}")
            
            # Notify callbacks of state changes
            if changed_fields:
                self._notify_state_change_callbacks(changed_fields)
    
    def transition_to_screen(self, screen: SetupScreen, clear_cache: bool = True) -> None:
        """Transition to a new screen with state management"""
        with self._state_lock:
            if self.state.current_screen != screen:
                old_screen = self.state.current_screen
                self.state.current_screen = screen
                
                self.logger.info(f"Screen transition: {old_screen.name} -> {screen.name}")
                
                # Screen-specific state updates
                if screen == SetupScreen.DISCOVERY:
                    self.state.pairing_status = PairingStatus.IDLE
                elif screen == SetupScreen.DEVICE_LIST:
                    self.scroll_offset = 0
                elif screen == SetupScreen.PAIRING:
                    if not self.state.selected_device:
                        self.logger.warning("Transitioning to PAIRING screen without selected device")
                elif screen == SetupScreen.COMPLETE:
                    self.state.setup_complete = True
                
                # Notify callbacks
                self._notify_screen_transition_callbacks(old_screen, screen)
    
    def select_device(self, device: BluetoothDevice) -> None:
        """Select a device for pairing"""
        with self._state_lock:
            self.state.selected_device = device
            self.logger.info(f"Device selected: {device.name} ({device.mac_address})")
    
    def reset_discovery(self) -> None:
        """Reset discovery state"""
        with self._state_lock:
            self.state.discovered_devices = []
            self.state.discovery_progress = 0.0
            self.state.pairing_status = PairingStatus.IDLE
            self.scroll_offset = 0
            self.logger.info("Discovery state reset")
    
    def complete_setup(self) -> None:
        """Mark setup as complete"""
        with self._state_lock:
            self.state.setup_complete = True
            self.state.current_screen = SetupScreen.COMPLETE
            self.logger.info("Setup marked as complete")
    
    def handle_setup_action(self, action: SetupAction, **kwargs) -> bool:
        """Handle setup actions with state coordination"""
        try:
            self.logger.debug(f"Handling setup action: {action.name}")
            
            if action == SetupAction.START_DISCOVERY:
                self.transition_to_screen(SetupScreen.DISCOVERY)
                self.reset_discovery()
                return True
                
            elif action == SetupAction.SELECT_DEVICE:
                device = kwargs.get('device')
                if device:
                    self.select_device(device)
                    self.transition_to_screen(SetupScreen.PAIRING)
                    return True
                else:
                    self.logger.error("SELECT_DEVICE action without device parameter")
                    return False
                    
            elif action == SetupAction.RETRY:
                if self.state.current_screen == SetupScreen.DEVICE_LIST:
                    self.reset_discovery()
                    self.transition_to_screen(SetupScreen.DISCOVERY)
                elif self.state.current_screen == SetupScreen.PAIRING:
                    # Retry pairing with current device
                    if self.state.selected_device:
                        self.update_state(pairing_status=PairingStatus.IDLE)
                    else:
                        self.logger.error("RETRY action in pairing screen without selected device")
                        return False
                return True
                
            elif action == SetupAction.BACK:
                return self._handle_back_navigation()
                
            elif action == SetupAction.NEXT:
                return self._handle_next_navigation()
                
            elif action == SetupAction.CANCEL:
                self.transition_to_screen(SetupScreen.WELCOME)
                self.reset_discovery()
                return True
                
            elif action == SetupAction.COMPLETE:
                self.complete_setup()
                return True
                
            else:
                self.logger.warning(f"Unhandled setup action: {action.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error handling setup action {action.name}: {e}")
            return False
    
    def _handle_back_navigation(self) -> bool:
        """Handle back navigation between screens"""
        current = self.state.current_screen
        
        if current == SetupScreen.DEVICE_LIST:
            self.transition_to_screen(SetupScreen.DISCOVERY)
        elif current == SetupScreen.PAIRING:
            self.transition_to_screen(SetupScreen.DEVICE_LIST)
        elif current == SetupScreen.TEST:
            self.transition_to_screen(SetupScreen.DEVICE_LIST)
        elif current == SetupScreen.COMPLETE:
            self.transition_to_screen(SetupScreen.TEST)
        elif current in [SetupScreen.DISCOVERY, SetupScreen.WELCOME]:
            self.transition_to_screen(SetupScreen.WELCOME)
        else:
            self.transition_to_screen(SetupScreen.WELCOME)
        
        return True
    
    def _handle_next_navigation(self) -> bool:
        """Handle next navigation between screens"""
        current = self.state.current_screen
        
        if current == SetupScreen.WELCOME:
            self.transition_to_screen(SetupScreen.DISCOVERY)
        elif current == SetupScreen.DISCOVERY:
            if self.state.discovered_devices:
                self.transition_to_screen(SetupScreen.DEVICE_LIST)
            else:
                self.logger.warning("NEXT from discovery without discovered devices")
                return False
        elif current == SetupScreen.DEVICE_LIST:
            if self.state.selected_device:
                self.transition_to_screen(SetupScreen.PAIRING)
            else:
                self.logger.warning("NEXT from device list without selected device")
                return False
        elif current == SetupScreen.PAIRING:
            if self.state.pairing_status == PairingStatus.SUCCESS:
                self.transition_to_screen(SetupScreen.TEST)
            else:
                self.logger.warning("NEXT from pairing without successful pairing")
                return False
        elif current == SetupScreen.TEST:
            self.complete_setup()
        else:
            self.logger.warning(f"NEXT navigation not defined for screen: {current.name}")
            return False
        
        return True
    
    def register_screen_transition_callback(self, callback: Callable[[SetupScreen, SetupScreen], None]) -> None:
        """Register callback for screen transitions"""
        self._screen_transition_callbacks.append(callback)
        self.logger.debug("Screen transition callback registered")
    
    def register_state_change_callback(self, callback: Callable[[List[str]], None]) -> None:
        """Register callback for state changes"""
        self._state_change_callbacks.append(callback)
        self.logger.debug("State change callback registered")
    
    def _notify_screen_transition_callbacks(self, old_screen: SetupScreen, new_screen: SetupScreen) -> None:
        """Notify all screen transition callbacks"""
        for callback in self._screen_transition_callbacks:
            try:
                callback(old_screen, new_screen)
            except Exception as e:
                self.logger.error(f"Error in screen transition callback: {e}")
    
    def _notify_state_change_callbacks(self, changed_fields: List[str]) -> None:
        """Notify all state change callbacks"""
        for callback in self._state_change_callbacks:
            try:
                callback(changed_fields)
            except Exception as e:
                self.logger.error(f"Error in state change callback: {e}")
    
    def update_animation(self, delta_time: float) -> None:
        """Update animation time and control visibility"""
        self.animation_time += delta_time
        self._update_control_visibility()
    
    def register_interaction(self) -> None:
        """Register user interaction for control auto-hide"""
        with self._control_visibility_lock:
            self._last_interaction_time = time.time()
            if not self._controls_visible:
                self._controls_visible = True
                self.logger.debug("Controls made visible due to user interaction")
    
    def _update_control_visibility(self, force_visible: bool = False) -> None:
        """Update control visibility based on interaction timing"""
        try:
            with self._control_visibility_lock:
                current_time = time.time()
                time_since_interaction = current_time - self._last_interaction_time
                
                if force_visible:
                    self._controls_visible = True
                    self._control_alpha = 255
                    return
                
                # Auto-hide logic
                if time_since_interaction > self._control_auto_hide_delay:
                    # Fade out controls
                    fade_progress = min(1.0, (time_since_interaction - self._control_auto_hide_delay) / self._control_fade_duration)
                    self._control_alpha = int(255 * (1.0 - fade_progress))
                    
                    if fade_progress >= 1.0:
                        self._controls_visible = False
                else:
                    # Controls should be visible
                    self._controls_visible = True
                    self._control_alpha = 255
                    
        except Exception as e:
            self.logger.error(f"Error updating control visibility: {e}")
    
    def get_control_alpha(self) -> int:
        """Get current control alpha value for rendering"""
        with self._control_visibility_lock:
            return self._control_alpha
    
    def are_controls_visible(self) -> bool:
        """Check if controls are currently visible"""
        with self._control_visibility_lock:
            return self._controls_visible
    
    def toggle_device_filter(self) -> None:
        """Toggle between showing all devices and ELM327 only"""
        with self._state_lock:
            self.show_all_devices = not self.show_all_devices
            self.logger.info(f"Device filter toggled: show_all_devices = {self.show_all_devices}")
    
    def enter_manual_entry_mode(self) -> None:
        """Enter manual MAC address entry mode"""
        with self._state_lock:
            self.manual_entry_mode = True
            self.manual_mac_input = ""
            self.logger.info("Entered manual MAC entry mode")
    
    def exit_manual_entry_mode(self) -> None:
        """Exit manual MAC address entry mode"""
        with self._state_lock:
            self.manual_entry_mode = False
            self.manual_mac_input = ""
            self.logger.info("Exited manual MAC entry mode")
    
    def update_manual_mac_input(self, mac_input: str) -> None:
        """Update manual MAC address input"""
        with self._state_lock:
            self.manual_mac_input = mac_input
            self.logger.debug(f"Manual MAC input updated: {mac_input}")
    
    def is_valid_mac_address(self, mac: str) -> bool:
        """Validate MAC address format"""
        try:
            # Remove separators and convert to uppercase
            clean_mac = mac.replace(':', '').replace('-', '').replace(' ', '').upper()
            
            # Check length and hex characters
            if len(clean_mac) != 12:
                return False
            
            # Verify all characters are hex
            for char in clean_mac:
                if char not in '0123456789ABCDEF':
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating MAC address: {e}")
            return False
    
    def create_manual_device(self, mac_address: str, device_name: str = None) -> Optional[BluetoothDevice]:
        """Create a BluetoothDevice from manual input"""
        try:
            if not self.is_valid_mac_address(mac_address):
                self.logger.error(f"Invalid MAC address format: {mac_address}")
                return None
            
            # Format MAC address with colons
            clean_mac = mac_address.replace(':', '').replace('-', '').replace(' ', '').upper()
            formatted_mac = ':'.join([clean_mac[i:i+2] for i in range(0, 12, 2)])
            
            # Create device with manual entry indication
            device_name = device_name or f"Manual-{formatted_mac[-5:]}"
            
            from ...setup_models import DeviceType
            manual_device = BluetoothDevice(
                name=device_name,
                mac_address=formatted_mac,
                device_type="Manual Entry",
                rssi=None,
                device_classification=DeviceType.POSSIBLY_COMPATIBLE
            )
            
            self.logger.info(f"Created manual device: {device_name} ({formatted_mac})")
            return manual_device
            
        except Exception as e:
            self.logger.error(f"Error creating manual device: {e}")
            return None
    
    def get_scroll_info(self) -> Dict[str, Any]:
        """Get current scroll information"""
        with self._state_lock:
            return {
                'scroll_offset': self.scroll_offset,
                'max_scroll': self.max_scroll,
                'show_all_devices': self.show_all_devices,
                'manual_entry_mode': self.manual_entry_mode,
                'manual_mac_input': self.manual_mac_input
            }
    
    def update_scroll_offset(self, offset: int, max_scroll: int) -> None:
        """Update scroll offset with bounds checking"""
        with self._state_lock:
            self.scroll_offset = max(0, min(offset, max_scroll))
            self.max_scroll = max_scroll
    
    def get_setup_progress(self) -> Dict[str, Any]:
        """Get overall setup progress information"""
        with self._state_lock:
            # Calculate progress based on current screen
            progress_map = {
                SetupScreen.WELCOME: 0.0,
                SetupScreen.DISCOVERY: 0.2,
                SetupScreen.DEVICE_LIST: 0.4,
                SetupScreen.PAIRING: 0.6,
                SetupScreen.TEST: 0.8,
                SetupScreen.COMPLETE: 1.0
            }
            
            base_progress = progress_map.get(self.state.current_screen, 0.0)
            
            # Add sub-progress for current operations
            if self.state.current_screen == SetupScreen.DISCOVERY:
                base_progress += (self.state.discovery_progress or 0.0) * 0.2
            elif self.state.current_screen == SetupScreen.PAIRING:
                if self.state.pairing_status == PairingStatus.PAIRING:
                    base_progress += 0.1
                elif self.state.pairing_status == PairingStatus.SUCCESS:
                    base_progress += 0.2
            
            return {
                'progress': min(1.0, base_progress),
                'current_screen': self.state.current_screen.name,
                'setup_complete': self.state.setup_complete,
                'selected_device': self.state.selected_device.name if self.state.selected_device else None,
                'discovered_devices_count': len(self.state.discovered_devices),
                'pairing_status': self.state.pairing_status.name
            }