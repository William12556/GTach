#!/usr/bin/env python3
"""
Unit tests for PackageCreator

Tests package creation functionality including:
- Basic package creation
- Configuration handling
- File collection and filtering
- Archive creation
- Manifest generation
- Thread safety
- Error handling
"""

import os
import sys
import unittest
import tempfile
import shutil
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from provisioning.package_creator import PackageCreator, PackageConfig, PackageManifest
from provisioning.archive_manager import CompressionFormat


class TestPackageCreator(unittest.TestCase):
    """Test PackageCreator functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir / "test_project"
        self.output_dir = self.temp_dir / "output"
        
        # Create test project structure
        self._create_test_project()
        
        # Initialize PackageCreator
        self.creator = PackageCreator(self.project_root)
        
    def tearDown(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_project(self):
        """Create a test project structure"""
        # Create project directories
        (self.project_root / "src" / "obdii").mkdir(parents=True, exist_ok=True)
        (self.project_root / "src" / "config").mkdir(parents=True, exist_ok=True)
        (self.project_root / "scripts").mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test source files
        test_files = [
            "src/obdii/__init__.py",
            "src/obdii/main.py", 
            "src/obdii/utils.py",
            "src/config/config.yaml",
            "scripts/install.sh",
            "requirements.txt"
        ]
        
        for file_path in test_files:
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write test content
            if file_path.endswith('.py'):
                content = f'"""Test module: {file_path}"""\nprint("Hello from {file_path}")\n'
            elif file_path.endswith('.yaml'):
                content = 'test_config: true\nvalue: 42\n'
            elif file_path.endswith('.sh'):
                content = '#!/bin/bash\necho "Installing..."\n'
            elif file_path == 'requirements.txt':
                content = 'pytest>=6.0\nrequests>=2.25\n'
            else:
                content = f'Test content for {file_path}\n'
            
            full_path.write_text(content)
        
        # Create some files that should be excluded
        (self.project_root / "src" / "__pycache__").mkdir(exist_ok=True)
        (self.project_root / "src" / "__pycache__" / "test.pyc").write_text("compiled")
        (self.project_root / "src" / "obdii" / "test_module.py").write_text("test code")
        (self.project_root / ".git").mkdir(exist_ok=True)
        (self.project_root / ".git" / "config").write_text("git config")
    
    def test_initialization(self):
        """Test PackageCreator initialization"""
        self.assertEqual(self.creator.project_root, self.project_root)
        self.assertTrue(hasattr(self.creator, 'source_platform'))
        self.assertTrue(hasattr(self.creator, 'config_manager'))
        self.assertTrue(hasattr(self.creator, 'logger'))
    
    def test_auto_detect_project_root(self):
        """Test auto-detection of project root"""
        # Create nested directory structure
        nested_dir = self.project_root / "deep" / "nested" / "path"
        nested_dir.mkdir(parents=True)
        
        # Initialize from nested directory
        original_cwd = os.getcwd()
        try:
            os.chdir(nested_dir)
            creator = PackageCreator()
            # Resolve both paths to handle symlinks in temp directories
            self.assertEqual(creator.project_root.resolve(), self.project_root.resolve())
        finally:
            os.chdir(original_cwd)
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config"""
        config = PackageConfig(
            package_name="test-package",
            version="1.0.0",
            source_dirs=["src/obdii"],
            output_dir=str(self.output_dir)
        )
        
        # Should not raise exception
        self.creator._validate_config(config)
    
    def test_validate_config_invalid(self):
        """Test configuration validation with invalid config"""
        # Empty package name
        config = PackageConfig(package_name="", version="1.0.0")
        with self.assertRaises(ValueError):
            self.creator._validate_config(config)
        
        # Non-existent source directory
        config = PackageConfig(
            package_name="test",
            version="1.0.0",
            source_dirs=["nonexistent"]
        )
        with self.assertRaises(ValueError):
            self.creator._validate_config(config)
    
    def test_collect_source_files(self):
        """Test source file collection"""
        config = PackageConfig(source_dirs=["src/obdii"])
        files = self.creator._collect_source_files(config)
        
        # Should collect Python files but exclude test files and cache
        file_names = [f.name for f in files]
        
        self.assertIn("__init__.py", file_names)
        self.assertIn("main.py", file_names)
        self.assertIn("utils.py", file_names)
        self.assertNotIn("test_module.py", file_names)  # Excluded by pattern
    
    def test_should_exclude_file(self):
        """Test file exclusion logic"""
        exclude_patterns = {"__pycache__", "*.pyc", "test_*", ".git"}
        
        # Test various file paths
        test_cases = [
            (Path("src/__pycache__/module.pyc"), True),
            (Path("src/module.pyc"), True), 
            (Path("src/test_module.py"), True),
            (Path(".git/config"), True),
            (Path("src/main.py"), False),
            (Path("src/utils.py"), False)
        ]
        
        for file_path, should_exclude in test_cases:
            result = self.creator._should_exclude_file(file_path, exclude_patterns)
            self.assertEqual(result, should_exclude, f"Failed for {file_path}")
    
    def test_create_manifest(self):
        """Test package manifest creation"""
        config = PackageConfig(
            package_name="test-package",
            version="1.2.3",
            include_dependencies=True
        )
        
        source_files = [self.project_root / "src" / "obdii" / "main.py"]
        template_files = ["config.yaml"]
        script_files = ["install.sh"]
        
        # Mock workspace_dir for this test
        with patch.object(self.creator, 'workspace_dir', self.temp_dir):
            manifest = self.creator._create_manifest(
                config, source_files, template_files, script_files
            )
            
            self.assertEqual(manifest.package_name, "test-package")
            self.assertEqual(manifest.version, "1.2.3")
            self.assertTrue(len(manifest.source_files) > 0)
            self.assertEqual(manifest.config_templates, template_files)
            self.assertEqual(manifest.scripts, script_files)
            self.assertTrue(len(manifest.dependencies) > 0)  # From requirements.txt
    
    def test_create_pi_install_script(self):
        """Test Raspberry Pi install script creation"""
        config = PackageConfig(package_name="test-app", version="1.0.0")
        
        with patch.object(self.creator, 'workspace_dir', self.temp_dir):
            script_path = self.creator._create_pi_install_script(config)
            
            self.assertTrue(script_path.exists())
            content = script_path.read_text()
            self.assertIn("#!/bin/bash", content)
            self.assertIn("test-app v1.0.0", content)
            self.assertIn("Raspberry Pi", content)
            self.assertTrue(os.access(script_path, os.X_OK))  # Executable
    
    def test_create_generic_install_script(self):
        """Test generic install script creation"""
        config = PackageConfig(package_name="test-app", version="1.0.0")
        
        with patch.object(self.creator, 'workspace_dir', self.temp_dir):
            script_path = self.creator._create_generic_install_script(config)
            
            self.assertTrue(script_path.exists())
            content = script_path.read_text()
            self.assertIn("#!/usr/bin/env python3", content)
            self.assertIn("test-app v1.0.0", content)
    
    @patch('provisioning.config_processor.ConfigProcessor')
    def test_process_config_templates(self, mock_config_processor_class):
        """Test configuration template processing"""
        mock_processor = Mock()
        mock_processor.process_templates.return_value = ["config.yaml", "env.conf"]
        mock_config_processor_class.return_value = mock_processor
        
        config = PackageConfig(
            target_platform="raspberry-pi",
            config_template_dirs=["src/config"]
        )
        
        with patch.object(self.creator, 'workspace_dir', self.temp_dir):
            template_files = self.creator._process_config_templates(config)
            
            self.assertEqual(template_files, ["config.yaml", "env.conf"])
            mock_config_processor_class.assert_called_once_with(
                self.project_root, "raspberry-pi"
            )
    
    @patch('provisioning.config_processor.ConfigProcessor')
    def test_create_package_basic(self, mock_config_processor_class):
        """Test basic package creation"""
        # Mock the config processor to avoid template processing issues
        mock_processor = Mock()
        mock_processor.process_templates.return_value = []
        mock_config_processor_class.return_value = mock_processor
        
        config = PackageConfig(
            package_name="test-package",
            version="1.0.0",
            source_dirs=["src/obdii"],
            config_template_dirs=[],  # Empty to skip template processing
            output_dir=str(self.output_dir),
            verify_integrity=False  # Skip integrity check for speed
        )
        
        package_path = self.creator.create_package(config)
        
        self.assertTrue(package_path.exists())
        self.assertTrue(package_path.name.startswith("test-package-1.0.0"))
        self.assertTrue(package_path.name.endswith(".tar.gz"))
        
        # Verify package is a valid archive
        import tarfile
        self.assertTrue(tarfile.is_tarfile(package_path))
    
    @patch('provisioning.config_processor.ConfigProcessor')
    def test_create_package_with_output_path(self, mock_config_processor_class):
        """Test package creation with specific output path"""
        # Mock the config processor
        mock_processor = Mock()
        mock_processor.process_templates.return_value = []
        mock_config_processor_class.return_value = mock_processor
        
        config = PackageConfig(
            package_name="test-package",
            version="1.0.0",
            source_dirs=["src/obdii"],
            config_template_dirs=[]  # Empty to skip template processing
        )
        
        output_path = self.output_dir / "custom-package.tar.gz"
        package_path = self.creator.create_package(config, output_path)
        
        self.assertEqual(package_path, output_path)
        self.assertTrue(package_path.exists())
    
    @patch('provisioning.config_processor.ConfigProcessor')
    def test_thread_safety(self, mock_config_processor_class):
        """Test thread-safe package creation"""
        # Mock the config processor
        mock_processor = Mock()
        mock_processor.process_templates.return_value = []
        mock_config_processor_class.return_value = mock_processor
        
        config = PackageConfig(
            package_name="test-package",
            version="1.0.0", 
            source_dirs=["src/obdii"],
            config_template_dirs=[],  # Empty to skip template processing
            output_dir=str(self.output_dir),
            verify_integrity=False
        )
        
        results = []
        errors = []
        
        def create_package_thread(thread_id):
            try:
                output_path = self.output_dir / f"package-{thread_id}.tar.gz"
                package_path = self.creator.create_package(config, output_path)
                results.append(package_path)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_package_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 3)
        
        for package_path in results:
            self.assertTrue(package_path.exists())
    
    def test_error_handling(self):
        """Test error handling during package creation"""
        # Test with invalid source directory
        config = PackageConfig(
            package_name="test-package",
            version="1.0.0",
            source_dirs=["nonexistent"]
        )
        
        with self.assertRaises(RuntimeError):
            self.creator.create_package(config)
    
    def test_get_stats(self):
        """Test statistics collection"""
        stats = self.creator.get_stats()
        
        self.assertIn('operation_count', stats)
        self.assertIn('project_root', stats)
        self.assertIn('source_platform', stats)
        self.assertIsInstance(stats['operation_count'], int)


