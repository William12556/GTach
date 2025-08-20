#!/usr/bin/env python3
# Copyright (c) 2025 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""
Direct validation of ConfigProcessor fix - minimal test version
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add project src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def validate_config_processor_fix():
    """Validate that ConfigProcessor now properly handles configuration files"""
    
    print("Validating ConfigProcessor configuration discovery fix...")
    
    # Create temporary test environment
    temp_dir = Path(tempfile.mkdtemp())
    test_project_root = temp_dir / "test_project"
    
    try:
        # Setup test project structure
        test_project_root.mkdir(parents=True)
        src_config_dir = test_project_root / "src" / "config"
        src_config_dir.mkdir(parents=True)
        
        # Create mock configuration file
        mock_config_content = """port: AUTO
baudrate: 38400
timeout: 1.0
reconnect_attempts: 3
fast_mode: true
bluetooth:
  saved_devices: []
  auto_connect: true
  scan_duration: 8.0
  retry_limit: 3
  timeout: 2.0
  bleak_timeout: 10.0
display:
  mode: DIGITAL
  rpm_warning: 6500
  rpm_danger: 7000
  fps_limit: 60
debug_logging: false
data_log_enabled: false"""
        
        config_file = src_config_dir / "config.yaml"
        config_file.write_text(mock_config_content)
        print(f"✓ Created test config file: {config_file}")
        
        # Import and test ConfigProcessor
        from provisioning.config_processor import ConfigProcessor
        print("✓ ConfigProcessor imported successfully")
        
        # Initialize ConfigProcessor with test project
        processor = ConfigProcessor(test_project_root, "raspberry-pi")
        print("✓ ConfigProcessor initialized")
        
        # Check that config file was discovered
        if processor.config_file_path is not None:
            print(f"✓ Configuration file discovered: {processor.config_file_path}")
            
            # Test that template processing validation passes
            template_dir = test_project_root / "templates"
            template_dir.mkdir()
            output_dir = temp_dir / "output"
            output_dir.mkdir()
            
            # Create a simple template file
            simple_template = """app_name: GTach
app_dir: ${app_dir}
user: ${user}
"""
            (template_dir / "test.template.yaml").write_text(simple_template)
            
            # Try to process templates (should not fail due to missing config now)
            try:
                from unittest.mock import Mock, patch
                with patch('provisioning.config_processor.ConfigManager') as mock_cm:
                    mock_config = Mock()
                    mock_config.port = "AUTO"
                    mock_config.baudrate = 38400
                    mock_config.bluetooth.scan_duration = 8.0
                    mock_config.bluetooth.timeout = 2.0
                    mock_config.display.fps_limit = 60
                    mock_config.display.mode = "DIGITAL"
                    mock_config.debug_logging = False
                    mock_cm.return_value.load_config.return_value = mock_config
                    
                    processed_files = processor.process_templates(template_dir, output_dir)
                    print(f"✓ Template processing successful: {len(processed_files)} files processed")
                    
                return True
                
            except Exception as template_error:
                print(f"✗ Template processing failed: {template_error}")
                return False
                
        else:
            print("✗ Configuration file not discovered")
            return False
            
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    success = validate_config_processor_fix()
    
    if success:
        print("\n✓ ConfigProcessor fix validation PASSED")
        print("The test failures should now be resolved.")
    else:
        print("\n✗ ConfigProcessor fix validation FAILED") 
        
    sys.exit(0 if success else 1)
