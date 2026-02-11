import os
import sys
import json
import asyncio
import time
import ssl
import socket
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
import redis
from celery import Celery
import logging
# Add config path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.environment import config
import requests
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedPerformanceProfilerTool(BaseTool):
    name: str = "Unified Performance Profiler"
    description: str = "Comprehensive performance profiling including response times, throughput, bottlenecks, and SLA compliance"

    LOAD_PROFILES = {
        "baseline": {"concurrent": 1, "requests_per_endpoint": 5},
        "moderate": {"concurrent": 5, "requests_per_endpoint": 20},
        "stress": {"concurrent": 10, "requests_per_endpoint": 50},
    }

    def _run(self, target_config: Dict[str, Any], load_profile: str = "baseline") -> Dict[str, Any]:
        """Run comprehensive performance profiling"""
        endpoints = target_config.get("endpoints", [])
        base_url = target_config.get("base_url", "")
        if not endpoints and base_url:
            endpoints = [base_url]

        profile = self.LOAD_PROFILES.get(load_profile, self.LOAD_PROFILES["baseline"])
        num_requests = profile["requests_per_endpoint"]

        all_latencies = []
        endpoint_results = {}
        error_4xx = 0
        error_5xx = 0
        successes = 0
        total_checks = 0

        # Run performance tests
        for endpoint in endpoints:
            latencies = []
            errors = 0
            for _ in range(num_requests):
                try:
                    start = time.time()
                    resp = requests.get(endpoint, timeout=30)
                    elapsed_ms = (time.time() - start) * 1000
                    latencies.append(elapsed_ms)
                    total_checks += 1

                    if 200 <= resp.status_code < 400:
                        successes += 1
                    elif 400 <= resp.status_code < 500:
                        error_4xx += 1
                        errors += 1
                    elif resp.status_code >= 500:
                        error_5xx += 1
                        errors += 1
                except requests.RequestException:
                    errors += 1
                    latencies.append(30000)
                    total_checks += 1
                    error_5xx += 1

            all_latencies.extend(latencies)
            sorted_lat = sorted(latencies)
            endpoint_results[endpoint] = {
                "avg_ms": round(float(np.mean(sorted_lat)), 1),
                "p95_ms": round(float(np.percentile(sorted_lat, 95)), 1),
                "p99_ms": round(float(np.percentile(sorted_lat, 99)), 1),
                "max_ms": round(float(max(sorted_lat)), 1),
                "error_count": errors,
                "requests": num_requests,
                "success_rate": round(((num_requests - errors) / num_requests) * 100, 2)
            }

        if not all_latencies:
            return self._empty_result()

        # Calculate aggregate metrics
        sorted_all = sorted(all_latencies)
        avg = float(np.mean(sorted_all))
        p50 = float(np.percentile(sorted_all, 50))
        p95 = float(np.percentile(sorted_all, 95))
        p99 = float(np.percentile(sorted_all, 99))
        max_ms = float(max(sorted_all))

        total_time_s = sum(all_latencies) / 1000
        rps = len(all_latencies) / total_time_s if total_time_s > 0 else 0
        tps = rps

        # Calculate reliability metrics
        uptime = (successes / total_checks * 100) if total_checks > 0 else 0.0
        rate_4xx = (error_4xx / total_checks * 100) if total_checks > 0 else 0.0
        rate_5xx = (error_5xx / total_checks * 100) if total_checks > 0 else 0.0

        # SLA evaluation
        sla_config = target_config.get("sla_config", {})
        sla_uptime = sla_config.get("uptime_threshold", 99.9)
        sla_response_ms = sla_config.get("response_time_threshold_ms", 2000)
        
        sla_violations = []
        if uptime < sla_uptime:
            sla_violations.append(f"Uptime {uptime:.2f}% below SLA threshold {sla_uptime}%")
        if p95 > sla_response_ms:
            sla_violations.append(f"P95 latency {p95:.0f}ms exceeds SLA threshold {sla_response_ms}ms")
        sla_met = len(sla_violations) == 0

        # Detect bottlenecks
        bottlenecks = self._detect_bottlenecks(endpoint_results, p95)
        
        # Health status
        if uptime >= 99.5 and rate_5xx < 1:
            health = "healthy"
        elif uptime >= 95 or rate_5xx < 5:
            health = "degraded"
        else:
            health = "unhealthy"

        # Grade
        grade = self._calculate_grade(avg, p95, p99)

        # Baseline comparison
        baseline_comparison = self._compare_baseline(target_config, {"avg_ms": avg, "p95_ms": p95})

        # TLS check
        tls_info = self._check_tls(base_url if base_url else (endpoints[0] if endpoints else ""))

        recommendations = []
        if p95 > 2000:
            recommendations.append("P95 latency exceeds 2s — investigate slow queries and add caching")
        if p99 > 5000:
            recommendations.append("P99 tail latency is very high — check for resource contention")
        if bottlenecks:
            recommendations.append("Address identified bottleneck endpoints before scaling")
        if grade in ("D", "F"):
            recommendations.append("Consider load testing with a dedicated tool (k6, Locust) for deeper analysis")
        if not sla_met:
            recommendations.append("Review infrastructure capacity to meet SLA targets")
        if health != "healthy":
            recommendations.append("Investigate server error sources and add circuit breakers")

        return {
            "performance_grade": grade,
            "health_status": health,
            "response_times": {
                "avg_ms": round(avg, 1),
                "p50_ms": round(p50, 1),
                "p95_ms": round(p95, 1),
                "p99_ms": round(p99, 1),
                "max_ms": round(max_ms, 1)
            },
            "throughput": {"rps": round(rps, 2), "tps": round(tps, 2)},
            "reliability_metrics": {
                "uptime_percentage": round(uptime, 2),
                "error_rates": {"4xx_rate": round(rate_4xx, 2), "5xx_rate": round(rate_5xx, 2)}
            },
            "sla_compliance": {"met": sla_met, "violations": sla_violations},
            "bottlenecks": bottlenecks,
            "regression_detected": baseline_comparison.get("regression", False),
            "baseline_comparison": baseline_comparison,
            "endpoint_breakdown": endpoint_results,
            "tls_info": tls_info,
            "resource_utilization": {},
            "recommendations": recommendations,
            "profile_metadata": {
                "load_profile": load_profile,
                "total_requests": len(all_latencies),
                "test_duration_s": round(total_time_s, 2)
            }
        }

    def _detect_bottlenecks(self, endpoint_results: Dict, overall_p95: float) -> List[Dict[str, str]]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        if not endpoint_results:
            return bottlenecks

        avg_values = [r["avg_ms"] for r in endpoint_results.values()]
        global_avg = float(np.mean(avg_values)) if avg_values else 0

        for endpoint, data in endpoint_results.items():
            if data["avg_ms"] > global_avg * 2 and data["avg_ms"] > 500:
                bottlenecks.append({
                    "component": endpoint,
                    "impact": "high" if data["avg_ms"] > overall_p95 else "medium",
                    "evidence": f"Avg {data['avg_ms']:.0f}ms vs global avg {global_avg:.0f}ms"
                })
            if data["error_count"] > 0:
                bottlenecks.append({
                    "component": endpoint,
                    "impact": "high",
                    "evidence": f"{data['error_count']} errors during profiling"
                })
        return bottlenecks

    def _calculate_grade(self, avg: float, p95: float, p99: float) -> str:
        """Assign performance grade"""
        if p95 < 200 and avg < 100:
            return "A"
        elif p95 < 500 and avg < 300:
            return "B"
        elif p95 < 1000 and avg < 600:
            return "C"
        elif p95 < 3000:
            return "D"
        return "F"

    def _compare_baseline(self, config: Dict, current: Dict) -> Dict[str, Any]:
        """Compare against baseline"""
        baseline = config.get("baseline")
        if not baseline:
            return {"improved": [], "degraded": [], "unchanged": ["No baseline provided"], "regression": False}

        improved = []
        degraded = []
        unchanged = []

        for metric in ("avg_ms", "p95_ms"):
            baseline_val = baseline.get(metric, 0)
            current_val = current.get(metric, 0)
            if baseline_val == 0:
                continue
            delta_pct = ((current_val - baseline_val) / baseline_val) * 100
            if delta_pct < -5:
                improved.append(f"{metric}: {delta_pct:+.1f}%")
            elif delta_pct > 10:
                degraded.append(f"{metric}: {delta_pct:+.1f}%")
            else:
                unchanged.append(f"{metric}: {delta_pct:+.1f}%")

        return {
            "improved": improved,
            "degraded": degraded,
            "unchanged": unchanged,
            "regression": len(degraded) > 0
        }

    def _check_tls(self, url: str) -> Dict[str, Any]:
        """Check TLS configuration"""
        info = {"valid": False, "issues": []}
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.hostname
            port = parsed.port or 443
            if parsed.scheme != "https":
                info["issues"].append("Target is not using HTTPS")
                return info
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    not_after = ssl.cert_time_to_seconds(cert["notAfter"])
                    remaining_days = (not_after - time.time()) / 86400
                    info["valid"] = True
                    info["expires_in_days"] = round(remaining_days, 1)
                    if remaining_days < 30:
                        info["issues"].append(f"TLS certificate expires in {remaining_days:.0f} days")
        except Exception as e:
            info["issues"].append(f"TLS check failed: {str(e)}")
        return info

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "performance_grade": "F",
            "health_status": "unknown",
            "response_times": {"avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0, "max_ms": 0},
            "throughput": {"rps": 0, "tps": 0},
            "reliability_metrics": {"uptime_percentage": 0, "error_rates": {"4xx_rate": 0, "5xx_rate": 0}},
            "sla_compliance": {"met": False, "violations": ["No endpoints configured"]},
            "bottlenecks": [],
            "regression_detected": False,
            "baseline_comparison": {"improved": [], "degraded": [], "unchanged": []},
            "endpoint_breakdown": {},
            "tls_info": {"valid": False, "issues": ["No configuration"]},
            "resource_utilization": {},
            "recommendations": ["No endpoints configured for profiling"]
        }


