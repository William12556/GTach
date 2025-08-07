#!/usr/bin/env python3
"""
Unit tests for VersionManager

Tests semantic versioning functionality including:
- Version parsing and validation
- Version comparison operators
- Compatibility checking
- Dependency resolution
- Thread safety
- Constraint handling
- Range validation
"""

import os
import sys
import unittest
import threading
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from provisioning.version_manager import (
    Version, VersionManager, VersionConstraint, VersionType, CompatibilityLevel
)


class TestVersion(unittest.TestCase):
    """Test Version class functionality"""
    
    def test_valid_version_parsing(self):
        """Test parsing of valid semantic versions"""
        test_cases = [
            ("1.0.0", (1, 0, 0, "", "")),
            ("0.0.1", (0, 0, 1, "", "")),
            ("10.20.30", (10, 20, 30, "", "")),
            ("1.1.2-prerelease", (1, 1, 2, "prerelease", "")),
            ("1.1.2+meta", (1, 1, 2, "", "meta")),
            ("1.1.2-prerelease+meta", (1, 1, 2, "prerelease", "meta")),
            ("1.0.0-alpha", (1, 0, 0, "alpha", "")),
            ("1.0.0-beta.1", (1, 0, 0, "beta.1", "")),
            ("1.0.0-0.3.7", (1, 0, 0, "0.3.7", "")),
            ("1.0.0-x.7.z.92", (1, 0, 0, "x.7.z.92", "")),
            ("1.0.0+20130313144700", (1, 0, 0, "", "20130313144700")),
            ("1.0.0-beta+exp.sha.5114f85", (1, 0, 0, "beta", "exp.sha.5114f85"))
        ]
        
        for version_str, expected in test_cases:
            with self.subTest(version=version_str):
                version = Version(version_str)
                self.assertEqual(version.major, expected[0])
                self.assertEqual(version.minor, expected[1])
                self.assertEqual(version.patch, expected[2])
                self.assertEqual(version.prerelease, expected[3])
                self.assertEqual(version.build_metadata, expected[4])
                self.assertEqual(str(version), version_str)
    
    def test_invalid_version_parsing(self):
        """Test parsing of invalid semantic versions"""
        invalid_versions = [
            "1",
            "1.2",
            "1.2.3-",
            "1.2.3+",
            "1.2.3-+",
            "1.2.31.2.3----RC-SNAPSHOT.12.09.1--..12+788",
            "1.2.3----RC-SNAPSHOT.12.09.1-.12+788",
            "1.2-SNAPSHOT-123",
            "1.2.31.2.3----RC-SNAPSHOT.12.09.1-.12+788",
            "1.2.3.DEV.SNAPSHOT",
            "1.2-SNAPSHOT-123",
            "1.2.3.DEV",
            "1.2-SNAPSHOT-123",
            "",
            "   ",
            "1.2.3.4",
            "01.2.3",  # Leading zeros not allowed
            "1.02.3",
            "1.2.03"
        ]
        
        for version_str in invalid_versions:
            with self.subTest(version=version_str):
                with self.assertRaises(ValueError):
                    Version(version_str)
    
    def test_version_equality(self):
        """Test version equality comparison"""
        test_cases = [
            ("1.0.0", "1.0.0", True),
            ("1.0.0", "2.0.0", False),
            ("1.0.0", "1.1.0", False),
            ("1.0.0", "1.0.1", False),
            ("1.0.0-alpha", "1.0.0-alpha", True),
            ("1.0.0-alpha", "1.0.0-beta", False),
            ("1.0.0+build1", "1.0.0+build2", True),  # Build metadata ignored
            ("1.0.0-alpha+build1", "1.0.0-alpha+build2", True)  # Build metadata ignored
        ]
        
        for version1_str, version2_str, expected in test_cases:
            with self.subTest(v1=version1_str, v2=version2_str):
                version1 = Version(version1_str)
                version2 = Version(version2_str)
                self.assertEqual(version1 == version2, expected)
                self.assertEqual(version2 == version1, expected)
    
    def test_version_ordering(self):
        """Test version ordering according to SemVer precedence"""
        # Test cases: (version1, version2, version1 < version2)
        test_cases = [
            ("1.0.0", "2.0.0", True),
            ("2.0.0", "2.1.0", True),
            ("2.1.0", "2.1.1", True),
            ("1.0.0-alpha", "1.0.0", True),
            ("1.0.0-alpha", "1.0.0-alpha.1", True),
            ("1.0.0-alpha.1", "1.0.0-alpha.beta", True),
            ("1.0.0-alpha.beta", "1.0.0-beta", True),
            ("1.0.0-beta", "1.0.0-beta.2", True),
            ("1.0.0-beta.2", "1.0.0-beta.11", True),
            ("1.0.0-beta.11", "1.0.0-rc.1", True),
            ("1.0.0-rc.1", "1.0.0", True),
            ("1.0.0-alpha", "1.0.0-beta", True),
            ("1.0.0-1", "1.0.0-2", True),
            ("2.0.0", "1.0.0", False),
            ("1.0.0", "1.0.0", False)
        ]
        
        for version1_str, version2_str, expected in test_cases:
            with self.subTest(v1=version1_str, v2=version2_str):
                version1 = Version(version1_str)
                version2 = Version(version2_str)
                self.assertEqual(version1 < version2, expected)
                
                # Test other comparison operators
                if expected:
                    self.assertTrue(version1 <= version2)
                    self.assertFalse(version1 > version2)
                    self.assertFalse(version1 >= version2)
                    self.assertFalse(version1 == version2)
                    self.assertTrue(version1 != version2)
    
    def test_version_properties(self):
        """Test version property accessors"""
        stable_version = Version("1.2.3")
        self.assertTrue(stable_version.is_stable)
        self.assertFalse(stable_version.is_prerelease)
        self.assertEqual(stable_version.version_type, VersionType.STABLE)
        
        prerelease_version = Version("1.2.3-alpha")
        self.assertFalse(prerelease_version.is_stable)
        self.assertTrue(prerelease_version.is_prerelease)
        self.assertEqual(prerelease_version.version_type, VersionType.PRE_RELEASE)
        
        build_version = Version("1.2.3+build1")
        self.assertTrue(build_version.is_stable)  # Build metadata doesn't affect stability
        self.assertFalse(build_version.is_prerelease)
        self.assertEqual(build_version.version_type, VersionType.BUILD)
    
    def test_version_bumping(self):
        """Test version bumping methods"""
        version = Version("1.2.3")
        
        major_bump = version.bump_major()
        self.assertEqual(str(major_bump), "2.0.0")
        
        minor_bump = version.bump_minor()
        self.assertEqual(str(minor_bump), "1.3.0")
        
        patch_bump = version.bump_patch()
        self.assertEqual(str(patch_bump), "1.2.4")
        
        # Original version unchanged
        self.assertEqual(str(version), "1.2.3")
    
    def test_compatibility_levels(self):
        """Test version compatibility level determination"""
        base_version = Version("1.2.3")
        
        # Same version
        same = Version("1.2.3")
        self.assertEqual(base_version.get_compatibility_level(same), CompatibilityLevel.COMPATIBLE)
        
        # Patch level change
        patch_change = Version("1.2.4")
        self.assertEqual(base_version.get_compatibility_level(patch_change), CompatibilityLevel.COMPATIBLE)
        
        # Minor level change
        minor_change = Version("1.3.0")
        self.assertEqual(base_version.get_compatibility_level(minor_change), CompatibilityLevel.MINOR_BREAKING)
        
        # Major level change
        major_change = Version("2.0.0")
        self.assertEqual(base_version.get_compatibility_level(major_change), CompatibilityLevel.MAJOR_BREAKING)
        
        # Pre-release change
        prerelease_change = Version("1.2.3-alpha")
        self.assertEqual(base_version.get_compatibility_level(prerelease_change), CompatibilityLevel.COMPATIBLE)
    
    def test_version_hash(self):
        """Test version hashing for use in sets and dicts"""
        version1 = Version("1.0.0")
        version2 = Version("1.0.0")
        version3 = Version("1.0.0+build")  # Different build metadata
        version4 = Version("1.0.1")
        
        # Equal versions should have same hash
        self.assertEqual(hash(version1), hash(version2))
        
        # Build metadata shouldn't affect hash (consistent with equality)
        self.assertEqual(hash(version1), hash(version3))
        
        # Different versions should have different hashes (usually)
        self.assertNotEqual(hash(version1), hash(version4))
        
        # Test in set
        version_set = {version1, version2, version3, version4}
        self.assertEqual(len(version_set), 2)  # version1, version2, version3 are same


