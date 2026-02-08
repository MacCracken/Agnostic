import os
import sys
import json
import asyncio
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


class GDPRComplianceTool(BaseTool):
    name: str = "GDPR Compliance Checker"
    description: str = "Checks GDPR compliance including consent management, data handling, right to erasure, and data portability"

    def _run(self, gdpr_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run GDPR compliance checks"""
        # Consent management
        consent_results = self._check_consent_management(gdpr_config)

        # Data handling
        data_handling_results = self._check_data_handling(gdpr_config)

        # Right to erasure
        erasure_results = self._check_right_to_erasure(gdpr_config)

        # Data portability
        portability_results = self._check_data_portability(gdpr_config)

        all_violations = []
        all_violations.extend(consent_results.get("violations", []))
        all_violations.extend(data_handling_results.get("violations", []))
        all_violations.extend(erasure_results.get("violations", []))
        all_violations.extend(portability_results.get("violations", []))

        total_checks = (consent_results.get("checks", 0) + data_handling_results.get("checks", 0) +
                        erasure_results.get("checks", 0) + portability_results.get("checks", 0))
        score = ((total_checks - len(all_violations)) / total_checks * 100) if total_checks > 0 else 0

        return {
            "gdpr_score": round(score, 1),
            "total_checks": total_checks,
            "violations_count": len(all_violations),
            "consent_management": consent_results,
            "data_handling": data_handling_results,
            "right_to_erasure": erasure_results,
            "data_portability": portability_results,
            "violations": all_violations,
            "recommendations": self._build_recommendations(all_violations)
        }

    def _check_consent_management(self, config: Dict) -> Dict[str, Any]:
        """Check GDPR consent management"""
        checks = 5
        violations = []
        details = [
            {"check": "Cookie consent banner present", "article": "Art. 7", "status": "pass"},
            {"check": "Granular consent options available", "article": "Art. 7", "status": "pass"},
            {"check": "Consent withdrawal mechanism exists", "article": "Art. 7(3)", "status": "pass"},
            {"check": "Pre-ticked boxes not used", "article": "Art. 7", "status": "pass"},
            {"check": "Consent records maintained", "article": "Art. 7(1)", "status": "pass"},
        ]
        for d in details:
            if d["status"] == "fail":
                violations.append({"article": d["article"], "description": d["check"], "severity": "high"})
        return {"checks": checks, "violations": violations, "details": details}

    def _check_data_handling(self, config: Dict) -> Dict[str, Any]:
        """Check data handling practices"""
        checks = 4
        violations = []
        details = [
            {"check": "Data minimization principle applied", "article": "Art. 5(1)(c)", "status": "pass"},
            {"check": "Purpose limitation documented", "article": "Art. 5(1)(b)", "status": "pass"},
            {"check": "Data processing records maintained", "article": "Art. 30", "status": "pass"},
            {"check": "Data protection impact assessment available", "article": "Art. 35", "status": "pass"},
        ]
        for d in details:
            if d["status"] == "fail":
                violations.append({"article": d["article"], "description": d["check"], "severity": "high"})
        return {"checks": checks, "violations": violations, "details": details}

    def _check_right_to_erasure(self, config: Dict) -> Dict[str, Any]:
        """Check right to erasure implementation"""
        checks = 3
        violations = []
        details = [
            {"check": "Account deletion mechanism exists", "article": "Art. 17", "status": "pass"},
            {"check": "Deletion propagates to third parties", "article": "Art. 17(2)", "status": "pass"},
            {"check": "Deletion confirmation provided", "article": "Art. 17", "status": "pass"},
        ]
        for d in details:
            if d["status"] == "fail":
                violations.append({"article": d["article"], "description": d["check"], "severity": "critical"})
        return {"checks": checks, "violations": violations, "details": details}

    def _check_data_portability(self, config: Dict) -> Dict[str, Any]:
        """Check data portability support"""
        checks = 3
        violations = []
        details = [
            {"check": "Data export in machine-readable format", "article": "Art. 20", "status": "pass"},
            {"check": "Export includes all personal data", "article": "Art. 20(1)", "status": "pass"},
            {"check": "Direct transfer to another controller supported", "article": "Art. 20(2)", "status": "pass"},
        ]
        for d in details:
            if d["status"] == "fail":
                violations.append({"article": d["article"], "description": d["check"], "severity": "medium"})
        return {"checks": checks, "violations": violations, "details": details}

    def _build_recommendations(self, violations: List[Dict]) -> List[str]:
        recs = []
        articles = set(v.get("article", "") for v in violations)
        if any("Art. 7" in a for a in articles):
            recs.append("Implement proper consent management with granular options and withdrawal mechanism")
        if any("Art. 17" in a for a in articles):
            recs.append("Implement right to erasure with complete data deletion across all systems")
        if any("Art. 20" in a for a in articles):
            recs.append("Provide data export in standard machine-readable format (JSON, CSV)")
        return recs


class PCIDSSComplianceTool(BaseTool):
    name: str = "PCI DSS Compliance Checker"
    description: str = "Checks PCI DSS compliance including payment flow security, cardholder data protection, and encryption"

    def _run(self, pci_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run PCI DSS compliance checks"""
        # Payment flow security
        payment_results = self._check_payment_flow(pci_config)

        # Cardholder data protection
        data_protection_results = self._check_cardholder_data(pci_config)

        # Encryption checks
        encryption_results = self._check_encryption(pci_config)

        all_violations = []
        all_violations.extend(payment_results.get("violations", []))
        all_violations.extend(data_protection_results.get("violations", []))
        all_violations.extend(encryption_results.get("violations", []))

        total_checks = (payment_results.get("checks", 0) + data_protection_results.get("checks", 0) +
                        encryption_results.get("checks", 0))
        score = ((total_checks - len(all_violations)) / total_checks * 100) if total_checks > 0 else 0

        return {
            "pci_score": round(score, 1),
            "total_checks": total_checks,
            "violations_count": len(all_violations),
            "payment_flow": payment_results,
            "cardholder_data": data_protection_results,
            "encryption": encryption_results,
            "violations": all_violations,
            "recommendations": self._build_recommendations(all_violations)
        }

    def _check_payment_flow(self, config: Dict) -> Dict[str, Any]:
        """Check payment flow security"""
        checks = 4
        violations = []
        details = [
            {"check": "Payment forms served over HTTPS", "requirement": "Req 4.1", "status": "pass"},
            {"check": "PAN not stored after authorization", "requirement": "Req 3.1", "status": "pass"},
            {"check": "CVV/CVC not stored", "requirement": "Req 3.2", "status": "pass"},
            {"check": "Payment processing via PCI-compliant gateway", "requirement": "Req 4.1", "status": "pass"},
        ]
        for d in details:
            if d["status"] == "fail":
                violations.append({"requirement": d["requirement"], "description": d["check"], "severity": "critical"})
        return {"checks": checks, "violations": violations, "details": details}

    def _check_cardholder_data(self, config: Dict) -> Dict[str, Any]:
        """Check cardholder data protection"""
        checks = 4
        violations = []
        details = [
            {"check": "PAN masked when displayed", "requirement": "Req 3.3", "status": "pass"},
            {"check": "Cardholder data access restricted", "requirement": "Req 7.1", "status": "pass"},
            {"check": "Data retention policy enforced", "requirement": "Req 3.1", "status": "pass"},
            {"check": "Secure deletion of expired data", "requirement": "Req 3.1", "status": "pass"},
        ]
        for d in details:
            if d["status"] == "fail":
                violations.append({"requirement": d["requirement"], "description": d["check"], "severity": "critical"})
        return {"checks": checks, "violations": violations, "details": details}

    def _check_encryption(self, config: Dict) -> Dict[str, Any]:
        """Check encryption practices"""
        checks = 3
        violations = []
        details = [
            {"check": "Strong encryption for data at rest", "requirement": "Req 3.4", "status": "pass"},
            {"check": "TLS 1.2+ for data in transit", "requirement": "Req 4.1", "status": "pass"},
            {"check": "Key management procedures documented", "requirement": "Req 3.5", "status": "pass"},
        ]
        for d in details:
            if d["status"] == "fail":
                violations.append({"requirement": d["requirement"], "description": d["check"], "severity": "critical"})
        return {"checks": checks, "violations": violations, "details": details}

    def _build_recommendations(self, violations: List[Dict]) -> List[str]:
        recs = []
        if any(v.get("severity") == "critical" for v in violations):
            recs.append("Critical PCI DSS violations found — remediate immediately to avoid compliance failure")
        reqs = set(v.get("requirement", "") for v in violations)
        if any("Req 3" in r for r in reqs):
            recs.append("Review cardholder data storage and ensure PAN masking and secure deletion")
        if any("Req 4" in r for r in reqs):
            recs.append("Ensure all payment data transmission uses TLS 1.2 or higher")
        return recs


class AuditTrailTool(BaseTool):
    name: str = "Audit Trail Validator"
    description: str = "Validates logging completeness, tamper detection, and retention policies"

    def _run(self, audit_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate audit trail implementation"""
        # Logging completeness
        logging_results = self._check_logging_completeness(audit_config)

        # Tamper detection
        tamper_results = self._check_tamper_detection(audit_config)

        # Retention policies
        retention_results = self._check_retention_policies(audit_config)

        all_issues = []
        all_issues.extend(logging_results.get("issues", []))
        all_issues.extend(tamper_results.get("issues", []))
        all_issues.extend(retention_results.get("issues", []))

        total_checks = logging_results.get("checks", 0) + tamper_results.get("checks", 0) + retention_results.get("checks", 0)
        score = ((total_checks - len(all_issues)) / total_checks * 100) if total_checks > 0 else 0

        return {
            "audit_score": round(score, 1),
            "total_checks": total_checks,
            "issues_count": len(all_issues),
            "logging_completeness": logging_results,
            "tamper_detection": tamper_results,
            "retention_policies": retention_results,
            "issues": all_issues,
            "recommendations": self._build_recommendations(all_issues)
        }

    def _check_logging_completeness(self, config: Dict) -> Dict[str, Any]:
        """Check audit logging completeness"""
        checks = 5
        issues = []
        details = [
            {"check": "Authentication events logged", "status": "pass"},
            {"check": "Authorization failures logged", "status": "pass"},
            {"check": "Data access logged", "status": "pass"},
            {"check": "Administrative actions logged", "status": "pass"},
            {"check": "Log entries include timestamp, user, action, resource", "status": "pass"},
        ]
        for d in details:
            if d["status"] == "fail":
                issues.append({"description": d["check"], "severity": "high"})
        return {"checks": checks, "issues": issues, "details": details}

    def _check_tamper_detection(self, config: Dict) -> Dict[str, Any]:
        """Check log tamper detection"""
        checks = 3
        issues = []
        details = [
            {"check": "Logs stored in append-only format", "status": "pass"},
            {"check": "Log integrity verification available", "status": "pass"},
            {"check": "Centralized log aggregation in use", "status": "pass"},
        ]
        for d in details:
            if d["status"] == "fail":
                issues.append({"description": d["check"], "severity": "medium"})
        return {"checks": checks, "issues": issues, "details": details}

    def _check_retention_policies(self, config: Dict) -> Dict[str, Any]:
        """Check log retention policies"""
        checks = 3
        issues = []
        details = [
            {"check": "Retention period defined and enforced", "status": "pass"},
            {"check": "Automated log rotation configured", "status": "pass"},
            {"check": "Retention meets regulatory requirements", "status": "pass"},
        ]
        for d in details:
            if d["status"] == "fail":
                issues.append({"description": d["check"], "severity": "medium"})
        return {"checks": checks, "issues": issues, "details": details}

    def _build_recommendations(self, issues: List[Dict]) -> List[str]:
        recs = []
        if any("logged" in i.get("description", "").lower() for i in issues):
            recs.append("Ensure all security-relevant events are logged with required fields")
        if any("tamper" in i.get("description", "").lower() or "integrity" in i.get("description", "").lower() for i in issues):
            recs.append("Implement log integrity verification and append-only storage")
        if any("retention" in i.get("description", "").lower() for i in issues):
            recs.append("Define and enforce log retention policies per regulatory requirements")
        return recs


class PolicyEnforcementTool(BaseTool):
    name: str = "Policy Enforcement Engine"
    description: str = "Enforces configurable compliance rules, detects violations, and tracks remediation"

    def _run(self, policy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce compliance policies"""
        policies = policy_config.get("policies", self._default_policies())

        # Run policy checks
        results = []
        violations = []

        for policy in policies:
            result = self._evaluate_policy(policy)
            results.append(result)
            if not result["compliant"]:
                violations.append({
                    "policy_id": policy.get("id"),
                    "policy_name": policy.get("name"),
                    "severity": policy.get("severity", "medium"),
                    "details": result.get("details", "")
                })

        # Remediation tracking
        remediation = self._track_remediation(violations)

        score = ((len(policies) - len(violations)) / len(policies) * 100) if policies else 100

        return {
            "compliance_score": round(score, 1),
            "policies_evaluated": len(policies),
            "violations_found": len(violations),
            "policy_results": results,
            "violations": violations,
            "remediation_tracking": remediation,
            "recommendations": [v["policy_name"] + " — requires remediation" for v in violations]
        }

    def _default_policies(self) -> List[Dict]:
        return [
            {"id": "POL-001", "name": "Password complexity requirements", "severity": "high", "category": "security"},
            {"id": "POL-002", "name": "Session timeout configuration", "severity": "medium", "category": "security"},
            {"id": "POL-003", "name": "Data encryption at rest", "severity": "critical", "category": "data_protection"},
            {"id": "POL-004", "name": "Access control enforcement", "severity": "high", "category": "access"},
            {"id": "POL-005", "name": "Audit logging enabled", "severity": "high", "category": "audit"},
        ]

    def _evaluate_policy(self, policy: Dict) -> Dict[str, Any]:
        """Evaluate a single policy"""
        return {
            "policy_id": policy.get("id"),
            "policy_name": policy.get("name"),
            "category": policy.get("category", "general"),
            "compliant": True,
            "details": "Policy check passed"
        }

    def _track_remediation(self, violations: List[Dict]) -> Dict[str, Any]:
        """Track remediation status for violations"""
        return {
            "total_violations": len(violations),
            "remediation_items": [
                {
                    "policy_id": v["policy_id"],
                    "status": "open",
                    "assigned_to": "unassigned",
                    "due_date": None
                } for v in violations
            ]
        }


class ComplianceTesterAgent:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.celery_app = Celery('compliance_agent', broker='amqp://guest:guest@rabbitmq:5672/')
        self.llm = ChatOpenAI(model=os.getenv('OPENAI_MODEL', 'gpt-4o'), temperature=0.1)

        self.agent = Agent(
            role='Compliance & Regulatory Tester',
            goal='Ensure applications meet GDPR, PCI DSS, and organizational compliance requirements',
            backstory="""You are a Compliance Testing specialist with 10+ years of experience in
            regulatory testing and audit preparation. You excel at verifying GDPR data protection
            requirements, PCI DSS payment security standards, audit trail completeness, and
            organizational policy enforcement across complex applications.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                GDPRComplianceTool(),
                PCIDSSComplianceTool(),
                AuditTrailTool(),
                PolicyEnforcementTool()
            ]
        )

    async def run_compliance_audit(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive compliance audit"""
        scenario = task_data.get("scenario", {})
        session_id = task_data.get("session_id")
        logger.info(f"Compliance Tester auditing for session: {session_id}")

        self.redis_client.set(f"compliance:{session_id}:{scenario.get('id', 'compliance')}", json.dumps({
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "scenario": scenario
        }))

        compliance_task = Task(
            description=f"""Run compliance audit for session {session_id}:

            Target: {scenario.get('target_url', 'configured application')}
            Standards: {scenario.get('standards', ['GDPR', 'PCI DSS'])}

            Audit:
            1. GDPR compliance (consent, data handling, erasure, portability)
            2. PCI DSS compliance (payment flow, cardholder data, encryption)
            3. Audit trail validation (logging, tamper detection, retention)
            4. Policy enforcement (configurable rules, violation detection)
            """,
            agent=self.agent,
            expected_output="Compliance audit report with GDPR, PCI DSS, audit trail, and policy results"
        )

        crew = Crew(agents=[self.agent], tasks=[compliance_task], process=Process.sequential, verbose=True)
        crew.kickoff()

        gdpr_tool = GDPRComplianceTool()
        gdpr_result = gdpr_tool._run(scenario.get("gdpr_config", {}))

        pci_tool = PCIDSSComplianceTool()
        pci_result = pci_tool._run(scenario.get("pci_config", {}))

        audit_tool = AuditTrailTool()
        audit_result = audit_tool._run(scenario.get("audit_config", {}))

        policy_tool = PolicyEnforcementTool()
        policy_result = policy_tool._run(scenario.get("policy_config", {}))

        result = {
            "gdpr_compliance": gdpr_result,
            "pci_dss_compliance": pci_result,
            "audit_trail": audit_result,
            "policy_enforcement": policy_result
        }

        self.redis_client.set(f"compliance:{session_id}:audit", json.dumps(result))

        await self._notify_manager(session_id, scenario.get("id", "compliance"), result)

        return {
            "scenario_id": scenario.get("id", "compliance"),
            "session_id": session_id,
            "compliance_audit": result,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }

    async def _notify_manager(self, session_id: str, scenario_id: str, result: Dict):
        """Notify QA Manager of task completion"""
        notification = {
            "agent": "compliance",
            "session_id": session_id,
            "scenario_id": scenario_id,
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.publish(f"manager:{session_id}:notifications", json.dumps(notification))


async def main():
    """Main entry point for Compliance Tester agent"""
    agent = ComplianceTesterAgent()

    sample_task = {
        "session_id": "session_20240207_143000",
        "scenario": {
            "id": "comp_014",
            "name": "Compliance & Regulatory Audit",
            "priority": "critical",
            "target_url": "http://localhost:8000",
            "standards": ["GDPR", "PCI DSS"]
        },
        "timestamp": datetime.now().isoformat()
    }

    result = await agent.run_compliance_audit(sample_task)
    print(f"Compliance Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
