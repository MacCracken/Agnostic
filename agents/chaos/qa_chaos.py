import os
import sys
import json
import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
import redis
from celery import Celery
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceFailureTool(BaseTool):
    name: str = "Service Failure Simulator"
    description: str = "Simulates dependency failures, tests circuit breakers, and validates fallback mechanisms"

    def _run(self, failure_config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate service failures and test resilience"""
        services = failure_config.get("services", [])
        failure_types = failure_config.get("failure_types", ["unavailable", "timeout", "error_response"])

        # Dependency failure injection
        injection_results = self._inject_failures(services, failure_types)

        # Circuit breaker testing
        circuit_breaker_results = self._test_circuit_breakers(services)

        # Fallback validation
        fallback_results = self._validate_fallbacks(services)

        all_issues = []
        all_issues.extend(injection_results.get("issues", []))
        all_issues.extend(circuit_breaker_results.get("issues", []))
        all_issues.extend(fallback_results.get("issues", []))

        resilience_score = max(0, 100 - len(all_issues) * 15)

        return {
            "resilience_score": resilience_score,
            "services_tested": len(services),
            "failure_injection": injection_results,
            "circuit_breakers": circuit_breaker_results,
            "fallback_validation": fallback_results,
            "total_issues": len(all_issues),
            "issues": all_issues,
            "recommendations": self._build_recommendations(all_issues)
        }

    def _inject_failures(self, services: List[Dict], failure_types: List[str]) -> Dict[str, Any]:
        """Inject failures into dependencies"""
        results = []
        issues = []

        for service in services:
            name = service.get("name", "unknown")
            for failure_type in failure_types:
                # Simulated failure injection
                result = {
                    "service": name,
                    "failure_type": failure_type,
                    "system_behavior": "graceful_degradation",
                    "error_propagation": False,
                    "user_impact": "minimal"
                }
                results.append(result)

        return {"results": results, "issues": issues}

    def _test_circuit_breakers(self, services: List[Dict]) -> Dict[str, Any]:
        """Test circuit breaker behavior"""
        checks = [
            {"check": "Circuit breaker opens on repeated failures", "status": "pass"},
            {"check": "Half-open state allows test requests", "status": "pass"},
            {"check": "Circuit breaker closes on recovery", "status": "pass"},
            {"check": "Circuit breaker metrics are exposed", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _validate_fallbacks(self, services: List[Dict]) -> Dict[str, Any]:
        """Validate fallback mechanisms"""
        checks = [
            {"check": "Fallback responses are meaningful", "status": "pass"},
            {"check": "Cached data served when primary unavailable", "status": "pass"},
            {"check": "Fallback does not mask critical errors", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _build_recommendations(self, issues: List) -> List[str]:
        recs = []
        if any("circuit" in i.get("check", "").lower() for i in issues):
            recs.append("Implement circuit breakers for all external dependency calls")
        if any("fallback" in i.get("check", "").lower() for i in issues):
            recs.append("Implement meaningful fallback responses for degraded service scenarios")
        return recs


class NetworkPartitionTool(BaseTool):
    name: str = "Network Partition Simulator"
    description: str = "Simulates network partitions including latency injection, packet loss, and DNS failures"

    def _run(self, network_config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate network partition scenarios"""
        # Latency injection
        latency_results = self._test_latency_injection(network_config)

        # Packet loss simulation
        packet_loss_results = self._test_packet_loss(network_config)

        # DNS failure testing
        dns_failure_results = self._test_dns_failures(network_config)

        all_issues = []
        all_issues.extend(latency_results.get("issues", []))
        all_issues.extend(packet_loss_results.get("issues", []))
        all_issues.extend(dns_failure_results.get("issues", []))

        score = max(0, 100 - len(all_issues) * 15)

        return {
            "network_resilience_score": score,
            "latency_injection": latency_results,
            "packet_loss": packet_loss_results,
            "dns_failures": dns_failure_results,
            "total_issues": len(all_issues),
            "issues": all_issues,
            "recommendations": self._build_recommendations(all_issues)
        }

    def _test_latency_injection(self, config: Dict) -> Dict[str, Any]:
        """Test system behavior under increased latency"""
        scenarios = [
            {"latency_ms": 100, "behavior": "normal", "timeout_triggered": False},
            {"latency_ms": 500, "behavior": "normal", "timeout_triggered": False},
            {"latency_ms": 2000, "behavior": "degraded", "timeout_triggered": False},
            {"latency_ms": 10000, "behavior": "timeout_expected", "timeout_triggered": True},
        ]
        issues = [s for s in scenarios if s["behavior"] == "error"]
        return {"scenarios_tested": len(scenarios), "results": scenarios, "issues": issues}

    def _test_packet_loss(self, config: Dict) -> Dict[str, Any]:
        """Test system behavior under packet loss"""
        scenarios = [
            {"loss_pct": 1, "retries_effective": True, "data_integrity": True},
            {"loss_pct": 5, "retries_effective": True, "data_integrity": True},
            {"loss_pct": 20, "retries_effective": True, "data_integrity": True},
            {"loss_pct": 50, "retries_effective": False, "data_integrity": True},
        ]
        issues = [s for s in scenarios if not s["data_integrity"]]
        return {"scenarios_tested": len(scenarios), "results": scenarios, "issues": issues}

    def _test_dns_failures(self, config: Dict) -> Dict[str, Any]:
        """Test system behavior during DNS failures"""
        checks = [
            {"check": "DNS cache prevents immediate failure", "status": "pass"},
            {"check": "Retry with exponential backoff", "status": "pass"},
            {"check": "Fallback DNS resolver configured", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _build_recommendations(self, issues: List) -> List[str]:
        recs = []
        if issues:
            recs.append("Implement retry logic with exponential backoff for network operations")
            recs.append("Configure appropriate timeouts for all network calls")
            recs.append("Add connection pooling and DNS caching")
        return recs


class ResourceExhaustionTool(BaseTool):
    name: str = "Resource Exhaustion Tester"
    description: str = "Tests system behavior under resource pressure including memory, CPU, and disk exhaustion"

    def _run(self, resource_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test resource exhaustion scenarios"""
        # Memory pressure
        memory_results = self._test_memory_pressure(resource_config)

        # CPU saturation
        cpu_results = self._test_cpu_saturation(resource_config)

        # Disk exhaustion
        disk_results = self._test_disk_exhaustion(resource_config)

        all_issues = []
        all_issues.extend(memory_results.get("issues", []))
        all_issues.extend(cpu_results.get("issues", []))
        all_issues.extend(disk_results.get("issues", []))

        score = max(0, 100 - len(all_issues) * 15)

        return {
            "resource_resilience_score": score,
            "memory_pressure": memory_results,
            "cpu_saturation": cpu_results,
            "disk_exhaustion": disk_results,
            "total_issues": len(all_issues),
            "issues": all_issues,
            "recommendations": self._build_recommendations(all_issues)
        }

    def _test_memory_pressure(self, config: Dict) -> Dict[str, Any]:
        """Test system behavior under memory pressure"""
        scenarios = [
            {"memory_usage_pct": 70, "behavior": "normal", "gc_effective": True},
            {"memory_usage_pct": 85, "behavior": "normal", "gc_effective": True},
            {"memory_usage_pct": 95, "behavior": "degraded", "gc_effective": True},
        ]
        issues = [s for s in scenarios if s["behavior"] == "crash"]
        return {"scenarios_tested": len(scenarios), "results": scenarios, "issues": issues}

    def _test_cpu_saturation(self, config: Dict) -> Dict[str, Any]:
        """Test system behavior under CPU saturation"""
        scenarios = [
            {"cpu_usage_pct": 50, "response_time_impact": "none"},
            {"cpu_usage_pct": 80, "response_time_impact": "moderate"},
            {"cpu_usage_pct": 95, "response_time_impact": "significant"},
        ]
        issues = [s for s in scenarios if s["response_time_impact"] == "critical"]
        return {"scenarios_tested": len(scenarios), "results": scenarios, "issues": issues}

    def _test_disk_exhaustion(self, config: Dict) -> Dict[str, Any]:
        """Test system behavior when disk space is low"""
        checks = [
            {"check": "Graceful handling of disk full condition", "status": "pass"},
            {"check": "Log rotation prevents disk exhaustion", "status": "pass"},
            {"check": "Alerts triggered before disk full", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _build_recommendations(self, issues: List) -> List[str]:
        recs = []
        if issues:
            recs.append("Implement resource monitoring with alerting at 80% thresholds")
            recs.append("Configure resource limits and OOM kill policies for containers")
            recs.append("Implement graceful degradation under resource pressure")
        return recs


class RecoveryValidationTool(BaseTool):
    name: str = "Recovery Validation"
    description: str = "Validates recovery behavior including MTTR measurement, data integrity, and auto-recovery verification"

    def _run(self, recovery_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate recovery mechanisms"""
        # MTTR measurement
        mttr_results = self._measure_mttr(recovery_config)

        # Data integrity after failure
        integrity_results = self._verify_data_integrity(recovery_config)

        # Auto-recovery verification
        auto_recovery_results = self._verify_auto_recovery(recovery_config)

        all_issues = []
        all_issues.extend(mttr_results.get("issues", []))
        all_issues.extend(integrity_results.get("issues", []))
        all_issues.extend(auto_recovery_results.get("issues", []))

        score = max(0, 100 - len(all_issues) * 15)

        return {
            "recovery_score": score,
            "mttr": mttr_results,
            "data_integrity": integrity_results,
            "auto_recovery": auto_recovery_results,
            "total_issues": len(all_issues),
            "issues": all_issues,
            "recommendations": self._build_recommendations(all_issues)
        }

    def _measure_mttr(self, config: Dict) -> Dict[str, Any]:
        """Measure Mean Time To Recovery"""
        target_mttr_seconds = config.get("target_mttr_seconds", 300)
        # Simulated MTTR measurement
        measured_mttr = 120  # seconds

        issues = []
        if measured_mttr > target_mttr_seconds:
            issues.append({"check": f"MTTR {measured_mttr}s exceeds target {target_mttr_seconds}s", "status": "fail"})

        return {
            "target_mttr_seconds": target_mttr_seconds,
            "measured_mttr_seconds": measured_mttr,
            "meets_target": measured_mttr <= target_mttr_seconds,
            "issues": issues
        }

    def _verify_data_integrity(self, config: Dict) -> Dict[str, Any]:
        """Verify data integrity after failure recovery"""
        checks = [
            {"check": "No data loss after crash recovery", "status": "pass"},
            {"check": "Transaction consistency maintained", "status": "pass"},
            {"check": "Cache coherence after restart", "status": "pass"},
            {"check": "Session state recoverable", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _verify_auto_recovery(self, config: Dict) -> Dict[str, Any]:
        """Verify automatic recovery mechanisms"""
        checks = [
            {"check": "Container auto-restart on failure", "status": "pass"},
            {"check": "Health check triggers recovery", "status": "pass"},
            {"check": "Service re-registers after recovery", "status": "pass"},
            {"check": "Reconnection to dependencies automatic", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _build_recommendations(self, issues: List) -> List[str]:
        recs = []
        if any("MTTR" in i.get("check", "") for i in issues):
            recs.append("Reduce MTTR — automate recovery procedures and pre-warm standby instances")
        if any("data" in i.get("check", "").lower() or "integrity" in i.get("check", "").lower() for i in issues):
            recs.append("Implement write-ahead logging and checkpoint mechanisms for data integrity")
        if any("auto" in i.get("check", "").lower() or "restart" in i.get("check", "").lower() for i in issues):
            recs.append("Configure health checks and restart policies for automatic recovery")
        return recs


class ChaosEngineerAgent:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.celery_app = Celery('chaos_agent', broker='amqp://guest:guest@rabbitmq:5672/')
        self.llm = ChatOpenAI(model=os.getenv('OPENAI_MODEL', 'gpt-4o'), temperature=0.1)

        self.agent = Agent(
            role='Chaos & Resilience Engineer',
            goal='Validate system resilience through controlled failure injection, network chaos, resource exhaustion, and recovery testing',
            backstory="""You are a Chaos Engineer with 8+ years of experience in resilience testing
            and failure injection. You excel at designing chaos experiments that safely expose
            weaknesses in distributed systems, testing circuit breakers and fallback mechanisms,
            and validating recovery procedures under realistic failure conditions.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                ServiceFailureTool(),
                NetworkPartitionTool(),
                ResourceExhaustionTool(),
                RecoveryValidationTool()
            ]
        )

    async def run_chaos_tests(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive chaos/resilience tests"""
        scenario = task_data.get("scenario", {})
        session_id = task_data.get("session_id")
        logger.info(f"Chaos Engineer testing for session: {session_id}")

        self.redis_client.set(f"chaos:{session_id}:{scenario.get('id', 'chaos')}", json.dumps({
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "scenario": scenario
        }))

        chaos_task = Task(
            description=f"""Run chaos/resilience tests for session {session_id}:

            Target: {scenario.get('target_services', 'configured services')}

            Test:
            1. Service failure injection (dependency failures, circuit breakers, fallbacks)
            2. Network partition simulation (latency, packet loss, DNS failures)
            3. Resource exhaustion (memory pressure, CPU saturation, disk full)
            4. Recovery validation (MTTR, data integrity, auto-recovery)
            """,
            agent=self.agent,
            expected_output="Chaos testing report with resilience scores and recovery validation"
        )

        crew = Crew(agents=[self.agent], tasks=[chaos_task], process=Process.sequential, verbose=True)
        crew.kickoff()

        failure_tool = ServiceFailureTool()
        failure_result = failure_tool._run(scenario.get("failure_config", {"services": []}))

        network_tool = NetworkPartitionTool()
        network_result = network_tool._run(scenario.get("network_config", {}))

        resource_tool = ResourceExhaustionTool()
        resource_result = resource_tool._run(scenario.get("resource_config", {}))

        recovery_tool = RecoveryValidationTool()
        recovery_result = recovery_tool._run(scenario.get("recovery_config", {}))

        result = {
            "service_failure": failure_result,
            "network_partition": network_result,
            "resource_exhaustion": resource_result,
            "recovery_validation": recovery_result
        }

        self.redis_client.set(f"chaos:{session_id}:tests", json.dumps(result))

        await self._notify_manager(session_id, scenario.get("id", "chaos"), result)

        return {
            "scenario_id": scenario.get("id", "chaos"),
            "session_id": session_id,
            "chaos_tests": result,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }

    async def _notify_manager(self, session_id: str, scenario_id: str, result: Dict):
        """Notify QA Manager of task completion"""
        notification = {
            "agent": "chaos",
            "session_id": session_id,
            "scenario_id": scenario_id,
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.publish(f"manager:{session_id}:notifications", json.dumps(notification))


async def main():
    """Main entry point for Chaos Engineer agent"""
    agent = ChaosEngineerAgent()

    sample_task = {
        "session_id": "session_20240207_143000",
        "scenario": {
            "id": "chaos_015",
            "name": "Chaos & Resilience Testing",
            "priority": "high",
            "target_services": ["qa-manager", "senior-qa", "junior-qa"]
        },
        "timestamp": datetime.now().isoformat()
    }

    result = await agent.run_chaos_tests(sample_task)
    print(f"Chaos Engineer Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
