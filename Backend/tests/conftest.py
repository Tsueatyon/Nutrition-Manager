"""
Pytest configuration and fixtures.
This file is loaded before any test files, allowing us to set up the environment.
"""
import os
import sys

# IMPORTANT: Set environment variables BEFORE any imports from the Backend codebase
# This is needed because config.py reads environment variables at module level

# Set test environment variables
os.environ['ENV_FILE'] = '.env.test'
os.environ['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'test_secret_key_for_testing_only')
os.environ['DB_HOST'] = os.getenv('DB_HOST', 'localhost')
os.environ['DB_PORT'] = os.getenv('DB_PORT', '5432')
os.environ['DB_NAME'] = os.getenv('DB_NAME', 'test_db')
os.environ['DB_USER'] = os.getenv('DB_USER', 'test_user')
os.environ['DB_PASSWORD'] = os.getenv('DB_PASSWORD', 'test_password')
os.environ['DB_DEBUG'] = os.getenv('DB_DEBUG', 'False')
os.environ['USDA_API_KEY'] = os.getenv('USDA_API_KEY', 'test_api_key')
os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', 'test_api_key')
os.environ['LLM_PROVIDER'] = os.getenv('LLM_PROVIDER', 'anthropic')
os.environ['LLM_MODEL'] = os.getenv('LLM_MODEL', 'claude-3-5-haiku-20241022')
os.environ['SERVER_PORT'] = os.getenv('SERVER_PORT', '9000')
os.environ['ENVIRONMENT'] = os.getenv('ENVIRONMENT', 'test')

# Add parent directory to path before any imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

