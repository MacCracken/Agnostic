#!/usr/bin/env python3
"""
Comprehensive script to update all files with environment configuration.
This script finds and replaces all hardcoded Redis/RabbitMQ connections.
"""

import os
import re
import glob
from pathlib import Path


def update_file_with_config(file_path: str) -> bool:
    """Update a single file to use environment configuration."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Skip if already updated
        if 'from config.environment import config' in content:
            return False
        
        # Add config import
        if file_path.startswith('agents/'):
            # For agent files
            import_addition = '''
# Add config path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.environment import config'''
        elif file_path.startswith('webgui/'):
            # For webgui
            import_addition = '''
# Add config path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.environment import config'''
        else:
            # For other files in shared/
            import_addition = '''
# Add config path for imports
from config.environment import config'''
        
        # Add the import after the existing imports
        if 'import logging' in content:
            content = content.replace('import logging', f'import logging{import_addition}')
        elif 'import os' in content:
            content = content.replace('import os', f'import os{import_addition}')
        
        # Replace Redis connections
        redis_patterns = [
            r"redis\.Redis\(host='redis', port=6379, db=0\)",
            r'redis\.Redis\(host="redis", port=6379, db=0\)',
            r"redis\.Redis\(host='redis',\s*port=6379,\s*db=0\)"
        ]
        
        for pattern in redis_patterns:
            content = re.sub(pattern, 'config.get_redis_client()', content)
        
        # Replace Celery connections
        celery_patterns = [
            r"Celery\('([^']+)',\s*broker='amqp://guest:guest@rabbitmq:5672/'\)",
            r"Celery\('([^']+)',\s*broker=\"amqp://guest:guest@rabbitmq:5672/\"\)"
        ]
        
        for pattern in celery_patterns:
            content = re.sub(pattern, r"config.get_celery_app('\1')", content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def main():
    """Update all relevant files."""
    
    # Find all Python files that might need updating
    patterns = [
        'agents/*/*.py',
        'webgui/*.py', 
        'shared/*.py',
        'config/*.py'
    ]
    
    updated_files = []
    
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            if update_file_with_config(file_path):
                updated_files.append(file_path)
    
    print(f"\nUpdated {len(updated_files)} files:")
    for file_path in sorted(updated_files):
        print(f"  - {file_path}")
    
    # Check for remaining hardcoded connections
    print("\nChecking for remaining hardcoded connections...")
    remaining = []
    
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if "redis.Redis(host='redis'" in content or "broker='amqp://guest:guest@rabbitmq" in content:
                    remaining.append(file_path)
            except:
                continue
    
    if remaining:
        print(f"Still {len(remaining)} files with hardcoded connections:")
        for file_path in sorted(remaining):
            print(f"  - {file_path}")
    else:
        print("No hardcoded connections found!")


if __name__ == "__main__":
    main()