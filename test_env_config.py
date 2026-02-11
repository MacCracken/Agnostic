#!/usr/bin/env python3
"""
Test script to verify environment configuration works correctly.
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.environment import config

def test_config():
    """Test the configuration system."""
    print("Testing Environment Configuration...")
    
    # Test validation
    validation = config.validate_required_env_vars()
    print(f"Environment validation: {validation}")
    
    # Test Redis client creation
    try:
        redis_client = config.get_redis_client()
        print(f"✓ Redis client created successfully")
        print(f"  Host: {redis_client.connection_pool.connection_kwargs.get('host', 'unknown')}")
        print(f"  Port: {redis_client.connection_pool.connection_kwargs.get('port', 'unknown')}")
    except Exception as e:
        print(f"✗ Redis client creation failed: {e}")
    
    # Test Celery app creation
    try:
        celery_app = config.get_celery_app('test_app')
        print(f"✓ Celery app created successfully")
        print(f"  Broker: {celery_app.conf.broker_url}")
    except Exception as e:
        print(f"✗ Celery app creation failed: {e}")
    
    # Test connection info
    try:
        connection_info = config.get_connection_info()
        print(f"✓ Connection info retrieved:")
        print(f"  Redis: {connection_info['redis']['url']}")
        print(f"  RabbitMQ: {connection_info['rabbitmq']['url']}")
    except Exception as e:
        print(f"✗ Connection info retrieval failed: {e}")
    
    print("\nEnvironment configuration test completed!")

if __name__ == "__main__":
    test_config()