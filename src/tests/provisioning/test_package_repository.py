#!/usr/bin/env python3
"""
Unit tests for PackageRepository

Tests package repository functionality including:
- Repository initialization and structure
- Package storage and retrieval 
- Search and query operations
- Repository maintenance and cleanup
- Thread safety
- Cross-platform compatibility
- Error handling
"""

import os
import sys
import unittest
import tempfile
import shutil
import threading
import time
import json
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from provisioning.package_repository import (
    PackageRepository, PackageEntry, SearchQuery, RepositoryStats
)
from provisioning.package_creator import PackageManifest
from provisioning.version_manager import VersionManager, CompatibilityLevel


class TestPackageEntry(unittest.TestCase):
    """Test PackageEntry functionality"""
    
    def test_to_dict(self):
        """Test package entry serialization to dictionary"""
        entry = PackageEntry(
            name="test-package",
            version="1.0.0",
            platform="linux",
            file_path="packages/test-package/linux/test-package-1.0.0-linux.tar.gz",
            file_size=1024,
            checksum="abcd1234",
            created_at="2023-01-01T00:00:00",
            manifest={"package_name": "test-package"},
            tags=["stable", "production"]
        )
        
        result = entry.to_dict()
        
        self.assertEqual(result['name'], "test-package")
        self.assertEqual(result['version'], "1.0.0")
        self.assertEqual(result['platform'], "linux")
        self.assertEqual(result['file_size'], 1024)
        self.assertEqual(result['checksum'], "abcd1234")
        self.assertEqual(result['tags'], ["stable", "production"])
    
    def test_from_dict(self):
        """Test package entry deserialization from dictionary"""
        data = {
            'name': "test-package",
            'version': "1.0.0",
            'platform': "linux",
            'file_path': "packages/test-package/linux/test-package-1.0.0-linux.tar.gz",
            'file_size': 1024,
            'checksum': "abcd1234",
            'created_at': "2023-01-01T00:00:00",
            'manifest': {"package_name": "test-package"},
            'tags': ["stable"]
        }
        
        entry = PackageEntry.from_dict(data)
        
        self.assertEqual(entry.name, "test-package")
        self.assertEqual(entry.version, "1.0.0")
        self.assertEqual(entry.platform, "linux")
        self.assertEqual(entry.file_size, 1024)
        self.assertEqual(entry.checksum, "abcd1234")
        self.assertEqual(entry.tags, ["stable"])
    
    def test_from_dict_missing_tags(self):
        """Test package entry deserialization with missing tags field"""
        data = {
            'name': "test-package",
            'version': "1.0.0",
            'platform': "linux",
            'file_path': "packages/test-package/linux/test-package-1.0.0-linux.tar.gz",
            'file_size': 1024,
            'checksum': "abcd1234",
            'created_at': "2023-01-01T00:00:00",
            'manifest': None
            # Missing 'tags' field
        }
        
        entry = PackageEntry.from_dict(data)
        self.assertEqual(entry.tags, [])


