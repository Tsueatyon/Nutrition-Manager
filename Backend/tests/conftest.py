"""
Pytest configuration and fixtures.
This file is loaded before any test files, allowing us to set up the environment.
"""
import os
import sys

# IMPORTANT: Set environment variables BEFORE any imports from the Backend codebase
# This is needed because config.py reads environment variables at module level
os.environ['ENV_FILE'] = '.env.test'
os.environ['ENVIRONMENT'] = 'test'

# Set test environment variables
os.environ['JWT_SECRET_KEY'] = 'test_secret_key_for_testing_only'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'test_db'
os.environ['DB_USER'] = 'test_user'
os.environ['DB_PASSWORD'] = 'test_password'
os.environ['DB_DEBUG'] = 'False'
os.environ['USDA_API_KEY'] = 'test_api_key'
os.environ['ANTHROPIC_API_KEY'] = 'test_api_key'
os.environ['LLM_PROVIDER'] = 'anthropic'
os.environ['LLM_MODEL'] = 'claude-3-5-haiku-20241022'
os.environ['SERVER_PORT'] = '9000'

# Add parent directory to path before any imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

