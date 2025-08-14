#!/usr/bin/env python3
"""
Test validation script for ConfigProcessor fix
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_config_processor_fix():
    """Test that ConfigProcessor now properly discovers configuration files"""
    
    print("Testing ConfigProcessor configuration discovery fix...")
    
    try:
        from provisioning.config_processor import ConfigProcessor
        print("✓ ConfigProcessor import successful")
        
        # Create test project structure
        temp_dir = Path(tempfile.mkdtemp())
        project_root = temp_dir / "test_project"
        project_root.mkdir(parents=True)
        
        # Create mock config file in expected location (src/config/)
        src_config_dir = project_root / "src" / "config"
        src_config_dir.mkdir(parents=True)
        
        mock_config = """port: AUTO
baudrate: 38400
timeout: 1.0
bluetooth:
  scan_duration: 8.0
  bleak_timeout: 10.0
display:
  fps_limit: 60
  mode: DIGITAL
debug_logging: false
data_log_enabled: false
"""
        
        config_file = src_config_dir / "config.yaml"
        config_file.write_text(mock_config)
        print(f"✓ Created mock config file: {config_file}")
        
        # Test ConfigProcessor initialization
        processor = ConfigProcessor(project_root, "raspberry-pi")
        print(f"✓ ConfigProcessor initialized successfully")
        print(f"✓ Config file discovered at: {processor.config_file_path}")
        
        if processor.config_file_path is not None:
            print("✓ Configuration discovery fix is working correctly")
            result = True
        else:
            print("✗ Configuration file not discovered")
            result = False
            
        # Cleanup
        shutil.rmtree(temp_dir)
        return result
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_processor_fix()
    if success:
        print("\n✓ All tests passed - ConfigProcessor fix is working")
        sys.exit(0)
    else:
        print("\n✗ Tests failed")
        sys.exit(1)
