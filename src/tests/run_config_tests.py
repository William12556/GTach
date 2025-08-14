#!/usr/bin/env python3
"""
Simple test runner to verify ConfigProcessor fix
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import unittest
from pathlib import Path
import tempfile
import shutil

# Import the test classes directly
from tests.provisioning.test_config_processor import TestConfigProcessor

def run_specific_tests():
    """Run the specific tests that were failing"""
    
    # Create a test suite with just the tests that were failing
    suite = unittest.TestSuite()
    
    # Add the specific test methods that were failing
    suite.addTest(TestConfigProcessor('test_process_templates'))
    suite.addTest(TestConfigProcessor('test_thread_safety'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

if __name__ == "__main__":
    print("Running ConfigProcessor fix validation tests...")
    success = run_specific_tests()
    
    if success:
        print("\n✓ All tests passed - ConfigProcessor fix is working correctly!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)