class TestVersionConstraint(unittest.TestCase):
    """Test VersionConstraint functionality"""
    
    def test_constraint_matching(self):
        """Test version constraint matching"""
        test_cases = [
            # (operator, constraint_version, test_version, should_match)
            (">=", "1.0.0", "1.0.0", True),
            (">=", "1.0.0", "1.0.1", True),
            (">=", "1.0.0", "0.9.9", False),
            ("<=", "2.0.0", "1.9.9", True),
            ("<=", "2.0.0", "2.0.0", True),
            ("<=", "2.0.0", "2.0.1", False),
            ("==", "1.2.3", "1.2.3", True),
            ("==", "1.2.3", "1.2.4", False),
            ("!=", "1.2.3", "1.2.4", True),
            ("!=", "1.2.3", "1.2.3", False),
            ("~", "1.2.3", "1.2.3", True),  # Compatible within patch
            ("~", "1.2.3", "1.2.4", True),
            ("~", "1.2.3", "1.3.0", False),
            ("^", "1.2.3", "1.2.3", True),  # Compatible within minor
            ("^", "1.2.3", "1.3.0", True),
            ("^", "1.2.3", "2.0.0", False)
        ]
        
        for operator, constraint_version_str, test_version_str, expected in test_cases:
            with self.subTest(op=operator, constraint=constraint_version_str, version=test_version_str):
                constraint = VersionConstraint(operator, Version(constraint_version_str))
                test_version = Version(test_version_str)
                self.assertEqual(constraint.matches(test_version), expected)
    
    def test_invalid_constraint_operator(self):
        """Test invalid constraint operator handling"""
        constraint = VersionConstraint(">>", Version("1.0.0"))  # Invalid operator
        
        with self.assertRaises(ValueError):
            constraint.matches(Version("1.0.0"))