class TestSearchQuery(unittest.TestCase):
    """Test SearchQuery functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.version_manager = VersionManager()
    
    def test_matches_name_filter(self):
        """Test search query name filtering"""
        query = SearchQuery(name="test-package")
        
        matching_entry = PackageEntry(
            name="test-package-core",
            version="1.0.0",
            platform="linux", 
            file_path="test",
            file_size=1024,
            checksum="abc",
            created_at="2023-01-01T00:00:00"
        )
        
        non_matching_entry = PackageEntry(
            name="other-package",
            version="1.0.0", 
            platform="linux",
            file_path="test",
            file_size=1024,
            checksum="abc",
            created_at="2023-01-01T00:00:00"
        )
        
        self.assertTrue(query.matches(matching_entry, self.version_manager))
        self.assertFalse(query.matches(non_matching_entry, self.version_manager))
    
    def test_matches_version_constraint(self):
        """Test search query version constraint filtering"""
        query = SearchQuery(version_constraint=">=1.0.0")
        
        matching_entry = PackageEntry(
            name="test-package",
            version="1.2.0",
            platform="linux",
            file_path="test",
            file_size=1024, 
            checksum="abc",
            created_at="2023-01-01T00:00:00"
        )
        
        non_matching_entry = PackageEntry(
            name="test-package",
            version="0.9.0",
            platform="linux",
            file_path="test",
            file_size=1024,
            checksum="abc", 
            created_at="2023-01-01T00:00:00"
        )
        
        self.assertTrue(query.matches(matching_entry, self.version_manager))
        self.assertFalse(query.matches(non_matching_entry, self.version_manager))
    
    def test_matches_platform_filter(self):
        """Test search query platform filtering"""
        query = SearchQuery(platform="linux")
        
        matching_entry = PackageEntry(
            name="test-package",
            version="1.0.0",
            platform="linux",
            file_path="test",
            file_size=1024,
            checksum="abc",
            created_at="2023-01-01T00:00:00"
        )
        
        non_matching_entry = PackageEntry(
            name="test-package",
            version="1.0.0",
            platform="windows",
            file_path="test",
            file_size=1024,
            checksum="abc",
            created_at="2023-01-01T00:00:00"
        )
        
        self.assertTrue(query.matches(matching_entry, self.version_manager))
        self.assertFalse(query.matches(non_matching_entry, self.version_manager))
    
    def test_matches_tags_filter(self):
        """Test search query tags filtering"""
        query = SearchQuery(tags=["stable", "production"])
        
        matching_entry = PackageEntry(
            name="test-package",
            version="1.0.0",
            platform="linux",
            file_path="test",
            file_size=1024,
            checksum="abc",
            created_at="2023-01-01T00:00:00",
            tags=["stable", "production", "latest"]
        )
        
        partial_matching_entry = PackageEntry(
            name="test-package", 
            version="1.0.0",
            platform="linux",
            file_path="test",
            file_size=1024,
            checksum="abc",
            created_at="2023-01-01T00:00:00",
            tags=["stable"]  # Missing "production" tag
        )
        
        self.assertTrue(query.matches(matching_entry, self.version_manager))
        self.assertFalse(query.matches(partial_matching_entry, self.version_manager))
    
    def test_matches_date_range(self):
        """Test search query date range filtering"""
        query = SearchQuery(
            created_after="2023-01-01T00:00:00",
            created_before="2023-12-31T23:59:59"
        )
        
        matching_entry = PackageEntry(
            name="test-package",
            version="1.0.0", 
            platform="linux",
            file_path="test",
            file_size=1024,
            checksum="abc",
            created_at="2023-06-15T12:00:00"
        )
        
        too_early_entry = PackageEntry(
            name="test-package",
            version="1.0.0",
            platform="linux", 
            file_path="test",
            file_size=1024,
            checksum="abc",
            created_at="2022-12-31T23:59:59"
        )
        
        too_late_entry = PackageEntry(
            name="test-package",
            version="1.0.0",
            platform="linux",
            file_path="test", 
            file_size=1024,
            checksum="abc",
            created_at="2024-01-01T00:00:00"
        )
        
        self.assertTrue(query.matches(matching_entry, self.version_manager))
        self.assertFalse(query.matches(too_early_entry, self.version_manager))
        self.assertFalse(query.matches(too_late_entry, self.version_manager))


class TestRepositoryStats(unittest.TestCase):
    """Test RepositoryStats functionality"""
    
    def test_to_dict(self):
        """Test repository stats serialization"""
        stats = RepositoryStats(
            total_packages=10,
            total_size_bytes=1048576,
            platforms=["linux", "windows"],
            package_names=["app-a", "app-b"],
            version_range=("1.0.0", "2.0.0"),
            created_at="2023-01-01T00:00:00"
        )
        
        result = stats.to_dict()
        
        self.assertEqual(result['total_packages'], 10)
        self.assertEqual(result['total_size_bytes'], 1048576)
        self.assertEqual(result['platforms'], ["linux", "windows"])
        self.assertEqual(result['package_names'], ["app-a", "app-b"])
        self.assertEqual(result['version_range'], ("1.0.0", "2.0.0"))
        self.assertEqual(result['created_at'], "2023-01-01T00:00:00")


class TestPackageRepository(unittest.TestCase):
    """Test PackageRepository functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_path = self.temp_dir / "test_repository"
        self.test_packages_dir = self.temp_dir / "test_packages"
        
        # Create test environment
        self.repo_path.mkdir(parents=True)
        self.test_packages_dir.mkdir(parents=True)
        
        # Create test package files
        self._create_test_packages()
        
        # Initialize repository
        self.repository = PackageRepository(self.repo_path)
    
    def tearDown(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_packages(self):
        """Create test package files"""
        # Create test package 1
        self.test_package_1 = self.test_packages_dir / "test-package-1.0.0.tar.gz"
        with open(self.test_package_1, 'wb') as f:
            f.write(b"test package content 1")
        
        # Create test package 2
        self.test_package_2 = self.test_packages_dir / "test-package-2.0.0.tar.gz"
        with open(self.test_package_2, 'wb') as f:
            f.write(b"test package content 2 with more data")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def test_initialization(self):
        """Test repository initialization"""
        self.assertTrue(self.repository.repository_path.exists())
        self.assertTrue(self.repository.packages_dir.exists())
        self.assertTrue(hasattr(self.repository, 'logger'))
        self.assertTrue(hasattr(self.repository, 'version_manager'))
        self.assertTrue(hasattr(self.repository, '_package_index'))
        self.assertTrue(hasattr(self.repository, '_operations_lock'))
    
    def test_default_repository_path(self):
        """Test default repository path"""
        default_repo = PackageRepository()
        expected_path = Path.home() / ".gtach" / "repository"
        self.assertEqual(default_repo.repository_path, expected_path)
    
    def test_store_package_basic(self):
        """Test basic package storage"""
        manifest = PackageManifest(
            package_name="test-package",
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            source_platform="MACOS",
            target_platform="linux"
        )
        
        entry = self.repository.store_package(
            package_file=self.test_package_1,
            name="test-package",
            version="1.0.0",
            platform="linux",
            manifest=manifest,
            tags=["stable"]
        )
        
        self.assertEqual(entry.name, "test-package")
        self.assertEqual(entry.version, "1.0.0")
        self.assertEqual(entry.platform, "linux")
        self.assertEqual(entry.tags, ["stable"])
        self.assertEqual(entry.file_size, len(b"test package content 1"))
        self.assertIsNotNone(entry.checksum)
        
        # Verify file was copied
        stored_file = self.repository.repository_path / entry.file_path
        self.assertTrue(stored_file.exists())
    
    def test_store_package_duplicate(self):
        """Test storing duplicate package raises error"""
        # Store first package
        self.repository.store_package(
            package_file=self.test_package_1,
            name="test-package",
            version="1.0.0", 
            platform="linux"
        )
        
        # Attempt to store duplicate
        with self.assertRaises(ValueError) as context:
            self.repository.store_package(
                package_file=self.test_package_1,
                name="test-package",
                version="1.0.0",
                platform="linux"
            )
        
        self.assertIn("Package already exists", str(context.exception))
    
    def test_store_package_invalid_version(self):
        """Test storing package with invalid semantic version"""
        with self.assertRaises(ValueError) as context:
            self.repository.store_package(
                package_file=self.test_package_1,
                name="test-package", 
                version="invalid.version",
                platform="linux"
            )
        
        self.assertIn("Invalid semantic version", str(context.exception))
    
    def test_store_package_missing_file(self):
        """Test storing package with missing file"""
        missing_file = self.test_packages_dir / "missing.tar.gz"
        
        with self.assertRaises(ValueError) as context:
            self.repository.store_package(
                package_file=missing_file,
                name="test-package",
                version="1.0.0",
                platform="linux"
            )
        
        self.assertIn("Package file does not exist", str(context.exception))
    
    def test_retrieve_package(self):
        """Test package retrieval"""
        # Store package first
        entry = self.repository.store_package(
            package_file=self.test_package_1,
            name="test-package",
            version="1.0.0",
            platform="linux"
        )
        
        # Retrieve package
        package_path = self.repository.retrieve_package("test-package", "1.0.0", "linux")
        
        self.assertIsNotNone(package_path)
        self.assertTrue(package_path.exists())
        self.assertEqual(package_path, self.repository.repository_path / entry.file_path)
    
    def test_retrieve_package_not_found(self):
        """Test retrieving non-existent package"""
        package_path = self.repository.retrieve_package("missing-package", "1.0.0", "linux")
        self.assertIsNone(package_path)
    
    def test_get_package_info(self):
        """Test getting package information"""
        # Store package first
        stored_entry = self.repository.store_package(
            package_file=self.test_package_1,
            name="test-package",
            version="1.0.0",
            platform="linux",
            tags=["stable"]
        )
        
        # Get package info
        info = self.repository.get_package_info("test-package", "1.0.0", "linux")
        
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "test-package")
        self.assertEqual(info.version, "1.0.0")
        self.assertEqual(info.platform, "linux")
        self.assertEqual(info.tags, ["stable"])
        self.assertEqual(info.checksum, stored_entry.checksum)
    
    def test_get_package_info_not_found(self):
        """Test getting info for non-existent package"""
        info = self.repository.get_package_info("missing-package", "1.0.0", "linux")
        self.assertIsNone(info)
    
    def test_search_packages(self):
        """Test package searching"""
        # Store test packages
        self.repository.store_package(
            self.test_package_1, "app-alpha", "1.0.0", "linux", tags=["stable"]
        )
        self.repository.store_package(
            self.test_package_2, "app-alpha", "1.1.0", "linux", tags=["beta"]
        )
        self.repository.store_package(
            self.test_package_1, "app-beta", "2.0.0", "windows", tags=["stable"]
        )
        
        # Search by name
        name_query = SearchQuery(name="app-alpha")
        name_results = self.repository.search_packages(name_query)
        self.assertEqual(len(name_results), 2)
        self.assertTrue(all("app-alpha" in r.name for r in name_results))
        
        # Search by platform
        platform_query = SearchQuery(platform="linux")
        platform_results = self.repository.search_packages(platform_query)
        self.assertEqual(len(platform_results), 2)
        self.assertTrue(all(r.platform == "linux" for r in platform_results))
        
        # Search by tags
        tag_query = SearchQuery(tags=["stable"])
        tag_results = self.repository.search_packages(tag_query)
        self.assertEqual(len(tag_results), 2)
        self.assertTrue(all("stable" in r.tags for r in tag_results))
        
        # Search by version constraint
        version_query = SearchQuery(version_constraint=">=1.1.0")
        version_results = self.repository.search_packages(version_query)
        self.assertEqual(len(version_results), 2)  # app-alpha 1.1.0 and app-beta 2.0.0
    
    def test_list_packages(self):
        """Test package listing"""
        # Store test packages
        self.repository.store_package(self.test_package_1, "app-c", "1.0.0", "linux")
        self.repository.store_package(self.test_package_2, "app-a", "2.0.0", "linux") 
        self.repository.store_package(self.test_package_1, "app-b", "1.5.0", "windows")
        
        # List all packages
        all_packages = self.repository.list_packages()
        self.assertEqual(len(all_packages), 3)
        
        # List with platform filter
        linux_packages = self.repository.list_packages(platform="linux")
        self.assertEqual(len(linux_packages), 2)
        self.assertTrue(all(p.platform == "linux" for p in linux_packages))
        
        # List sorted by name
        name_sorted = self.repository.list_packages(sort_by="name")
        names = [p.name for p in name_sorted]
        self.assertEqual(names, ["app-a", "app-b", "app-c"])
        
        # List sorted by version
        version_sorted = self.repository.list_packages(sort_by="version")
        versions = [p.version for p in version_sorted]
        self.assertEqual(versions, ["2.0.0", "1.5.0", "1.0.0"])  # Descending order
    
    def test_delete_package(self):
        """Test package deletion"""
        # Store package first
        self.repository.store_package(
            self.test_package_1, "test-package", "1.0.0", "linux"
        )
        
        # Verify package exists
        self.assertIsNotNone(self.repository.get_package_info("test-package", "1.0.0", "linux"))
        
        # Delete package
        deleted = self.repository.delete_package("test-package", "1.0.0", "linux")
        self.assertTrue(deleted)
        
        # Verify package no longer exists
        self.assertIsNone(self.repository.get_package_info("test-package", "1.0.0", "linux"))
        self.assertIsNone(self.repository.retrieve_package("test-package", "1.0.0", "linux"))
    
    def test_delete_package_not_found(self):
        """Test deleting non-existent package"""
        deleted = self.repository.delete_package("missing-package", "1.0.0", "linux")
        self.assertFalse(deleted)
    
    def test_find_compatible_versions(self):
        """Test finding compatible versions"""
        # Store multiple versions
        self.repository.store_package(self.test_package_1, "test-app", "1.0.0", "linux")
        self.repository.store_package(self.test_package_1, "test-app", "1.0.5", "linux")
        self.repository.store_package(self.test_package_1, "test-app", "1.1.0", "linux")
        self.repository.store_package(self.test_package_1, "test-app", "2.0.0", "linux")
        self.repository.store_package(self.test_package_1, "test-app", "1.1.0", "windows")  # Different platform
        
        # Find compatible versions
        compatible = self.repository.find_compatible_versions(
            name="test-app",
            target_version="1.0.0", 
            platform="linux"
        )
        
        # Should find versions >= 1.0.0 for linux platform
        self.assertGreater(len(compatible), 0)
        compatible_versions = [entry.version for entry in compatible]
        
        # Verify all are >= 1.0.0 and on linux platform
        for entry in compatible:
            self.assertEqual(entry.platform, "linux")
            self.assertGreaterEqual(
                self.repository.version_manager.parse_version(entry.version),
                self.repository.version_manager.parse_version("1.0.0")
            )
    
    def test_get_latest_version(self):
        """Test getting latest version of package"""
        # Store multiple versions
        self.repository.store_package(self.test_package_1, "test-app", "1.0.0", "linux")
        self.repository.store_package(self.test_package_1, "test-app", "1.2.0", "linux") 
        self.repository.store_package(self.test_package_1, "test-app", "2.0.0-alpha", "linux")
        self.repository.store_package(self.test_package_1, "test-app", "1.1.0", "linux")
        
        # Get latest stable version
        latest = self.repository.get_latest_version("test-app", "linux")
        self.assertIsNotNone(latest)
        self.assertEqual(latest.version, "1.2.0")
        
        # Get latest including prerelease
        latest_pre = self.repository.get_latest_version("test-app", "linux", include_prerelease=True)
        self.assertIsNotNone(latest_pre)
        self.assertEqual(latest_pre.version, "2.0.0-alpha")
    
    def test_get_latest_version_not_found(self):
        """Test getting latest version for non-existent package"""
        latest = self.repository.get_latest_version("missing-app", "linux")
        self.assertIsNone(latest)
    
    def test_cleanup_repository_dry_run(self):
        """Test repository cleanup dry run"""
        # Store a package first
        self.repository.store_package(self.test_package_1, "test-app", "1.0.0", "linux")
        
        # Create orphaned file
        orphaned_file = self.repository.packages_dir / "orphaned.tar.gz" 
        orphaned_file.parent.mkdir(parents=True, exist_ok=True)
        orphaned_file.write_text("orphaned content")
        
        # Run dry run cleanup
        stats = self.repository.cleanup_repository(dry_run=True)
        
        self.assertIn('orphaned_files', stats)
        self.assertIn('missing_files', stats)
        self.assertIn('corrupted_files', stats)
        self.assertEqual(stats['orphaned_files'], 1)
        
        # Verify orphaned file still exists (dry run)
        self.assertTrue(orphaned_file.exists())
    
    def test_cleanup_repository_actual(self):
        """Test actual repository cleanup"""
        # Store a package first  
        entry = self.repository.store_package(self.test_package_1, "test-app", "1.0.0", "linux")
        
        # Create orphaned file
        orphaned_file = self.repository.packages_dir / "orphaned.tar.gz"
        orphaned_file.write_text("orphaned content")
        
        # Delete actual package file to simulate missing file
        package_file = self.repository.repository_path / entry.file_path
        package_file.unlink()
        
        # Run actual cleanup
        stats = self.repository.cleanup_repository(dry_run=False)
        
        self.assertEqual(stats['orphaned_files'], 1)
        self.assertEqual(stats['missing_files'], 1)
        
        # Verify orphaned file was removed
        self.assertFalse(orphaned_file.exists())
        
        # Verify missing entry was removed from index
        self.assertIsNone(self.repository.get_package_info("test-app", "1.0.0", "linux"))
    
    def test_get_stats(self):
        """Test repository statistics"""
        # Store some packages
        self.repository.store_package(self.test_package_1, "app-a", "1.0.0", "linux")
        self.repository.store_package(self.test_package_2, "app-b", "2.0.0", "windows")
        
        stats = self.repository.get_stats()
        
        self.assertEqual(stats.total_packages, 2)
        self.assertGreater(stats.total_size_bytes, 0)
        self.assertEqual(set(stats.platforms), {"linux", "windows"})
        self.assertEqual(set(stats.package_names), {"app-a", "app-b"})
        self.assertEqual(stats.version_range, ("1.0.0", "2.0.0"))
        self.assertIsNotNone(stats.created_at)
    
    def test_get_operation_stats(self):
        """Test operation statistics"""
        # Perform some operations
        self.repository.store_package(self.test_package_1, "test-app", "1.0.0", "linux")
        self.repository.search_packages(SearchQuery(name="test-app"))
        
        stats = self.repository.get_operation_stats()
        
        self.assertIn('operation_count', stats)
        self.assertIn('repository_path', stats)
        self.assertIn('packages_loaded', stats)
        self.assertIn('version_manager_stats', stats)
        self.assertGreaterEqual(stats['operation_count'], 2)
        self.assertEqual(stats['packages_loaded'], 1)
    
    def test_thread_safety(self):
        """Test thread-safe repository operations"""
        results = []
        errors = []
        
        def store_package_thread(thread_id):
            try:
                # Create unique test package for each thread
                test_package = self.test_packages_dir / f"thread-{thread_id}.tar.gz"
                test_package.write_bytes(f"thread {thread_id} content".encode())
                
                entry = self.repository.store_package(
                    package_file=test_package,
                    name=f"thread-app-{thread_id}",
                    version="1.0.0",
                    platform="linux"
                )
                results.append((thread_id, entry))
                
            except Exception as e:
                errors.append((thread_id, e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=store_package_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)
        
        # Verify all packages were stored
        for thread_id, entry in results:
            self.assertEqual(entry.name, f"thread-app-{thread_id}")
            info = self.repository.get_package_info(f"thread-app-{thread_id}", "1.0.0", "linux")
            self.assertIsNotNone(info)
    
    def test_index_persistence(self):
        """Test package index persistence across repository instances"""
        # Store package in first repository instance
        self.repository.store_package(
            self.test_package_1, "persistent-app", "1.0.0", "linux"
        )
        
        # Create new repository instance with same path
        new_repository = PackageRepository(self.repo_path)
        
        # Verify package is still available
        info = new_repository.get_package_info("persistent-app", "1.0.0", "linux")
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "persistent-app")
        self.assertEqual(info.version, "1.0.0")
        self.assertEqual(info.platform, "linux")
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test invalid repository path permissions (if possible to simulate)
        # This test may be skipped on some systems
        try:
            invalid_repo_path = Path("/root/invalid_repository")  # Likely no write access
            with self.assertRaises(RuntimeError):
                PackageRepository(invalid_repo_path)
        except (PermissionError, FileNotFoundError):
            # Skip test if we can't create the scenario
            self.skipTest("Cannot simulate permission error on this system")
        
        # Test corrupted index file
        index_file = self.repository.index_file
        with open(index_file, 'w') as f:
            f.write("invalid json content")
        
        # Repository should handle corrupted index gracefully
        new_repo = PackageRepository(self.repo_path)
        self.assertEqual(len(new_repo._package_index), 0)


if __name__ == '__main__':
    unittest.main()