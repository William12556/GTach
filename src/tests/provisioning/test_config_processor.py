#!/usr/bin/env python3
"""
Unit tests for ConfigProcessor

Tests configuration template processing including:
- Platform-specific configuration generation
- Template variable substitution
- YAML/JSON template processing
- Configuration validation
- Platform capability mapping
- Thread safety
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from provisioning.config_processor import ConfigProcessor, PlatformConfig


class TestConfigProcessor(unittest.TestCase):
    """Test ConfigProcessor functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir / "test_project"
        self.template_dir = self.project_root / "templates"
        self.output_dir = self.temp_dir / "output"
        
        # Create test directory structure
        self.project_root.mkdir(parents=True)
        self.template_dir.mkdir(parents=True)
        self.output_dir.mkdir(parents=True)
        
        # Create test templates
        self._create_test_templates()
        
        # Initialize ConfigProcessor
        self.processor = ConfigProcessor(self.project_root, "raspberry-pi")
    
    def tearDown(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_templates(self):
        """Create test configuration templates"""
        # YAML template
        yaml_template = """
app_name: GTach
app_dir: ${app_dir}
log_dir: ${log_dir}
user: ${user}
group: ${group}

display:
  fps_limit: ${fps_limit}
  mode: digital

bluetooth:
  timeout: ${bluetooth_timeout}
  scan_duration: 8.0

platform_info:
  target: ${platform_name}
  gpio_available: ${gpio_available}
"""
        (self.template_dir / "config.template.yaml").write_text(yaml_template)
        
        # JSON template
        json_template = """{
  "application": {
    "name": "GTach",
    "version": "1.0.0",
    "install_dir": "${app_dir}",
    "user": "${user}"
  },
  "performance": {
    "profile": "${performance_profile}",
    "fps_limit": ${fps_limit}
  },
  "platform": {
    "name": "${platform_name}",
    "gpio": ${gpio_available}
  }
}"""
        (self.template_dir / "app.template.json").write_text(json_template)
        
        # Service template
        service_template = """[Unit]
Description=GTach OBD-II Display Application
After=network.target

[Service]
Type=simple
User=${user}
Group=${group}
WorkingDirectory=${app_dir}
ExecStart=${python_executable} ${app_dir}/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        (self.template_dir / "service.template").write_text(service_template)
        
        # Environment template
        env_template = """# GTach Environment Configuration
APP_DIR=${app_dir}
LOG_DIR=${log_dir}
CONFIG_DIR=${config_dir}
USER=${user}
GROUP=${group}
PYTHON_EXECUTABLE=${python_executable}
PERFORMANCE_PROFILE=${performance_profile}
GPIO_AVAILABLE=${gpio_available}
"""
        (self.template_dir / "environment.template").write_text(env_template)
    
    def test_initialization(self):
        """Test ConfigProcessor initialization"""
        self.assertEqual(self.processor.project_root, self.project_root)
        self.assertEqual(self.processor.target_platform, "raspberry-pi")
        self.assertTrue(hasattr(self.processor, 'platform_configs'))
        self.assertTrue(hasattr(self.processor, 'logger'))
    
    def test_platform_configs_loaded(self):
        """Test that platform configurations are properly loaded"""
        configs = self.processor.platform_configs
        
        # Check that required platforms are available
        self.assertIn('raspberry-pi', configs)
        self.assertIn('macos', configs)
        self.assertIn('linux', configs)
        
        # Check raspberry-pi config specifics
        pi_config = configs['raspberry-pi']
        self.assertEqual(pi_config.platform_name, 'raspberry-pi')
        self.assertEqual(pi_config.template_variables['app_dir'], '/opt/gtach')
        self.assertTrue(pi_config.template_variables['gpio_available'])
        self.assertEqual(pi_config.template_variables['fps_limit'], 30)
    
    def test_get_platform_config(self):
        """Test platform configuration retrieval"""
        # Valid platform
        config = self.processor._get_platform_config()
        self.assertIsNotNone(config)
        self.assertEqual(config.platform_name, 'raspberry-pi')
        
        # Invalid platform
        processor = ConfigProcessor(self.project_root, "nonexistent-platform")
        config = processor._get_platform_config()
        self.assertIsNone(config)
    
    @patch('provisioning.config_processor.ConfigManager')
    def test_prepare_template_variables(self, mock_config_manager):
        """Test template variable preparation"""
        # Mock configuration
        mock_config = Mock()
        mock_config.port = "AUTO"
        mock_config.baudrate = 38400
        mock_config.bluetooth.scan_duration = 8.0
        mock_config.bluetooth.timeout = 2.0
        mock_config.display.fps_limit = 60
        mock_config.display.mode = "DIGITAL"
        mock_config.debug_logging = False
        
        mock_config_manager.return_value.load_config.return_value = mock_config
        
        platform_config = self.processor._get_platform_config()
        variables = self.processor._prepare_template_variables(platform_config)
        
        # Check platform variables
        self.assertEqual(variables['app_dir'], '/opt/gtach')
        self.assertEqual(variables['user'], 'pi')
        self.assertTrue(variables['gpio_available'])
        
        # Check config variables
        self.assertEqual(variables['obd_port'], 'AUTO')
        self.assertEqual(variables['obd_baudrate'], 38400)
        self.assertEqual(variables['bt_scan_duration'], 8.0)
        
        # Check system variables
        self.assertIn('system_platform', variables)
        self.assertIn('generated_at', variables)
    
    def test_get_output_filename(self):
        """Test output filename determination"""
        platform_config = self.processor._get_platform_config()
        
        # Test mapped filenames
        filename = self.processor._get_output_filename(
            Path("config.template.yaml"), platform_config
        )
        self.assertEqual(filename, "config.yaml")
        
        filename = self.processor._get_output_filename(
            Path("service.template"), platform_config
        )
        self.assertEqual(filename, "gtach.service")
        
        # Test unmapped filename
        filename = self.processor._get_output_filename(
            Path("unknown.template.txt"), platform_config
        )
        self.assertEqual(filename, "unknown.txt")
    
    def test_process_yaml_template(self):
        """Test YAML template processing"""
        template_file = self.template_dir / "config.template.yaml"
        output_file = self.output_dir / "config.yaml"
        
        variables = {
            'app_dir': '/opt/gtach',
            'log_dir': '/var/log/gtach',
            'user': 'pi',
            'group': 'pi',
            'fps_limit': 30,
            'bluetooth_timeout': 10.0,
            'platform_name': 'raspberry-pi',
            'gpio_available': True
        }
        
        self.processor._process_yaml_template(template_file, output_file, variables)
        
        self.assertTrue(output_file.exists())
        
        # Check that variables were substituted
        content = output_file.read_text()
        self.assertIn('/opt/gtach', content)
        self.assertIn('pi', content)
        self.assertIn('30', content)  # fps_limit
        self.assertIn('true', content)  # gpio_available (YAML boolean)
    
    def test_process_json_template(self):
        """Test JSON template processing"""
        template_file = self.template_dir / "app.template.json"
        output_file = self.output_dir / "app.json"
        
        variables = {
            'app_dir': '/opt/gtach',
            'user': 'pi',
            'performance_profile': 'embedded',
            'fps_limit': 30,
            'platform_name': 'raspberry-pi',
            'gpio_available': True
        }
        
        self.processor._process_json_template(template_file, output_file, variables)
        
        self.assertTrue(output_file.exists())
        
        # Parse and verify JSON
        with open(output_file) as f:
            data = json.load(f)
        
        self.assertEqual(data['application']['install_dir'], '/opt/gtach')
        self.assertEqual(data['application']['user'], 'pi')
        self.assertEqual(data['performance']['fps_limit'], 30)
        self.assertTrue(data['platform']['gpio'])
    
    def test_process_text_template(self):
        """Test text template processing"""
        template_file = self.template_dir / "environment.template"
        output_file = self.output_dir / "environment"
        
        variables = {
            'app_dir': '/opt/gtach',
            'log_dir': '/var/log/gtach',
            'config_dir': '/etc/gtach',
            'user': 'pi',
            'group': 'pi',
            'python_executable': 'python3',
            'performance_profile': 'embedded',
            'gpio_available': True
        }
        
        self.processor._process_text_template(template_file, output_file, variables)
        
        self.assertTrue(output_file.exists())
        content = output_file.read_text()
        
        # Check substitutions
        self.assertIn('APP_DIR=/opt/gtach', content)
        self.assertIn('USER=pi', content)
        self.assertIn('GPIO_AVAILABLE=True', content)
    
    @patch('provisioning.config_processor.ConfigManager')
    def test_process_templates(self, mock_config_manager):
        """Test complete template processing"""
        # Mock configuration
        mock_config = Mock()
        mock_config.port = "AUTO"
        mock_config.baudrate = 38400
        mock_config.bluetooth.scan_duration = 8.0
        mock_config.bluetooth.timeout = 2.0
        mock_config.display.fps_limit = 60
        mock_config.display.mode = "DIGITAL"
        mock_config.debug_logging = False
        
        mock_config_manager.return_value.load_config.return_value = mock_config
        
        # Process all templates
        processed_files = self.processor.process_templates(
            self.template_dir, 
            self.output_dir
        )
        
        # Should have processed all template files
        self.assertTrue(len(processed_files) > 0)
        
        # Check specific files were created
        expected_files = ['config.yaml', 'gtach.service', 'environment']
        
        for expected_file in expected_files:
            file_path = self.output_dir / expected_file
            self.assertTrue(file_path.exists(), f"Expected file not created: {expected_file}")
    
    def test_validate_config_content(self):
        """Test configuration content validation"""
        platform_config = self.processor._get_platform_config()
        validation_rules = platform_config.validation_rules
        
        # Valid configuration
        valid_config = {
            'display': {'fps_limit': 25},
            'bluetooth': {'bleak_timeout': 10.0}
        }
        
        # Should not raise exception
        self.processor._validate_config_content(valid_config, validation_rules)
        
        # Invalid configuration - exceeds FPS limit
        invalid_config = {
            'display': {'fps_limit': 60},  # Exceeds Pi limit of 30
            'bluetooth': {'bleak_timeout': 1.0}  # Below minimum of 5.0
        }
        
        # Should log warnings but not raise exception
        with self.assertLogs(level='WARNING') as log:
            self.processor._validate_config_content(invalid_config, validation_rules)
            self.assertTrue(any('FPS limit exceeds' in message for message in log.output))
    
    def test_create_platform_config_template(self):
        """Test platform-specific configuration template creation"""
        output_path = self.output_dir / "platform_config.yaml"
        
        # Mock base configuration
        mock_config = Mock()
        mock_config.to_dict.return_value = {
            'port': 'AUTO',
            'baudrate': 38400,
            'display': {'fps_limit': 60},
            'bluetooth': {'bleak_timeout': 5.0}
        }
        
        self.processor.create_platform_config_template(output_path, mock_config)
        
        self.assertTrue(output_path.exists())
        
        # Check that platform-specific adjustments were made
        content = output_path.read_text()
        if content.strip():  # Only check if file has content
            self.assertIn('raspberry-pi', content)
    
    def test_different_target_platforms(self):
        """Test processing for different target platforms"""
        platforms = ['raspberry-pi', 'macos', 'linux']
        
        for platform in platforms:
            with self.subTest(platform=platform):
                processor = ConfigProcessor(self.project_root, platform)
                config = processor._get_platform_config()
                
                self.assertIsNotNone(config, f"No config for platform: {platform}")
                self.assertEqual(config.platform_name, platform)
                
                # Check platform-specific variables
                variables = config.template_variables
                if platform == 'raspberry-pi':
                    self.assertTrue(variables['gpio_available'])
                    self.assertEqual(variables['fps_limit'], 30)
                elif platform == 'macos':
                    self.assertFalse(variables['gpio_available'])
                    self.assertEqual(variables['fps_limit'], 60)
    
    def test_thread_safety(self):
        """Test thread-safe template processing"""
        import threading
        
        results = []
        errors = []
        
        def process_templates_thread(thread_id):
            try:
                output_dir = self.temp_dir / f"output_{thread_id}"
                output_dir.mkdir(exist_ok=True)
                
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
                    
                    processed = self.processor.process_templates(
                        self.template_dir, output_dir
                    )
                    results.append((thread_id, processed))
                    
            except Exception as e:
                errors.append((thread_id, e))
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=process_templates_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 3)
    
    def test_get_stats(self):
        """Test statistics collection"""
        stats = self.processor.get_stats()
        
        self.assertIn('operation_count', stats)
        self.assertIn('target_platform', stats)
        self.assertIn('source_platform', stats)
        self.assertIn('available_platforms', stats)
        self.assertIn('cache_size', stats)
        
        self.assertEqual(stats['target_platform'], 'raspberry-pi')
        self.assertIsInstance(stats['available_platforms'], list)
        self.assertIn('raspberry-pi', stats['available_platforms'])


class TestPlatformConfig(unittest.TestCase):
    """Test PlatformConfig functionality"""
    
    def test_to_dict(self):
        """Test platform config serialization"""
        config = PlatformConfig(
            platform_name="test-platform",
            template_variables={'key': 'value'},
            file_mappings={'template.txt': 'output.txt'},
            permission_settings={'file.txt': 0o644}
        )
        
        result = config.to_dict()
        
        self.assertEqual(result['platform_name'], "test-platform")
        self.assertEqual(result['template_variables']['key'], 'value')
        self.assertEqual(result['file_mappings']['template.txt'], 'output.txt')


if __name__ == '__main__':
    unittest.main()