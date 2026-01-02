"""
Pytest configuration and fixtures.
This file is loaded before any test files, allowing us to set up the environment.
"""
import sys
import os

# IMPORTANT: Set sys.argv[1] BEFORE any imports from the Backend codebase
# This is needed because functions.py reads config at module level: config.read(sys.argv[1])
_test_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.test.ini')
if len(sys.argv) < 2:
    sys.argv.insert(1, _test_config_path)
elif not (len(sys.argv) > 1 and sys.argv[1].endswith('.ini')):
    sys.argv.insert(1, _test_config_path)

# Add parent directory to path before any imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

