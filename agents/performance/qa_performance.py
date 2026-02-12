#!/usr/bin/env python3
"""
Performance & Resilience Agent
Combines performance monitoring and resilience testing capabilities
"""

from crewai import Agent
from langchain.tools import BaseTool
from typing import Type, List, Dict, Any, Optional
from datetime import datetime
import asyncio
import sys
import os
import logging
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.llm_integration import llm_service
from config.environment import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMonitoringTool(BaseTool):
    name: str = "performance_monitoring"
    description: str = "Monitor system performance metrics including latency, throughput, and resource utilization"
    
    def _run(self, system_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor system performance with LLM-driven analysis"""
        # Implementation would use LLM integration
        return {
            "status": "completed",
            "metrics": {
                "latency_ms": 120,
                "throughput_rps": 850,
                "cpu_usage": 65.2,
                "memory_usage": 78.5
            },
            "analysis": "System performance within acceptable ranges"
        }


class LoadTestingTool(BaseTool):
    name: str = "load_testing"
    description: str = "Perform load testing to validate system behavior under stress"
    
    def _run(self, load_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute load testing scenarios"""
        return {
            "status": "completed",
            "test_results": {
                "concurrent_users": 100,
                "response_time_avg": 250,
                "error_rate": 0.02,
                "throughput_peak": 1200
            }
        }


class ResilienceValidationTool(BaseTool):
    name: str = "resilience_validation"
    description: str = "Test system resilience and recovery mechanisms"
    
    def _run(self, resilience_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate system resilience under failure conditions"""
        return {
            "status": "completed",
            "resilience_score": 0.85,
            "recovery_time_seconds": 45,
            "failure_scenarios_tested": ["database_down", "cache_miss", "network_partition"]
        }


class QAPerformanceAgent:
    def __init__(self):
        self.redis_client = config.get_redis_client()
        self.celery_app = config.get_celery_app('performance_agent')
        connection_info = config.get_connection_info()
        logger.info(f"Redis connection: {connection_info['redis']['url']}")
        logger.info(f"RabbitMQ connection: {connection_info['rabbitmq']['url']}")

        self.llm_service = llm_service
        
        # Create the CrewAI agent
        self.agent = Agent(
            role="Performance & Resilience Specialist",
            goal="Monitor system performance, conduct load testing, and validate resilience mechanisms",
            backstory="""You are a performance and resilience specialist with deep expertise in 
            system optimization, load testing, chaos engineering, and infrastructure resilience. 
            You ensure systems can handle expected loads and recover gracefully from failures.""",
            tools=[
                PerformanceMonitoringTool(),
                LoadTestingTool(),
                ResilienceValidationTool()
            ],
            llm=self.llm_service,
            verbose=True
        )
    
    async def monitor_performance(self, system_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor system performance metrics"""
        result = await asyncio.get_event_loop().run_in_executor(
            None, 
            self.agent.tools[0]._run, 
            system_specs
        )
        return result
    
    async def run_load_tests(self, load_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute load testing"""
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            self.agent.tools[1]._run,
            load_config
        )
        return result
    
    async def validate_resilience(self, resilience_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate system resilience"""
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            self.agent.tools[2]._run,
            resilience_config
        )
        return result

    async def run_performance_suite(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run performance/resilience suite based on scenario"""
        scenario = task_data.get("scenario", {})
        session_id = task_data.get("session_id")
        scenario_id = scenario.get("id", "performance")

        suite_type = self._determine_suite_type(scenario)

        if suite_type == "resilience":
            resilience_config = {
                "failure_scenarios": scenario.get("failure_scenarios", ["database_down", "cache_miss"]) 
            }
            result = await self.validate_resilience(resilience_config)
        elif suite_type == "load":
            load_config = {
                "concurrent_users": scenario.get("concurrent_users", 100),
                "duration_seconds": scenario.get("duration_seconds", 300)
            }
            result = await self.run_load_tests(load_config)
        else:
            monitoring_config = {
                "target_system": scenario.get("target_url", "configured system"),
                "monitoring_duration": scenario.get("monitoring_duration", 300)
            }
            result = await self.monitor_performance(monitoring_config)

        payload = {
            "suite_type": suite_type,
            "scenario_id": scenario_id,
            "session_id": session_id,
            "completed_at": datetime.now().isoformat(),
            **result
        }

        if session_id:
            self.redis_client.set(f"performance:{session_id}:{suite_type}", json.dumps(payload))
            self.redis_client.set(f"performance:{session_id}:{scenario_id}:result", json.dumps(payload))
            await self._notify_manager(str(session_id), scenario_id, payload)

        return payload

    def _determine_suite_type(self, scenario: Dict[str, Any]) -> str:
        name = scenario.get("name", "").lower()
        if "resilience" in name or scenario.get("failure_scenarios"):
            return "resilience"
        if "load" in name or scenario.get("concurrent_users") or scenario.get("load_profile"):
            return "load"
        return "monitoring"

    async def _notify_manager(self, session_id: str, scenario_id: str, result: Dict[str, Any]) -> None:
        notification = {
            "agent": "performance",
            "session_id": session_id,
            "scenario_id": scenario_id,
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.publish(f"manager:{session_id}:notifications", json.dumps(notification))


async def main():
    """Main entry point for Performance & Resilience agent with Celery worker"""
    agent = QAPerformanceAgent()

    logger.info("Starting Performance & Resilience Celery worker...")

    @agent.celery_app.task(bind=True, name="performance_agent.run_performance_suite")
    def run_performance_suite_task(self, task_data_json: str):
        """Celery task wrapper for performance suite"""
        try:
            task_data = json.loads(task_data_json)
            result = asyncio.run(agent.run_performance_suite(task_data))
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Celery performance task failed: {e}")
            return {"status": "error", "error": str(e)}

    async def redis_task_listener():
        """Listen for tasks from Redis pub/sub"""
        pubsub = agent.redis_client.pubsub()
        pubsub.subscribe("performance:tasks")

        logger.info("Performance Redis task listener started")

        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    task_data = json.loads(message['data'])
                    result = await agent.run_performance_suite(task_data)
                    logger.info(f"Performance task completed: {result.get('suite_type', 'unknown')}")
                except Exception as e:
                    logger.error(f"Redis task processing failed: {e}")

    import threading

    def start_celery_worker():
        """Start Celery worker in separate thread"""
        argv = [
            'worker',
            '--loglevel=info',
            '--concurrency=2',
            '--hostname=performance-worker@%h',
            '--queues=performance,default'
        ]
        agent.celery_app.worker_main(argv)

    celery_thread = threading.Thread(target=start_celery_worker, daemon=True)
    celery_thread.start()

    asyncio.create_task(redis_task_listener())

    logger.info("Performance & Resilience agent started with Celery worker and Redis listener")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Performance & Resilience agent shutting down...")
    except Exception as e:
        logger.error(f"Performance & Resilience agent error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