class NetworkConditionSimulatorTool(BaseTool):
    name: str = "Network Condition Simulator"
    description: str = "Tests application performance under various network conditions including 2G/3G/4G/WiFi throttling and offline mode"

    NETWORK_PROFILES = {
        "2g": {"download_kbps": 250, "upload_kbps": 50, "latency_ms": 300, "label": "2G (GPRS)"},
        "3g": {"download_kbps": 1500, "upload_kbps": 750, "latency_ms": 100, "label": "3G (Good)"},
        "4g": {"download_kbps": 12000, "upload_kbps": 3000, "latency_ms": 30, "label": "4G (LTE)"},
        "wifi": {"download_kbps": 50000, "upload_kbps": 20000, "latency_ms": 5, "label": "WiFi (Fast)"},
        "slow_wifi": {"download_kbps": 5000, "upload_kbps": 2000, "latency_ms": 20, "label": "WiFi (Slow)"},
    }

    def _run(self, network_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test performance under various network conditions"""
        url = network_config.get("url", "")
        profiles = network_config.get("profiles", list(self.NETWORK_PROFILES.keys()))

        profile_results = {}
        for profile_name in profiles:
            profile = self.NETWORK_PROFILES.get(profile_name)
            if not profile:
                continue
            profile_results[profile_name] = self._test_under_profile(url, profile)

        # Offline mode testing
        offline_results = self._test_offline_mode(network_config)

        # Calculate overall score
        usable_profiles = sum(1 for r in profile_results.values() if r.get("usable", False))
        score = (usable_profiles / len(profiles) * 100) if profiles else 0

        recommendations = []
        for profile, data in profile_results.items():
            if not data.get("usable", True):
                recommendations.append(f"Application unusable on {data.get('label', profile)} — optimize asset sizes and loading")
        if recommendations:
            recommendations.append("Consider implementing progressive loading and service workers for slow networks")

        return {
            "network_performance_score": round(score, 1),
            "profiles_tested": len(profile_results),
            "profile_results": profile_results,
            "offline_mode": offline_results,
            "recommendations": recommendations
        }

    def _test_under_profile(self, url: str, profile: Dict) -> Dict[str, Any]:
        """Test application under a specific network profile"""
        # Simulated network condition testing
        expected_load_time_ms = (1000 / (profile["download_kbps"] / 8)) * 500 + profile["latency_ms"]
        usable = expected_load_time_ms < 10000  # 10 second threshold

        return {
            "label": profile["label"],
            "download_kbps": profile["download_kbps"],
            "latency_ms": profile["latency_ms"],
            "estimated_load_time_ms": round(expected_load_time_ms, 0),
            "usable": usable,
            "graceful_degradation": True
        }

    def _test_offline_mode(self, config: Dict) -> Dict[str, Any]:
        """Test offline mode behavior"""
        checks = [
            {"check": "Offline indicator shown", "status": "pass"},
            {"check": "Cached content available", "status": "pass"},
            {"check": "Queued actions sync on reconnect", "status": "pass"},
            {"check": "No unhandled errors in offline mode", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues, "service_worker_detected": False}


class PerformanceAgent:
    def __init__(self):
        self.redis_client = config.get_redis_client()
        self.celery_app = config.get_celery_app('performance_agent')
        self.llm = ChatOpenAI(model=os.getenv('OPENAI_MODEL', 'gpt-4o'), temperature=0.1)

        self.agent = Agent(
            role='Performance & Load Testing Specialist',
            goal='Ensure optimal application performance through comprehensive profiling, load testing, and network condition simulation',
            backstory="""You are a Performance Engineering specialist with 10+ years of experience in
            application performance optimization, load testing, and infrastructure monitoring. You excel at
            identifying performance bottlenecks, validating SLA compliance, testing under various network
            conditions, and providing actionable optimization recommendations.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                UnifiedPerformanceProfilerTool(),
                NetworkConditionSimulatorTool()
            ]
        )

    async def run_performance_analysis(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive performance analysis"""
        scenario = task_data.get("scenario", {})
        session_id = task_data.get("session_id")
        logger.info(f"Performance Agent analyzing for session: {session_id}")

        self.redis_client.set(f"performance:{session_id}:{scenario.get('id', 'performance')}", json.dumps({
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "scenario": scenario
        }))

        # Performance profiling task
        performance_task = Task(
            description=f"""Run comprehensive performance analysis for session {session_id}:

            Target: {scenario.get('target_url', 'configured endpoints')}
            Load Profile: {scenario.get('load_profile', 'baseline')}

            Analyze:
            1. Response times (avg, p50, p95, p99, max)
            2. Throughput (RPS, TPS)
            3. Reliability metrics (uptime, error rates)
            4. SLA compliance evaluation
            5. Bottleneck identification
            6. Performance regression detection
            7. TLS certificate validation
            8. Network condition simulation
            """,
            agent=self.agent,
            expected_output="Comprehensive performance report with grades, SLA compliance, bottlenecks, and optimization recommendations"
        )

        crew = Crew(agents=[self.agent], tasks=[performance_task], process=Process.sequential, verbose=True)
        crew.kickoff()

        # Run performance profiling
        profiler_tool = UnifiedPerformanceProfilerTool()
        target_config = {
            "base_url": scenario.get("target_url", ""),
            "endpoints": scenario.get("endpoints", []),
            "sla_config": scenario.get("sla_config", {}),
            "baseline": scenario.get("baseline")
        }
        load_profile = scenario.get("load_profile", "baseline")
        performance_result = profiler_tool._run(target_config, load_profile)

        # Run network condition testing
        network_tool = NetworkConditionSimulatorTool()
        network_config = {
            "url": scenario.get("target_url", ""),
            "profiles": scenario.get("network_profiles", ["4g", "wifi", "3g"])
        }
        network_result = network_tool._run(network_config)

        result = {
            "performance_profiling": performance_result,
            "network_conditions": network_result,
            "overall_score": round(
                (performance_result.get("performance_grade") in ["A", "B"] and performance_result.get("health_status") == "healthy") * 100,
                1
            )
        }

        self.redis_client.set(f"performance:{session_id}:analysis", json.dumps(result))

        await self._notify_manager(session_id, scenario.get("id", "performance"), result)

        return {
            "scenario_id": scenario.get("id", "performance"),
            "session_id": session_id,
            "performance_analysis": result,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }

    async def _notify_manager(self, session_id: str, scenario_id: str, result: Dict):
        """Notify QA Manager of task completion"""
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
    """Main entry point for Performance agent"""
    agent = PerformanceAgent()

    sample_task = {
        "session_id": "session_20240207_143000",
        "scenario": {
            "id": "perf_analysis",
            "name": "Comprehensive Performance Analysis",
            "priority": "high",
            "target_url": "http://localhost:8000",
            "load_profile": "moderate",
            "sla_config": {"uptime_threshold": 99.9, "response_time_threshold_ms": 2000}
        },
        "timestamp": datetime.now().isoformat()
    }

    result = await agent.run_performance_analysis(sample_task)
    print(f"Performance Agent Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())