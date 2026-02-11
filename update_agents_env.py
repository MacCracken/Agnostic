#!/usr/bin/env python3
"""
Script to update all agent files to use environment configuration.
Replaces hardcoded Redis and RabbitMQ connections with config-based ones.
"""

import os
import re
from pathlib import Path


def update_agent_file(file_path: Path) -> bool:
    """Update a single agent file to use environment configuration."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if already updated
        if 'from config.environment import config' in content:
            print(f"Already updated: {file_path}")
            return True
        
        # Add config import after existing imports
        import_pattern = r'(import logging\n)'
        config_import = r'\1\n# Add config path for imports\nsys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))\nfrom config.environment import config\n'
        
        # Add sys import if not present
        if 'import sys' not in content:
            content = re.sub(r'import os', 'import os\nimport sys', content)
        
        content = re.sub(import_pattern, config_import, content)
        
        # Replace Redis client initialization
        redis_patterns = [
            r"redis\.Redis\(host='redis', port=6379, db=0\)",
            r'redis\.Redis\(host="redis", port=6379, db=0\)',
            r"redis\.Redis\(host='redis',\s*port=6379,\s*db=0\)"
        ]
        
        for pattern in redis_patterns:
            content = re.sub(pattern, 'config.get_redis_client()', content)
        
        # Replace Celery app initialization
        celery_patterns = [
            r"Celery\('([^']+)',\s*broker='amqp://guest:guest@rabbitmq:5672/'\)",
            r"Celery\('([^']+)',\s*broker=\"amqp://guest:guest@rabbitmq:5672/\"\)"
        ]
        
        for pattern in celery_patterns:
            content = re.sub(pattern, r"config.get_celery_app('\1')", content)
        
        # Update class __init__ methods to add validation and logging
        init_pattern = r'(class\s+\w+Agent.*?def\s+__init__\(self\):\s*\n)'
        new_init = r'''\1
        # Validate environment variables
        validation = config.validate_required_env_vars()
        if not all(validation.values()):
            missing = [k for k, v in validation.items() if not v]
            logger.warning(f"Missing environment variables: {missing}")
        
        # Initialize Redis and Celery with environment configuration
        self.redis_client = config.get_redis_client()
        self.celery_app = config.get_celery_app('\2')
        
        # Log connection info (without passwords)
        connection_info = config.get_connection_info()
        logger.info(f"Redis connection: {connection_info['redis']['url']}")
        logger.info(f"RabbitMQ connection: {connection_info['rabbitmq']['url']}")
'''
        
        # This is complex - let's do a simpler approach for the __init__ method
        class_init_pattern = r'(class\s+(\w+Agent):.*?def\s+__init__\(self\):\s*\n)'
        def replace_init(match):
            class_name = match.group(2)
            return f'''{match.group(0)}
        # Validate environment variables
        validation = config.validate_required_env_vars()
        if not all(validation.values()):
            missing = [k for k, v in validation.items() if not v]
            logger.warning(f"Missing environment variables: {missing}")
        
        # Initialize Redis and Celery with environment configuration
        self.redis_client = config.get_redis_client()
        self.celery_app = config.get_celery_app('{class_name.lower()}')
        
        # Log connection info (without passwords)
        connection_info = config.get_connection_info()
        logger.info(f"Redis connection: {{connection_info['redis']['url']}}")
        logger.info(f"RabbitMQ connection: {{connection_info['rabbitmq']['url']}}")'''
        
        # This is getting complex - let's do manual updates for key files instead
        return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def manual_update_agent(agent_path: str, agent_name: str, app_name: str):
    """Manually update a specific agent file."""
    file_path = Path(agent_path)
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add sys import if not present
    if 'import sys' not in content:
        content = content.replace('import os', 'import os\nimport sys')
    
    # Add config import
    if 'from config.environment import config' not in content:
        content = content.replace(
            'import logging',
            'import logging\n\n# Add config path for imports\nsys.path.append(os.path.join(os.path.dirname(__file__), \'..\', \'..\'))\nfrom config.environment import config'
        )
    
    # Replace hardcoded connections
    content = content.replace(
        "redis.Redis(host='redis', port=6379, db=0)",
        'config.get_redis_client()'
    ).replace(
        "redis.Redis(host=\"redis\", port=6379, db=0)",
        'config.get_redis_client()'
    )
    
    content = content.replace(
        f"Celery('{app_name}', broker='amqp://guest:guest@rabbitmq:5672/')",
        f"config.get_celery_app('{app_name}')"
    ).replace(
        f'Celery("{app_name}", broker="amqp://guest:guest@rabbitmq:5672/")',
        f"config.get_celery_app('{app_name}')"
    )
    
    # Update initialization
    old_init = f"class {agent_name}:\n    def __init__(self):\n        self.redis_client = config.get_redis_client()\n        self.celery_app = config.get_celery_app('{app_name}')"
    new_init = f"""class {agent_name}:
    def __init__(self):
        # Validate environment variables
        validation = config.validate_required_env_vars()
        if not all(validation.values()):
            missing_vars = [k for k, v in validation.items() if not v]
            logger.warning(f"Missing environment variables: {{missing_vars}}")
        
        # Initialize Redis and Celery with environment configuration
        self.redis_client = config.get_redis_client()
        self.celery_app = config.get_celery_app('{app_name}')
        
        # Log connection info (without passwords)
        connection_info = config.get_connection_info()
        logger.info(f"Redis connection: {{connection_info['redis']['url']}}")
        logger.info(f"RabbitMQ connection: {{connection_info['rabbitmq']['url']}}")"""
    
    # Find and replace the class initialization
    import re
    pattern = rf"class {agent_name}:\s*\n\s*def __init__\(self\):\s*\n\s*self\.redis_client = config\.get_redis_client\(\)\s*\n\s*self\.celery_app = config\.get_celery_app\('{app_name}'\)"
    content = re.sub(pattern, new_init, content, flags=re.MULTILINE | re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Updated: {agent_path}")


def main():
    """Update all agent files."""
    agents = [
        ("agents/senior/senior_qa.py", "SeniorQAAgent", "senior_qa"),
        ("agents/junior/junior_qa.py", "JuniorQAAgent", "junior_qa"),
        ("agents/sre/qa_sre.py", "QSREAgent", "sre_agent"),
        ("agents/accessibility/qa_accessibility.py", "AccessibilityAgent", "accessibility_agent"),
        ("agents/api/qa_api.py", "APIAgent", "api_agent"),
        ("agents/mobile/qa_mobile.py", "MobileAgent", "mobile_agent"),
        ("agents/compliance/qa_compliance.py", "ComplianceAgent", "compliance_agent"),
        ("agents/chaos/qa_chaos.py", "ChaosAgent", "chaos_agent"),
    ]
    
    for agent_path, agent_name, app_name in agents:
        try:
            manual_update_agent(agent_path, agent_name, app_name)
        except Exception as e:
            print(f"Failed to update {agent_path}: {e}")
    
    # Update webgui separately
    try:
        file_path = "webgui/app.py"
        with open(file_path, 'r') as f:
            content = f.read()
        
        if 'from config.environment import config' not in content:
            content = content.replace(
                'import logging',
                'import logging\n\n# Add config path for imports\nsys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\nfrom config.environment import config'
            )
        
        content = content.replace(
            "redis.Redis(host='redis', port=6379, db=0)",
            'config.get_redis_client()'
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("Updated: webgui/app.py")
    except Exception as e:
        print(f"Failed to update webgui/app.py: {e}")


if __name__ == "__main__":
    main()