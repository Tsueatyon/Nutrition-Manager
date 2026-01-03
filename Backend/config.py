import os
from dotenv import load_dotenv

# Determine which .env file to load
# Default to .env.dev if no ENV_FILE specified
env_file = os.getenv('ENV_FILE', '.env.dev')

# Load environment variables from the appropriate .env file
# This only loads if the file exists (won't break in Cloud Run)
if os.path.exists(env_file):
    load_dotenv(env_file)
elif os.path.exists(f'Backend/{env_file}'):
    load_dotenv(f'Backend/{env_file}')
else:
    # Try to load from parent directory
    parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), env_file)
    if os.path.exists(parent_env):
        load_dotenv(parent_env)
    else:
        # Fallback: try .env.dev in current directory
        if os.path.exists('.env.dev'):
            load_dotenv('.env.dev')
        print(f"Warning: {env_file} not found, using environment variables only")

# Server Configuration
PORT = int(os.getenv('PORT', 8080))
SERVER_PORT = int(os.getenv('SERVER_PORT', os.getenv('PORT', 8080)))
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

# Database Configuration
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DEBUG = os.getenv('DB_DEBUG', 'False').lower() == 'true'

# API Keys
USDA_API_KEY = os.getenv('USDA_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# LLM Configuration
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'anthropic')
LLM_MODEL = os.getenv('LLM_MODEL', 'claude-3-5-haiku-20241022')

# Environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Redis Configuration (optional)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

# Celery Configuration (optional)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')

# Validate required environment variables
required_vars = ['JWT_SECRET_KEY', 'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'USDA_API_KEY', 'ANTHROPIC_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

print(f"Starting in {ENVIRONMENT} mode")
print(f"Loaded config from: {env_file if os.path.exists(env_file) else 'environment variables'}")

