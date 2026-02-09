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
import requests
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataOrganizationReportingTool(BaseTool):
    name: str = "Data Organization & Reporting"
    description: str = "Aggregates test results from all agents, organizes data by category, and generates structured QA reports"

    def _run(self, session_id: str, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results and generate a structured QA report"""
        redis_client = redis.Redis(host='redis', port=6379, db=0)

        # Gather results from Senior and Junior agents
        senior_results = self._collect_agent_results(redis_client, f"senior:{session_id}")
        junior_results = self._collect_agent_results(redis_client, f"junior:{session_id}")

        all_results = senior_results + junior_results
        if raw_results:
            all_results.append(raw_results)

        # Categorize findings by severity
        findings = self._categorize_findings(all_results)

        # Calculate metrics
        metrics = self._calculate_metrics(all_results)

        # Generate trend analysis
        trend = self._generate_trend_analysis(redis_client, session_id, metrics)

        # Build action items
        action_items = self._build_action_items(findings)

        # Executive summary
        executive_summary = self._generate_executive_summary(metrics, findings)

        return {
            "executive_summary": executive_summary,
            "metrics": metrics,
            "findings_by_severity": findings,
            "trend_analysis": trend,
            "action_items": action_items,
            "report_generated_at": datetime.now().isoformat()
        }

    def _collect_agent_results(self, redis_client: redis.Redis, prefix: str) -> List[Dict]:
        """Scan Redis for agent result keys and parse them"""
        results = []
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match=f"{prefix}:*:result", count=100)
            for key in keys:
                data = redis_client.get(key)
                if data:
                    try:
                        results.append(json.loads(data))
                    except json.JSONDecodeError:
                        continue
            if cursor == 0:
                break
        return results

    def _categorize_findings(self, results: List[Dict]) -> Dict[str, List]:
        """Bucket findings into severity categories"""
        findings = {"critical": [], "high": [], "medium": [], "low": []}

        for result in results:
            # Pull from edge case analysis
            for area in result.get("edge_case_analysis", {}).get("high_risk_areas", []):
                findings["critical"].append({"source": "edge_case", "area": area})

            # Pull from test execution failures
            for failed in result.get("test_execution", {}).get("failed_tests", []):
                severity = "high" if "auth" in failed.get("test_name", "").lower() else "medium"
                findings[severity].append({"source": "regression", "test": failed.get("test_name"), "error": failed.get("error_message")})

            # Pull from self-healing analysis
            healing = result.get("self_healing_analysis")
            if healing and healing.get("confidence_score", 1.0) < 0.7:
                findings["high"].append({"source": "self_healing", "detail": "Low healing confidence", "score": healing.get("confidence_score")})

            # Pull from complexity assessment
            complexity = result.get("complexity_assessment", {})
            if complexity.get("complexity_level") == "high":
                findings["medium"].append({"source": "complexity", "level": "high", "scenario": result.get("scenario_id")})

            # Recommendations as low-severity informational items
            for rec in result.get("recommendations", []):
                findings["low"].append({"source": "recommendation", "detail": rec})

        return findings

    def _calculate_metrics(self, results: List[Dict]) -> Dict[str, float]:
        """Compute summary metrics across all results"""
        total_tests = 0
        passed = 0
        failed = 0
        coverage_scores = []
        detection_times = []

        for result in results:
            exec_data = result.get("test_execution", {}).get("results", {})
            total_tests += exec_data.get("total_tests", 0)
            passed += exec_data.get("passed", 0)
            failed += exec_data.get("failed", 0)

            mbt = result.get("model_based_testing", {})
            if mbt.get("coverage_potential"):
                coverage_scores.append(mbt["coverage_potential"])

            exec_time = result.get("test_execution", {}).get("execution_time")
            if exec_time:
                detection_times.append(exec_time)

        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0.0
        failure_rate = (failed / total_tests * 100) if total_tests > 0 else 0.0
        coverage = float(np.mean(coverage_scores) * 100) if coverage_scores else 0.0
        mttr = float(np.mean(detection_times)) if detection_times else 0.0

        return {
            "pass_rate": round(pass_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "coverage": round(coverage, 2),
            "mttr": round(mttr, 2),
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed
        }

    def _generate_trend_analysis(self, redis_client: redis.Redis, session_id: str, current_metrics: Dict) -> Dict[str, str]:
        """Compare current session metrics against historical data"""
        previous_report = redis_client.get("analyst:latest_report_metrics")
        if previous_report:
            try:
                prev = json.loads(previous_report)
                delta = current_metrics["pass_rate"] - prev.get("pass_rate", 0)
                if delta > 0:
                    comparison = f"Pass rate improved by {delta:.1f}%"
                elif delta < 0:
                    comparison = f"Pass rate declined by {abs(delta):.1f}%"
                else:
                    comparison = "Pass rate unchanged"

                regression = "regression_detected" if current_metrics["failure_rate"] > prev.get("failure_rate", 0) else "stable"
            except json.JSONDecodeError:
                comparison = "No valid previous data"
                regression = "unknown"
        else:
            comparison = "First session — no historical data"
            regression = "baseline"

        # Store current metrics for future comparison
        redis_client.set("analyst:latest_report_metrics", json.dumps(current_metrics))

        return {"current_vs_previous": comparison, "regression_trend": regression}

    def _build_action_items(self, findings: Dict[str, List]) -> List[Dict[str, str]]:
        """Create prioritized action items from findings"""
        items = []
        for finding in findings.get("critical", []):
            items.append({"priority": "critical", "description": f"Address critical finding in {finding.get('area', finding.get('detail', 'unknown'))}", "assigned_to": "senior"})
        for finding in findings.get("high", []):
            items.append({"priority": "high", "description": f"Investigate high-severity issue: {finding.get('test', finding.get('detail', 'unknown'))}", "assigned_to": "senior"})
        for finding in findings.get("medium", [])[:5]:
            items.append({"priority": "medium", "description": f"Review medium finding: {finding.get('detail', finding.get('scenario', 'unknown'))}", "assigned_to": "junior"})
        return items

    def _generate_executive_summary(self, metrics: Dict, findings: Dict) -> str:
        """Produce a human-readable executive summary"""
        critical_count = len(findings.get("critical", []))
        high_count = len(findings.get("high", []))
        return (
            f"QA Report: {metrics['total_tests']} tests executed — "
            f"{metrics['pass_rate']}% pass rate, {metrics['failure_rate']}% failure rate. "
            f"{critical_count} critical and {high_count} high-severity findings identified. "
            f"Test coverage at {metrics['coverage']}%."
        )


class SecurityAssessmentTool(BaseTool):
    name: str = "Security Assessment"
    description: str = "Performs security analysis including vulnerability scanning, header inspection, and compliance checking"

    EXPECTED_HEADERS = [
        "Content-Security-Policy",
        "Strict-Transport-Security",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "X-XSS-Protection",
    ]

    def _run(self, target: Dict[str, Any], scan_profile: str = "standard") -> Dict[str, Any]:
        """Run security assessment against target"""
        url = target.get("url", "")
        headers_result = self._analyze_headers(url)
        tls_result = self._assess_tls(url)
        cors_result = self._check_cors(url)
        disclosure_result = self._check_info_disclosure(url)
        owasp_result = self._evaluate_owasp_indicators(target)

        # Aggregate vulnerabilities
        vulnerabilities = []
        for h in headers_result.get("missing", []):
            vulnerabilities.append({
                "type": "missing_header",
                "severity": "medium" if h != "Strict-Transport-Security" else "high",
                "description": f"Missing security header: {h}",
                "remediation": f"Add {h} header to server responses"
            })

        for issue in tls_result.get("issues", []):
            vulnerabilities.append({
                "type": "tls_configuration",
                "severity": "high",
                "description": issue,
                "remediation": "Update TLS configuration to use TLS 1.2+ with strong cipher suites"
            })

        if cors_result.get("misconfigured"):
            vulnerabilities.append({
                "type": "cors_misconfiguration",
                "severity": "high",
                "description": cors_result["detail"],
                "remediation": "Restrict Access-Control-Allow-Origin to trusted domains"
            })

        for disclosure in disclosure_result:
            vulnerabilities.append({
                "type": "information_disclosure",
                "severity": "low",
                "description": disclosure,
                "remediation": "Remove or mask server version and technology information"
            })

        vulnerabilities.extend(owasp_result)

        # Calculate score
        deductions = sum(0.15 if v["severity"] == "critical" else 0.10 if v["severity"] == "high" else 0.05 if v["severity"] == "medium" else 0.02 for v in vulnerabilities)
        score = max(0.0, min(1.0, 1.0 - deductions))

        if score >= 0.9:
            risk_level = "low"
        elif score >= 0.7:
            risk_level = "medium"
        elif score >= 0.5:
            risk_level = "high"
        else:
            risk_level = "critical"

        recommendations = self._build_recommendations(vulnerabilities)

        return {
            "security_score": round(score, 2),
            "risk_level": risk_level,
            "header_analysis": headers_result,
            "tls_assessment": tls_result,
            "vulnerabilities": vulnerabilities,
            "compliance_status": {
                "owasp_top_10": {v["type"]: v["severity"] for v in owasp_result},
                "headers_best_practice": len(headers_result.get("missing", [])) == 0
            },
            "recommendations": recommendations
        }

    def _analyze_headers(self, url: str) -> Dict[str, Any]:
        """Inspect HTTP security headers"""
        present = []
        missing = []
        misconfigured = []

        if not url:
            return {"present": [], "missing": self.EXPECTED_HEADERS, "misconfigured": []}

        try:
            resp = requests.get(url, timeout=10, allow_redirects=True)
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}

            for header in self.EXPECTED_HEADERS:
                if header.lower() in resp_headers:
                    present.append(header)
                    # Check for weak values
                    val = resp_headers[header.lower()]
                    if header == "X-Frame-Options" and val.lower() not in ("deny", "sameorigin"):
                        misconfigured.append({"header": header, "value": val, "issue": "Should be DENY or SAMEORIGIN"})
                    if header == "X-Content-Type-Options" and val.lower() != "nosniff":
                        misconfigured.append({"header": header, "value": val, "issue": "Should be nosniff"})
                else:
                    missing.append(header)
        except requests.RequestException:
            missing = list(self.EXPECTED_HEADERS)

        return {"present": present, "missing": missing, "misconfigured": misconfigured}

    def _assess_tls(self, url: str) -> Dict[str, Any]:
        """Assess TLS/SSL configuration"""
        result = {"grade": "unknown", "issues": []}
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.scheme != "https":
                result["grade"] = "F"
                result["issues"].append("Site does not use HTTPS")
                return result

            hostname = parsed.hostname
            port = parsed.port or 443
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    protocol = ssock.version()
                    if protocol and "TLSv1.0" in protocol:
                        result["issues"].append("TLS 1.0 is deprecated")
                    if protocol and "TLSv1.1" in protocol:
                        result["issues"].append("TLS 1.1 is deprecated")
                    result["protocol"] = protocol

            if not result["issues"]:
                result["grade"] = "A"
            else:
                result["grade"] = "C"
        except Exception as e:
            result["grade"] = "F"
            result["issues"].append(f"TLS connection failed: {str(e)}")

        return result

    def _check_cors(self, url: str) -> Dict[str, Any]:
        """Verify CORS configuration"""
        result = {"misconfigured": False, "detail": ""}
        if not url:
            return result
        try:
            resp = requests.options(url, headers={"Origin": "https://evil.example.com"}, timeout=10)
            acao = resp.headers.get("Access-Control-Allow-Origin", "")
            if acao == "*":
                result["misconfigured"] = True
                result["detail"] = "Access-Control-Allow-Origin is set to wildcard (*)"
            elif "evil.example.com" in acao:
                result["misconfigured"] = True
                result["detail"] = "CORS reflects arbitrary Origin header"
        except requests.RequestException:
            pass
        return result

    def _check_info_disclosure(self, url: str) -> List[str]:
        """Check for information disclosure in response headers"""
        disclosures = []
        if not url:
            return disclosures
        try:
            resp = requests.get(url, timeout=10)
            server = resp.headers.get("Server", "")
            if server and any(tok in server.lower() for tok in ["apache", "nginx", "iis", "express"]):
                disclosures.append(f"Server header discloses technology: {server}")
            powered = resp.headers.get("X-Powered-By", "")
            if powered:
                disclosures.append(f"X-Powered-By header discloses: {powered}")
        except requests.RequestException:
            pass
        return disclosures

    def _evaluate_owasp_indicators(self, target: Dict[str, Any]) -> List[Dict[str, str]]:
        """Check for OWASP Top 10 indicators based on target configuration"""
        indicators = []
        url = target.get("url", "")

        # A03:2021 Injection — check if test inputs are reflected
        if url:
            try:
                test_payload = "<script>alert(1)</script>"
                resp = requests.get(url, params={"q": test_payload}, timeout=10)
                if test_payload in resp.text:
                    indicators.append({
                        "type": "A03_injection_xss",
                        "severity": "critical",
                        "description": "Reflected XSS: user input echoed without encoding",
                        "remediation": "Encode all user input in output contexts"
                    })
            except requests.RequestException:
                pass

        # A01:2021 Broken Access Control — test for directory listing
        if url:
            try:
                resp = requests.get(url.rstrip("/") + "/", timeout=10)
                if "Index of /" in resp.text or "Directory listing" in resp.text.lower():
                    indicators.append({
                        "type": "A01_broken_access_control",
                        "severity": "medium",
                        "description": "Directory listing is enabled",
                        "remediation": "Disable directory listing on the web server"
                    })
            except requests.RequestException:
                pass

        return indicators

    def _build_recommendations(self, vulnerabilities: List[Dict]) -> List[str]:
        """Deduplicate and prioritize recommendations"""
        seen = set()
        recs = []
        for v in sorted(vulnerabilities, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["severity"], 4)):
            if v["remediation"] not in seen:
                recs.append(v["remediation"])
                seen.add(v["remediation"])
        return recs


class PerformanceProfilingTool(BaseTool):
    name: str = "Performance Profiler"
    description: str = "Profiles application performance including response times, throughput, resource utilization, and bottleneck detection"

    LOAD_PROFILES = {
        "baseline": {"concurrent": 1, "requests_per_endpoint": 5},
        "moderate": {"concurrent": 5, "requests_per_endpoint": 20},
        "stress": {"concurrent": 10, "requests_per_endpoint": 50},
    }

    def _run(self, target_config: Dict[str, Any], load_profile: str = "baseline") -> Dict[str, Any]:
        """Profile performance for given endpoints"""
        endpoints = target_config.get("endpoints", [])
        base_url = target_config.get("base_url", "")
        if not endpoints and base_url:
            endpoints = [base_url]

        profile = self.LOAD_PROFILES.get(load_profile, self.LOAD_PROFILES["baseline"])
        num_requests = profile["requests_per_endpoint"]

        all_latencies = []
        endpoint_results = {}

        for endpoint in endpoints:
            latencies = []
            errors = 0
            for _ in range(num_requests):
                try:
                    start = time.time()
                    resp = requests.get(endpoint, timeout=30)
                    elapsed = (time.time() - start) * 1000
                    latencies.append(elapsed)
                    if resp.status_code >= 400:
                        errors += 1
                except requests.RequestException:
                    errors += 1
                    latencies.append(30000)

            all_latencies.extend(latencies)
            sorted_lat = sorted(latencies)
            endpoint_results[endpoint] = {
                "avg_ms": round(float(np.mean(sorted_lat)), 1),
                "p95_ms": round(float(np.percentile(sorted_lat, 95)), 1),
                "error_count": errors
            }

        if not all_latencies:
            return self._empty_result()

        sorted_all = sorted(all_latencies)
        avg = float(np.mean(sorted_all))
        p50 = float(np.percentile(sorted_all, 50))
        p95 = float(np.percentile(sorted_all, 95))
        p99 = float(np.percentile(sorted_all, 99))
        max_ms = float(max(sorted_all))

        total_time_s = sum(all_latencies) / 1000
        rps = len(all_latencies) / total_time_s if total_time_s > 0 else 0
        tps = rps  # 1 transaction per request in simple model

        # Detect bottlenecks
        bottlenecks = self._detect_bottlenecks(endpoint_results, p95)

        # Grade
        grade = self._calculate_grade(avg, p95, p99)

        # Baseline comparison
        baseline_comparison = self._compare_baseline(target_config, {"avg_ms": avg, "p95_ms": p95})

        recommendations = []
        if p95 > 2000:
            recommendations.append("P95 latency exceeds 2s — investigate slow queries and add caching")
        if p99 > 5000:
            recommendations.append("P99 tail latency is very high — check for resource contention")
        if bottlenecks:
            recommendations.append("Address identified bottleneck endpoints before scaling")
        if grade in ("D", "F"):
            recommendations.append("Consider load testing with a dedicated tool (k6, Locust) for deeper analysis")

        return {
            "performance_grade": grade,
            "response_times": {
                "avg_ms": round(avg, 1),
                "p50_ms": round(p50, 1),
                "p95_ms": round(p95, 1),
                "p99_ms": round(p99, 1),
                "max_ms": round(max_ms, 1)
            },
            "throughput": {"rps": round(rps, 2), "tps": round(tps, 2)},
            "bottlenecks": bottlenecks,
            "regression_detected": baseline_comparison.get("regression", False),
            "baseline_comparison": baseline_comparison,
            "resource_utilization": {},
            "endpoint_breakdown": endpoint_results,
            "recommendations": recommendations
        }

    def _detect_bottlenecks(self, endpoint_results: Dict, overall_p95: float) -> List[Dict[str, str]]:
        """Identify endpoints that are significantly slower than others"""
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
        """Assign a letter grade based on response times"""
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
        """Compare against stored baseline if available"""
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

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "performance_grade": "F",
            "response_times": {"avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0, "max_ms": 0},
            "throughput": {"rps": 0, "tps": 0},
            "bottlenecks": [],
            "regression_detected": False,
            "baseline_comparison": {"improved": [], "degraded": [], "unchanged": []},
            "resource_utilization": {},
            "endpoint_breakdown": {},
            "recommendations": ["No endpoints configured for profiling"]
        }


class QAAnalystAgent:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.celery_app = Celery('qa_analyst', broker='amqp://guest:guest@rabbitmq:5672/')
        self.llm = ChatOpenAI(model=os.getenv('OPENAI_MODEL', 'gpt-4o'), temperature=0.1)

        self.agent = Agent(
            role='QA Analyst',
            goal='Organize test data into actionable reports, perform security assessments, and profile performance',
            backstory="""You are a QA Analyst with 8+ years of experience in test analytics
            and security auditing. You excel at transforming raw test data into clear, prioritized
            reports and ensuring applications meet performance and security benchmarks.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                DataOrganizationReportingTool(),
                SecurityAssessmentTool(),
                PerformanceProfilingTool()
            ]
        )

    async def analyze_and_report(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all agents and produce a structured report"""
        scenario = task_data.get("scenario", {})
        session_id = task_data.get("session_id")
        logger.info(f"QA Analyst generating report for session: {session_id}")

        self.redis_client.set(f"analyst:{session_id}:{scenario.get('id', 'report')}", json.dumps({
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "scenario": scenario
        }))

        report_task = Task(
            description=f"""Aggregate and analyze test results for session {session_id}:

            Scenario: {scenario.get('name', 'Full Report')}

            Produce:
            1. Executive summary of all test outcomes
            2. Categorized findings by severity
            3. Key metrics (pass rate, coverage, MTTR)
            4. Trend analysis against historical data
            5. Prioritized action items
            """,
            agent=self.agent,
            expected_output="Structured QA report with metrics, findings, and recommendations"
        )

        crew = Crew(agents=[self.agent], tasks=[report_task], process=Process.sequential, verbose=True)
        crew.kickoff()

        tool = DataOrganizationReportingTool()
        report = tool._run(session_id, task_data.get("raw_results", {}))

        self.redis_client.set(f"analyst:{session_id}:report", json.dumps(report))

        await self._notify_manager(session_id, scenario.get("id", "report"), report)

        return {
            "scenario_id": scenario.get("id", "report"),
            "session_id": session_id,
            "report": report,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }

    async def run_security_assessment(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run security assessment"""
        scenario = task_data.get("scenario", {})
        session_id = task_data.get("session_id")
        logger.info(f"QA Analyst running security assessment for session: {session_id}")

        self.redis_client.set(f"analyst:{session_id}:{scenario.get('id', 'security')}", json.dumps({
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "scenario": scenario
        }))

        security_task = Task(
            description=f"""Perform security assessment for session {session_id}:

            Target: {scenario.get('target_url', 'configured endpoints')}

            Analyze:
            1. HTTP security headers
            2. TLS/SSL configuration
            3. CORS policy
            4. Information disclosure
            5. OWASP Top 10 indicators
            6. Input validation posture
            """,
            agent=self.agent,
            expected_output="Security assessment with vulnerability findings and compliance status"
        )

        crew = Crew(agents=[self.agent], tasks=[security_task], process=Process.sequential, verbose=True)
        crew.kickoff()

        tool = SecurityAssessmentTool()
        target = {"url": scenario.get("target_url", "")}
        scan_profile = scenario.get("scan_profile", "standard")
        result = tool._run(target, scan_profile)

        self.redis_client.set(f"analyst:{session_id}:security", json.dumps(result))

        await self._notify_manager(session_id, scenario.get("id", "security"), result)

        return {
            "scenario_id": scenario.get("id", "security"),
            "session_id": session_id,
            "security_assessment": result,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }

    async def profile_performance(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run performance profiling"""
        scenario = task_data.get("scenario", {})
        session_id = task_data.get("session_id")
        logger.info(f"QA Analyst profiling performance for session: {session_id}")

        self.redis_client.set(f"analyst:{session_id}:{scenario.get('id', 'performance')}", json.dumps({
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "scenario": scenario
        }))

        perf_task = Task(
            description=f"""Profile application performance for session {session_id}:

            Target: {scenario.get('target_url', 'configured endpoints')}
            Load Profile: {scenario.get('load_profile', 'baseline')}

            Measure:
            1. Response times (avg, p50, p95, p99)
            2. Throughput (RPS, TPS)
            3. Bottleneck identification
            4. Performance regression detection
            5. Per-endpoint breakdown
            """,
            agent=self.agent,
            expected_output="Performance profile with grade, bottlenecks, and recommendations"
        )

        crew = Crew(agents=[self.agent], tasks=[perf_task], process=Process.sequential, verbose=True)
        crew.kickoff()

        tool = PerformanceProfilingTool()
        target_config = {
            "base_url": scenario.get("target_url", ""),
            "endpoints": scenario.get("endpoints", []),
            "baseline": scenario.get("baseline")
        }
        load_profile = scenario.get("load_profile", "baseline")
        result = tool._run(target_config, load_profile)

        self.redis_client.set(f"analyst:{session_id}:performance", json.dumps(result))

        await self._notify_manager(session_id, scenario.get("id", "performance"), result)

        return {
            "scenario_id": scenario.get("id", "performance"),
            "session_id": session_id,
            "performance_profile": result,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }

    async def generate_comprehensive_report(self, session_id: str) -> Dict[str, Any]:
        """Aggregate all analyst outputs into a single comprehensive report"""
        logger.info(f"QA Analyst generating comprehensive report for session: {session_id}")

        # Gather individual reports from Redis
        report_data = self._get_redis_json(f"analyst:{session_id}:report")
        reliability_data = self._get_redis_json(f"sre:{session_id}:reliability")
        security_data = self._get_redis_json(f"analyst:{session_id}:security")
        performance_data = self._get_redis_json(f"analyst:{session_id}:performance")

        synthesis_task = Task(
            description=f"""Synthesize a comprehensive QA report for session {session_id}:

            Test Report: {json.dumps(report_data) if report_data else 'Not available'}
            Reliability: {json.dumps(reliability_data) if reliability_data else 'Not available'}
            Security: {json.dumps(security_data) if security_data else 'Not available'}
            Performance: {json.dumps(performance_data) if performance_data else 'Not available'}

            Produce a cross-cutting analysis identifying:
            1. Correlations between security issues and performance
            2. Reliability risks stemming from test failures
            3. Overall quality posture and release readiness
            """,
            agent=self.agent,
            expected_output="Comprehensive cross-cutting QA report"
        )

        crew = Crew(agents=[self.agent], tasks=[synthesis_task], process=Process.sequential, verbose=True)
        crew.kickoff()

        # Cross-cutting analysis
        cross_cutting = []
        if security_data and security_data.get("risk_level") in ("high", "critical"):
            cross_cutting.append("Security vulnerabilities may impact reliability — prioritize remediation before scaling")
        if performance_data and performance_data.get("regression_detected"):
            cross_cutting.append("Performance regression detected — correlate with recent code changes")
        if report_data and report_data.get("metrics", {}).get("failure_rate", 0) > 20:
            cross_cutting.append("High test failure rate — not recommended for release until stabilized")

        comprehensive = {
            "session_id": session_id,
            "generated_at": datetime.now().isoformat(),
            "test_report": report_data,
            "reliability_assessment": reliability_data,
            "security_assessment": security_data,
            "performance_profile": performance_data,
            "cross_cutting_analysis": cross_cutting,
            "release_readiness": self._assess_release_readiness(report_data, reliability_data, security_data, performance_data)
        }

        self.redis_client.set(f"analyst:{session_id}:comprehensive_report", json.dumps(comprehensive))

        await self._notify_manager(session_id, "comprehensive_report", comprehensive)

        return comprehensive

    def _assess_release_readiness(self, report: Optional[Dict], reliability: Optional[Dict],
                                   security: Optional[Dict], performance: Optional[Dict]) -> Dict[str, Any]:
        """Determine overall release readiness"""
        blockers = []
        warnings = []

        if report:
            if report.get("metrics", {}).get("failure_rate", 0) > 10:
                blockers.append("Test failure rate exceeds 10%")
            if len(report.get("findings_by_severity", {}).get("critical", [])) > 0:
                blockers.append("Unresolved critical findings")

        if reliability:
            if reliability.get("health_status") == "unhealthy":
                blockers.append("Site health status is unhealthy")
            if not reliability.get("sla_compliance", {}).get("met", True):
                warnings.append("SLA compliance not met")

        if security:
            if security.get("risk_level") in ("critical", "high"):
                blockers.append(f"Security risk level is {security['risk_level']}")

        if performance:
            if performance.get("performance_grade") in ("D", "F"):
                warnings.append(f"Performance grade is {performance['performance_grade']}")
            if performance.get("regression_detected"):
                warnings.append("Performance regression detected")

        ready = len(blockers) == 0
        return {
            "ready": ready,
            "verdict": "GO" if ready and not warnings else "GO_WITH_WARNINGS" if ready else "NO_GO",
            "blockers": blockers,
            "warnings": warnings
        }

    def _get_redis_json(self, key: str) -> Optional[Dict]:
        """Safely retrieve and parse JSON from Redis"""
        data = self.redis_client.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None

    async def _notify_manager(self, session_id: str, scenario_id: str, result: Dict):
        """Notify QA Manager of task completion"""
        notification = {
            "agent": "qa_analyst",
            "session_id": session_id,
            "scenario_id": scenario_id,
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.publish(f"manager:{session_id}:notifications", json.dumps(notification))


async def main():
    """Main entry point for QA Analyst agent"""
    analyst = QAAnalystAgent()

    sample_task = {
        "session_id": "session_20240207_143000",
        "scenario": {
            "id": "rel_006",
            "name": "Site Reliability Assessment",
            "priority": "high",
            "target_url": "http://localhost:8000/health",
            "sla_config": {"num_probes": 5, "uptime_threshold": 99.9, "response_time_threshold_ms": 2000}
        },
        "timestamp": datetime.now().isoformat()
    }

    result = await analyst.assess_reliability(sample_task)
    print(f"QA Analyst Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