class TestPackageManifest(unittest.TestCase):
    """Test PackageManifest functionality"""
    
    def test_to_dict(self):
        """Test manifest serialization to dictionary"""
        manifest = PackageManifest(
            package_name="test-package",
            version="1.0.0",
            created_at="2023-01-01T00:00:00",
            source_platform="MACOS",
            target_platform="raspberry-pi",
            source_files=["main.py", "utils.py"],
            config_templates=["config.yaml"],
            scripts=["install.sh"],
            dependencies=["requests>=2.25"],
            checksum="abcd1234"
        )
        
        result = manifest.to_dict()
        
        self.assertEqual(result['package_name'], "test-package")
        self.assertEqual(result['version'], "1.0.0")
        self.assertEqual(result['source_files'], ["main.py", "utils.py"])
        self.assertEqual(result['checksum'], "abcd1234")
    
    def test_from_dict(self):
        """Test manifest deserialization from dictionary"""
        data = {
            'package_name': "test-package",
            'version': "1.0.0", 
            'created_at': "2023-01-01T00:00:00",
            'source_platform': "MACOS",
            'target_platform': "raspberry-pi",
            'source_files': ["main.py"],
            'config_templates': ["config.yaml"],
            'scripts': ["install.sh"],
            'dependencies': ["requests"],
            'checksum': "abcd1234"
        }
        
        manifest = PackageManifest.from_dict(data)
        
        self.assertEqual(manifest.package_name, "test-package")
        self.assertEqual(manifest.version, "1.0.0")
        self.assertEqual(manifest.source_files, ["main.py"])
        self.assertEqual(manifest.checksum, "abcd1234")


class TestPackageConfig(unittest.TestCase):
    """Test PackageConfig functionality"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = PackageConfig()
        
        self.assertEqual(config.package_name, "gtach-app")
        self.assertEqual(config.version, "1.0.0")
        self.assertEqual(config.target_platform, "raspberry-pi")
        self.assertIn("src/obdii", config.source_dirs)
        self.assertIn("__pycache__", config.exclude_patterns)
        self.assertEqual(config.compression_level, 6)
        self.assertTrue(config.verify_integrity)
    
    def test_custom_values(self):
        """Test custom configuration values"""
        config = PackageConfig(
            package_name="custom-app",
            version="2.0.0",
            target_platform="linux",
            compression_level=9
        )
        
        self.assertEqual(config.package_name, "custom-app")
        self.assertEqual(config.version, "2.0.0")
        self.assertEqual(config.target_platform, "linux")
        self.assertEqual(config.compression_level, 9)


if __name__ == '__main__':
    unittest.main()