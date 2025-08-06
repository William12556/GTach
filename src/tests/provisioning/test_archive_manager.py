#!/usr/bin/env python3
"""
Unit tests for ArchiveManager

Tests archive management functionality including:
- Archive creation (tar.gz, tar.bz2, zip)
- Archive extraction
- Integrity verification
- Metadata management
- Thread safety
- Error handling
"""

import os
import sys
import unittest
import tempfile
import shutil
import tarfile
import zipfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from provisioning.archive_manager import (
    ArchiveManager, ArchiveMetadata, ArchiveConfig, CompressionFormat
)


class TestArchiveManager(unittest.TestCase):
    """Test ArchiveManager functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.source_dir = self.temp_dir / "source"
        self.archive_dir = self.temp_dir / "archives"
        self.extract_dir = self.temp_dir / "extract"
        
        # Create directories
        self.source_dir.mkdir(parents=True)
        self.archive_dir.mkdir(parents=True)
        self.extract_dir.mkdir(parents=True)
        
        # Create test files
        self._create_test_files()
        
        # Initialize ArchiveManager
        self.manager = ArchiveManager()
    
    def tearDown(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_files(self):
        """Create test files for archiving"""
        test_files = [
            "main.py",
            "utils.py",
            "config/settings.yaml",
            "data/test.txt",
            "scripts/install.sh"
        ]
        
        for file_path in test_files:
            full_path = self.source_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write test content
            if file_path.endswith('.py'):
                content = f'"""Test module: {file_path}"""\nprint("Test content")\n'
            elif file_path.endswith('.yaml'):
                content = 'test_setting: true\nvalue: 123\n'
            elif file_path.endswith('.sh'):
                content = '#!/bin/bash\necho "Test script"\n'
            else:
                content = f'Test content for {file_path}\n'
            
            full_path.write_text(content)
    
    def test_initialization(self):
        """Test ArchiveManager initialization"""
        self.assertTrue(hasattr(self.manager, 'logger'))
        self.assertTrue(hasattr(self.manager, 'platform'))
        self.assertEqual(self.manager._operation_count, 0)
    
    def test_compression_format_from_extension(self):
        """Test compression format detection from filename"""
        test_cases = [
            ("archive.tar.gz", CompressionFormat.TAR_GZ),
            ("archive.tgz", CompressionFormat.TAR_GZ),
            ("archive.tar.bz2", CompressionFormat.TAR_BZ2),
            ("archive.tbz2", CompressionFormat.TAR_BZ2),
            ("archive.zip", CompressionFormat.ZIP),
            ("archive.unknown", CompressionFormat.TAR_GZ),  # Default
        ]
        
        for filename, expected_format in test_cases:
            result = CompressionFormat.from_extension(filename)
            self.assertEqual(result, expected_format, f"Failed for {filename}")
    
    def test_collect_files(self):
        """Test file collection with exclusion patterns"""
        config = ArchiveConfig(
            exclude_patterns=['.DS_Store', '*.pyc'],
            max_file_size=1024 * 1024  # 1MB
        )
        
        files = self.manager._collect_files(self.source_dir, config)
        
        # Should collect all test files
        file_names = [f.name for f in files]
        self.assertIn("main.py", file_names)
        self.assertIn("utils.py", file_names)
        self.assertIn("settings.yaml", file_names)
        self.assertIn("test.txt", file_names)
        self.assertIn("install.sh", file_names)
    
    def test_should_exclude_file(self):
        """Test file exclusion logic"""
        exclude_patterns = ['.DS_Store', '*.pyc', '__pycache__']
        
        test_cases = [
            (Path("file.py"), False),
            (Path("file.pyc"), True),
            (Path(".DS_Store"), True),
            (Path("some/__pycache__/file.py"), True),
            (Path("normal_file.txt"), False)
        ]
        
        for file_path, should_exclude in test_cases:
            result = self.manager._should_exclude_file(file_path, exclude_patterns)
            self.assertEqual(result, should_exclude, f"Failed for {file_path}")
    
    def test_create_tar_gz_archive(self):
        """Test tar.gz archive creation"""
        archive_path = self.archive_dir / "test.tar.gz"
        config = ArchiveConfig(compression_level=6)
        
        metadata = self.manager.create_archive(
            self.source_dir, archive_path, config
        )
        
        # Check archive was created
        self.assertTrue(archive_path.exists())
        self.assertTrue(tarfile.is_tarfile(archive_path))
        
        # Check metadata
        self.assertEqual(metadata.filename, "test.tar.gz")
        self.assertEqual(metadata.format, CompressionFormat.TAR_GZ)
        self.assertGreater(metadata.file_count, 0)
        self.assertGreater(metadata.uncompressed_size, 0)
        self.assertGreater(metadata.compressed_size, 0)
        self.assertTrue(len(metadata.files) > 0)
    
    def test_create_tar_bz2_archive(self):
        """Test tar.bz2 archive creation"""
        archive_path = self.archive_dir / "test.tar.bz2"
        config = ArchiveConfig()
        
        metadata = self.manager.create_archive(
            self.source_dir, archive_path, config
        )
        
        self.assertTrue(archive_path.exists())
        self.assertTrue(tarfile.is_tarfile(archive_path))
        self.assertEqual(metadata.format, CompressionFormat.TAR_BZ2)
    
    def test_create_zip_archive(self):
        """Test ZIP archive creation"""
        archive_path = self.archive_dir / "test.zip"
        config = ArchiveConfig()
        
        metadata = self.manager.create_archive(
            self.source_dir, archive_path, config
        )
        
        self.assertTrue(archive_path.exists())
        self.assertTrue(zipfile.is_zipfile(archive_path))
        self.assertEqual(metadata.format, CompressionFormat.ZIP)
    
    def test_create_archive_with_checksums(self):
        """Test archive creation with checksum calculation"""
        archive_path = self.archive_dir / "test.tar.gz"
        config = ArchiveConfig(create_checksums=True)
        
        metadata = self.manager.create_archive(
            self.source_dir, archive_path, config
        )
        
        # Check checksums were calculated
        self.assertIsNotNone(metadata.checksum_sha256)
        self.assertIsNotNone(metadata.checksum_md5)
        self.assertEqual(len(metadata.checksum_sha256), 64)  # SHA256 hex length
        self.assertEqual(len(metadata.checksum_md5), 32)    # MD5 hex length
    
    def test_create_archive_with_metadata_file(self):
        """Test archive creation with metadata file"""
        archive_path = self.archive_dir / "test.tar.gz"
        config = ArchiveConfig(include_metadata=True)
        
        metadata = self.manager.create_archive(
            self.source_dir, archive_path, config
        )
        
        # Check metadata file was created
        metadata_path = archive_path.with_suffix(archive_path.suffix + '.meta')
        self.assertTrue(metadata_path.exists())
        
        # Load and verify metadata
        loaded_metadata = self.manager._load_metadata(archive_path)
        self.assertIsNotNone(loaded_metadata)
        self.assertEqual(loaded_metadata.filename, metadata.filename)
        self.assertEqual(loaded_metadata.file_count, metadata.file_count)
    
    def test_extract_tar_archive(self):
        """Test tar archive extraction"""
        # Create archive first
        archive_path = self.archive_dir / "test.tar.gz"
        self.manager.create_archive(self.source_dir, archive_path)
        
        # Extract archive
        metadata = self.manager.extract_archive(
            archive_path, self.extract_dir, verify_integrity=False
        )
        
        # Check files were extracted
        self.assertTrue((self.extract_dir / "main.py").exists())
        self.assertTrue((self.extract_dir / "utils.py").exists())
        self.assertTrue((self.extract_dir / "config" / "settings.yaml").exists())
        
        # Check metadata
        self.assertGreater(metadata.file_count, 0)
        self.assertTrue(len(metadata.files) > 0)
    
    def test_extract_zip_archive(self):
        """Test ZIP archive extraction"""
        # Create ZIP archive first
        archive_path = self.archive_dir / "test.zip"
        self.manager.create_archive(self.source_dir, archive_path)
        
        # Extract archive
        metadata = self.manager.extract_archive(archive_path, self.extract_dir)
        
        # Check files were extracted
        self.assertTrue((self.extract_dir / "main.py").exists())
        self.assertTrue((self.extract_dir / "config" / "settings.yaml").exists())
    
    def test_verify_tar_integrity(self):
        """Test tar archive integrity verification"""
        # Create valid archive
        archive_path = self.archive_dir / "test.tar.gz"
        self.manager.create_archive(self.source_dir, archive_path)
        
        # Verify integrity
        is_valid = self.manager.verify_archive_integrity(archive_path)
        self.assertTrue(is_valid)
        
        # Create corrupted archive
        corrupted_path = self.archive_dir / "corrupted.tar.gz"
        with open(corrupted_path, 'wb') as f:
            f.write(b'corrupted data')
        
        # Should fail verification
        is_valid = self.manager.verify_archive_integrity(corrupted_path)
        self.assertFalse(is_valid)
    
    def test_verify_zip_integrity(self):
        """Test ZIP archive integrity verification"""
        # Create valid ZIP archive
        archive_path = self.archive_dir / "test.zip"
        self.manager.create_archive(self.source_dir, archive_path)
        
        # Verify integrity
        is_valid = self.manager.verify_archive_integrity(archive_path)
        self.assertTrue(is_valid)
    
    def test_is_safe_path(self):
        """Test path safety checks for extraction"""
        safe_paths = [
            "normal/file.txt",
            "dir/subdir/file.txt",
            "file.txt"
        ]
        
        unsafe_paths = [
            "/absolute/path/file.txt",
            "../parent/file.txt",
            "dir/../../../etc/passwd",
            "dir\\..\\..\\windows\\system32"
        ]
        
        for path in safe_paths:
            self.assertTrue(self.manager._is_safe_path(path), f"Safe path rejected: {path}")
        
        for path in unsafe_paths:
            self.assertFalse(self.manager._is_safe_path(path), f"Unsafe path accepted: {path}")
    
    def test_progress_callback(self):
        """Test progress callback during archive operations"""
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        config = ArchiveConfig(progress_callback=progress_callback)
        archive_path = self.archive_dir / "test.tar.gz"
        
        self.manager.create_archive(self.source_dir, archive_path, config)
        
        # Should have received progress callbacks
        self.assertTrue(len(progress_calls) > 0)
        
        # Check callback format
        for current, total in progress_calls:
            self.assertIsInstance(current, int)
            self.assertIsInstance(total, int)
            self.assertLessEqual(current, total)
    
    def test_thread_safety(self):
        """Test thread-safe archive operations"""
        results = []
        errors = []
        
        def create_archive_thread(thread_id):
            try:
                archive_path = self.archive_dir / f"test_{thread_id}.tar.gz"
                metadata = self.manager.create_archive(self.source_dir, archive_path)
                results.append((thread_id, metadata))
            except Exception as e:
                errors.append((thread_id, e))
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_archive_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 3)
        
        # Verify all archives were created
        for thread_id, metadata in results:
            archive_path = self.archive_dir / f"test_{thread_id}.tar.gz"
            self.assertTrue(archive_path.exists())
            self.assertGreater(metadata.file_count, 0)
    
    def test_error_handling(self):
        """Test error handling for invalid operations"""
        # Test with non-existent source directory
        with self.assertRaises(RuntimeError):
            self.manager.create_archive(
                Path("/nonexistent"), self.archive_dir / "test.tar.gz"
            )
        
        # Test extraction of non-existent archive
        with self.assertRaises(RuntimeError):
            self.manager.extract_archive(
                Path("/nonexistent.tar.gz"), self.extract_dir
            )
        
        # Test integrity verification of non-existent archive
        with self.assertRaises(RuntimeError):
            self.manager.verify_archive_integrity(Path("/nonexistent.tar.gz"))
    
    def test_get_stats(self):
        """Test statistics collection"""
        # Create some archives to generate stats
        archive_path = self.archive_dir / "test.tar.gz"
        self.manager.create_archive(self.source_dir, archive_path)
        
        stats = self.manager.get_stats()
        
        self.assertIn('operation_count', stats)
        self.assertIn('bytes_processed', stats)
        self.assertIn('archives_created', stats)
        self.assertIn('archives_extracted', stats)
        self.assertIn('platform', stats)
        
        self.assertGreater(stats['operation_count'], 0)
        self.assertGreater(stats['archives_created'], 0)


class TestArchiveMetadata(unittest.TestCase):
    """Test ArchiveMetadata functionality"""
    
    def test_to_dict(self):
        """Test metadata serialization to dictionary"""
        metadata = ArchiveMetadata(
            filename="test.tar.gz",
            format=CompressionFormat.TAR_GZ,
            created_at="2023-01-01T00:00:00",
            file_count=5,
            uncompressed_size=1024,
            compressed_size=512,
            checksum_sha256="abcd1234",
            files=["file1.txt", "file2.py"]
        )
        
        result = metadata.to_dict()
        
        self.assertEqual(result['filename'], "test.tar.gz")
        self.assertEqual(result['format'], "TAR_GZ")
        self.assertEqual(result['file_count'], 5)
        self.assertEqual(result['checksum_sha256'], "abcd1234")
        self.assertEqual(result['files'], ["file1.txt", "file2.py"])
    
    def test_from_dict(self):
        """Test metadata deserialization from dictionary"""
        data = {
            'filename': "test.tar.gz",
            'format': "TAR_GZ",
            'created_at': "2023-01-01T00:00:00",
            'file_count': 5,
            'uncompressed_size': 1024,
            'compressed_size': 512,
            'checksum_sha256': "abcd1234",
            'files': ["file1.txt", "file2.py"]
        }
        
        metadata = ArchiveMetadata.from_dict(data)
        
        self.assertEqual(metadata.filename, "test.tar.gz")
        self.assertEqual(metadata.format, CompressionFormat.TAR_GZ)
        self.assertEqual(metadata.file_count, 5)
        self.assertEqual(metadata.checksum_sha256, "abcd1234")
        self.assertEqual(metadata.files, ["file1.txt", "file2.py"])


class TestArchiveConfig(unittest.TestCase):
    """Test ArchiveConfig functionality"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = ArchiveConfig()
        
        self.assertEqual(config.compression_level, 6)
        self.assertTrue(config.preserve_permissions)
        self.assertTrue(config.preserve_timestamps)
        self.assertFalse(config.follow_symlinks)
        self.assertTrue(config.create_checksums)
        self.assertTrue(config.include_metadata)
        self.assertIsNone(config.progress_callback)
        self.assertIn('.DS_Store', config.exclude_patterns)
        self.assertEqual(config.max_file_size, 100 * 1024 * 1024)
    
    def test_custom_values(self):
        """Test custom configuration values"""
        callback = lambda current, total: None
        
        config = ArchiveConfig(
            compression_level=9,
            preserve_permissions=False,
            create_checksums=False,
            progress_callback=callback,
            max_file_size=50 * 1024 * 1024
        )
        
        self.assertEqual(config.compression_level, 9)
        self.assertFalse(config.preserve_permissions)
        self.assertFalse(config.create_checksums)
        self.assertEqual(config.progress_callback, callback)
        self.assertEqual(config.max_file_size, 50 * 1024 * 1024)


if __name__ == '__main__':
    unittest.main()