class TestVersionManager(unittest.TestCase):
    """Test VersionManager functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.manager = VersionManager()
    
    def test_initialization(self):
        """Test VersionManager initialization"""
        self.assertTrue(hasattr(self.manager, 'logger'))
        self.assertTrue(hasattr(self.manager, '_version_cache'))
        self.assertTrue(hasattr(self.manager, '_operations_lock'))
    
    def test_parse_version_caching(self):
        """Test version parsing with caching"""
        version_str = "1.2.3"
        
        # First parse
        version1 = self.manager.parse_version(version_str)
        self.assertEqual(str(version1), version_str)
        
        # Second parse should return cached version
        version2 = self.manager.parse_version(version_str)
        self.assertIs(version1, version2)  # Same object reference
        
        # Invalid version should raise error
        with self.assertRaises(ValueError):
            self.manager.parse_version("invalid.version")
    
    def test_parse_constraint(self):
        """Test constraint parsing"""
        test_cases = [
            (">=1.0.0", ">=", "1.0.0"),
            ("~2.1.0", "~", "2.1.0"),
            ("^3.0.0", "^", "3.0.0"),
            ("1.2.3", "==", "1.2.3"),  # Default to exact match
            ("  <=  4.5.6  ", "<=", "4.5.6")  # Whitespace handling
        ]
        
        for constraint_str, expected_op, expected_version in test_cases:
            with self.subTest(constraint=constraint_str):
                constraint = self.manager.parse_constraint(constraint_str)
                self.assertEqual(constraint.operator, expected_op)
                self.assertEqual(str(constraint.version), expected_version)
        
        # Test invalid constraint
        with self.assertRaises(ValueError):
            self.manager.parse_constraint(">=")  # Missing version
    
    def test_check_compatibility(self):
        """Test compatibility checking"""
        test_cases = [
            ("1.0.0", "1.0.1", CompatibilityLevel.COMPATIBLE),
            ("1.0.0", "1.1.0", CompatibilityLevel.MINOR_BREAKING),
            ("1.0.0", "2.0.0", CompatibilityLevel.MAJOR_BREAKING),
            ("1.2.3", "1.2.3", CompatibilityLevel.COMPATIBLE)
        ]
        
        for version1_str, version2_str, expected in test_cases:
            with self.subTest(v1=version1_str, v2=version2_str):
                result = self.manager.check_compatibility(version1_str, version2_str)
                self.assertEqual(result, expected)
                
                # Test with Version objects
                version1 = Version(version1_str)
                version2 = Version(version2_str)
                result2 = self.manager.check_compatibility(version1, version2)
                self.assertEqual(result2, expected)
    
    def test_find_compatible_versions(self):
        """Test finding compatible versions"""
        target = "1.2.0"
        available = ["1.1.0", "1.2.0", "1.2.1", "1.3.0", "2.0.0"]
        
        # Without constraint
        compatible = self.manager.find_compatible_versions(target, available)
        compatible_strs = [str(v) for v in compatible]
        
        # Should include patch and minor compatible versions, sorted desc
        expected = ["1.3.0", "1.2.1", "1.2.0"]
        self.assertEqual(compatible_strs, expected)
        
        # With constraint
        compatible_constrained = self.manager.find_compatible_versions(
            target, available, "^1.2.0"
        )
        compatible_constrained_strs = [str(v) for v in compatible_constrained]
        expected_constrained = ["1.3.0", "1.2.1", "1.2.0"]
        self.assertEqual(compatible_constrained_strs, expected_constrained)
        
        # With stricter constraint
        compatible_strict = self.manager.find_compatible_versions(
            target, available, "~1.2.0"
        )
        compatible_strict_strs = [str(v) for v in compatible_strict]
        expected_strict = ["1.2.1", "1.2.0"]
        self.assertEqual(compatible_strict_strs, expected_strict)
    
    def test_resolve_dependencies(self):
        """Test dependency resolution"""
        dependencies = {
            "package-a": ">=1.0.0",
            "package-b": "^2.1.0",
            "package-c": "~3.0.5"
        }
        
        resolved = self.manager.resolve_dependencies(dependencies)
        
        self.assertEqual(len(resolved), 3)
        self.assertIn("package-a", resolved)
        self.assertIn("package-b", resolved)
        self.assertIn("package-c", resolved)
        
        # Check resolved versions match constraints
        self.assertEqual(str(resolved["package-a"]), "1.0.0")
        self.assertEqual(str(resolved["package-b"]), "2.1.0")
        self.assertEqual(str(resolved["package-c"]), "3.0.5")
        
        # Test invalid dependency
        invalid_deps = {"invalid-package": "invalid-version"}
        with self.assertRaises(RuntimeError):
            self.manager.resolve_dependencies(invalid_deps)
    
    def test_validate_version_range(self):
        """Test version range validation"""
        test_cases = [
            ("1.0.0", "2.0.0", "1.5.0", True),
            ("1.0.0", "2.0.0", "1.0.0", True),  # Inclusive
            ("1.0.0", "2.0.0", "2.0.0", True),  # Inclusive
            ("1.0.0", "2.0.0", "0.9.9", False),
            ("1.0.0", "2.0.0", "2.0.1", False)
        ]
        
        for min_ver, max_ver, check_ver, expected in test_cases:
            with self.subTest(min=min_ver, max=max_ver, check=check_ver):
                result = self.manager.validate_version_range(min_ver, max_ver, check_ver)
                self.assertEqual(result, expected)
    
    def test_get_latest_version(self):
        """Test getting latest version from list"""
        versions = ["1.0.0", "1.1.0", "1.0.5", "2.0.0", "1.2.0-alpha"]
        
        # Without pre-release
        latest = self.manager.get_latest_version(versions)
        self.assertEqual(str(latest), "2.0.0")
        
        # With pre-release
        latest_with_pre = self.manager.get_latest_version(versions, include_prerelease=True)
        self.assertEqual(str(latest_with_pre), "2.0.0")  # Still stable is higher
        
        # Only pre-release versions
        prerelease_versions = ["1.0.0-alpha", "1.0.0-beta", "1.0.0-rc"]
        latest_pre = self.manager.get_latest_version(prerelease_versions, include_prerelease=True)
        self.assertEqual(str(latest_pre), "1.0.0-rc")
        
        # Empty list
        latest_empty = self.manager.get_latest_version([])
        self.assertIsNone(latest_empty)
        
        # No stable versions
        latest_no_stable = self.manager.get_latest_version(prerelease_versions, include_prerelease=False)
        self.assertIsNone(latest_no_stable)
    
    def test_thread_safety(self):
        """Test thread-safe operations"""
        results = []
        errors = []
        
        def parse_versions_thread(thread_id):
            try:
                versions = [f"{thread_id}.0.0", f"{thread_id}.1.0", f"{thread_id}.2.0"]
                parsed = [self.manager.parse_version(v) for v in versions]
                results.append((thread_id, parsed))
            except Exception as e:
                errors.append((thread_id, e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=parse_versions_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)
        
        # Verify versions were parsed correctly
        for thread_id, parsed_versions in results:
            self.assertEqual(len(parsed_versions), 3)
            self.assertEqual(str(parsed_versions[0]), f"{thread_id}.0.0")
    
    def test_get_stats(self):
        """Test statistics collection"""
        # Parse some versions to populate cache
        self.manager.parse_version("1.0.0")
        self.manager.parse_version("2.0.0")
        
        stats = self.manager.get_stats()
        
        self.assertIn('operation_count', stats)
        self.assertIn('cached_versions', stats)
        self.assertIn('cached_dependencies', stats)
        
        self.assertGreaterEqual(stats['operation_count'], 0)
        self.assertEqual(stats['cached_versions'], 2)
        self.assertEqual(stats['cached_dependencies'], 0)
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Populate cache
        self.manager.parse_version("1.0.0")
        self.assertEqual(len(self.manager._version_cache), 1)
        
        # Clear cache
        self.manager.clear_cache()
        self.assertEqual(len(self.manager._version_cache), 0)


if __name__ == '__main__':
    unittest.main()