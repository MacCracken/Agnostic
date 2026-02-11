import os
import sys
import json
import asyncio
import redis
from typing import Dict, List, Any, Optional
from datetime import datetime
import chainlit as cl
from fastapi import FastAPI
import uvicorn
import logging

# Add config path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.environment import config
from chainlit.types import ThreadDict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to Python path
sys.path.append('/app')

class AgenticQAGUI:
    def __init__(self) -> None:
        self.redis_client = config.get_redis_client()
        self.active_sessions = {}
        
    async def start_new_session(self) -> str:
        """Start a new testing session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.active_sessions[session_id] = {
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "requirements": None,
            "test_plan": None,
            "results": None
        }
        return session_id
    
    async def submit_requirements(self, session_id: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Submit requirements to QA Manager"""
        try:
            # Import here to avoid circular imports
            from agents.manager.qa_manager import QAManagerAgent
            
            manager = QAManagerAgent()
            result = await manager.process_requirements(requirements)
            
            # Update session
            self.active_sessions[session_id]["requirements"] = requirements
            self.active_sessions[session_id]["test_plan"] = result.get("test_plan")
            self.active_sessions[session_id]["status"] = "planning_completed"
            
            return result
            
        except Exception as e:
            logger.error(f"Error submitting requirements: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current session status"""
        try:
            # Get status from Redis if not in active sessions
            if session_id not in self.active_sessions:
                from agents.manager.qa_manager import QAManagerAgent
                manager = QAManagerAgent()
                status = manager.get_session_status(session_id)
                return status
            
            return self.active_sessions[session_id]
            
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            return {"error": str(e), "status": "unknown"}
    
    async def get_reasoning_trace(self, session_id: str) -> List[Dict[str, Any]]:
        """Get reasoning trace for a session"""
        try:
            trace = []
            
            # Get manager notifications
            manager_notifications = self.redis_client.lrange(f"manager:{session_id}:notifications", 0, -1)
            for notification in manager_notifications:
                try:
                    data = json.loads(notification)
                    trace.append({
                        "timestamp": data.get("timestamp"),
                        "agent": data.get("agent"),
                        "type": "notification",
                        "message": f"Agent {data.get('agent')} completed task {data.get('scenario_id')}",
                        "data": data
                    })
                except json.JSONDecodeError:
                    continue
            
            # Sort by timestamp
            trace.sort(key=lambda x: x.get("timestamp", ""))
            
            return trace
            
        except Exception as e:
            logger.error(f"Error getting reasoning trace: {e}")
            return []

# Initialize GUI
gui = AgenticQAGUI()

@cl.on_chat_start
async def on_chat_start() -> Dict[str, Any]:
    """Initialize chat session"""
    await cl.Message(
        content="🤖 Welcome to the Agentic QA Team System!\n\n"
        "I'm your interface to a team of AI-powered QA agents:\n"
        "• **QA Manager**: Orchestrates test planning and verification\n"
        "• **Senior QA Engineer**: Handles complex testing and self-healing\n"
        "• **Junior QA Worker**: Executes regression tests and data generation\n"
        "• **QA Analyst**: Data reporting, security & performance analysis\n"
        "• **Site Reliability Engineer**: Reliability monitoring, database testing, infrastructure health & incident response\n"
        "• **Accessibility Tester**: WCAG compliance, screen reader compatibility, keyboard navigation & color contrast\n"
        "• **API Integration Engineer**: Schema validation, contract testing, versioning & load testing\n"
        "• **Mobile/Device QA**: Responsive design, device compatibility, network conditions & mobile UX\n"
        "• **Compliance Tester**: GDPR, PCI DSS, audit trails & policy enforcement\n"
        "• **Chaos Engineer**: Service failure injection, network partitions, resource exhaustion & recovery validation\n\n"
        "To get started, please:\n"
        "1. Upload a PR/feature document, or\n"
        "2. Describe your testing requirements\n\n"
        "What would you like to test today?"
    ).send()
    
    # Store session in user session
    session_id = await gui.start_new_session()
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("gui", gui)

@cl.on_message
async def on_message(message: cl.Message) -> Dict[str, Any]:
    """Handle incoming messages"""
    session_id = cl.user_session.get("session_id")
    gui_instance = cl.user_session.get("gui")
    
    if not session_id or not gui_instance:
        await cl.Message(
            content="❌ Session error. Please restart the chat."
        ).send()
        return
    
    # Process the message
    user_input = message.content
    
    # Check if this is a requirements submission
    if user_input.lower().startswith(("test", "verify", "check", "validate")):
        await cl.Message(
            content="🔄 Processing your requirements..."
        ).send()
        
        # Parse requirements from user input
        requirements = {
            "title": f"Testing Request - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "description": user_input,
            "business_goals": "Ensure quality and functionality",
            "constraints": "Standard testing environment",
            "priority": "high",
            "submitted_by": "web_user",
            "submitted_at": datetime.now().isoformat()
        }
        
        # Submit to QA Manager
        result = await gui_instance.submit_requirements(session_id, requirements)
        
        if "error" in result:
            await cl.Message(
                content=f"❌ Error: {result['error']}"
            ).send()
        else:
            # Display test plan
            test_plan = result.get("test_plan", {})
            
            response = f"✅ **Test Plan Created!**\n\n"
            response += f"**Session ID**: {result.get('session_id')}\n"
            response += f"**Status**: {result.get('status')}\n\n"
            
            if test_plan.get("scenarios"):
                response += "**📋 Test Scenarios:**\n"
                for scenario in test_plan["scenarios"]:
                    priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(scenario.get("priority"), "⚪")
                    assigned_agent = {"senior": "👨‍💼", "junior": "👩‍💼"}.get(scenario.get("assigned_to"), "🤖")
                    response += f"{priority_emoji} {assigned_agent} **{scenario.get('name')}** ({scenario.get('priority')})\n"
            
            if test_plan.get("acceptance_criteria"):
                response += "\n**✅ Acceptance Criteria:**\n"
                for i, criteria in enumerate(test_plan["acceptance_criteria"], 1):
                    response += f"{i}. {criteria}\n"
            
            response += f"\n**🔄 Next Steps:**\n"
            for step in result.get("next_steps", []):
                response += f"• {step}\n"
            
            await cl.Message(content=response).send()
            
            # Start monitoring progress
            await cl.Message(
                content="⏳ Monitoring test execution progress..."
            ).send()
    
    elif user_input.lower() in ("status", "progress", "how's it going?"):
        # Get session status
        status = await gui_instance.get_session_status(session_id)
        
        response = f"📊 **Session Status**\n\n"
        response += f"**Session ID**: {session_id}\n"
        response += f"**Status**: {status.get('status', 'unknown')}\n"
        
        if status.get("test_plan"):
            test_plan = status["test_plan"]
            total_scenarios = len(test_plan.get("scenarios", []))
            response += f"**Total Scenarios**: {total_scenarios}\n"
        
        if status.get("verification"):
            verification = status["verification"]
            response += f"**Verification Score**: {verification.get('overall_score', 'N/A')}\n"
            response += f"**Business Alignment**: {verification.get('business_alignment', 'N/A')}\n"
        
        await cl.Message(content=response).send()
    
    elif user_input.lower() in ("trace", "reasoning", "log"):
        # Get reasoning trace
        trace = await gui_instance.get_reasoning_trace(session_id)
        
        if not trace:
            await cl.Message(
                content="📝 No reasoning trace available yet."
            ).send()
        else:
            response = f"📝 **Reasoning Trace**\n\n"
            
            for event in trace[-10:]:  # Show last 10 events
                agent_emoji = {"manager": "👔", "senior": "👨‍💼", "junior": "👩‍💼"}.get(event.get("agent"), "🤖")
                response += f"{agent_emoji} **{event.get('agent', 'unknown')}** - {event.get('message', 'No message')}\n"
                response += f"   _{event.get('timestamp', 'No timestamp')}_\n\n"
            
            await cl.Message(content=response).send()
    
    elif user_input.lower() in ("report", "qa report"):
        # Get analyst comprehensive report
        report_data = gui_instance.redis_client.get(f"analyst:{session_id}:comprehensive_report")
        if not report_data:
            report_data = gui_instance.redis_client.get(f"analyst:{session_id}:report")

        if report_data:
            try:
                report = json.loads(report_data)
                response = "📊 **QA Analyst Report**\n\n"

                if report.get("executive_summary"):
                    response += f"**Executive Summary:** {report['executive_summary']}\n\n"
                elif report.get("test_report", {}).get("executive_summary"):
                    response += f"**Executive Summary:** {report['test_report']['executive_summary']}\n\n"

                metrics = report.get("metrics") or report.get("test_report", {}).get("metrics")
                if metrics:
                    response += "**Metrics:**\n"
                    response += f"• Pass Rate: {metrics.get('pass_rate', 'N/A')}%\n"
                    response += f"• Failure Rate: {metrics.get('failure_rate', 'N/A')}%\n"
                    response += f"• Coverage: {metrics.get('coverage', 'N/A')}%\n\n"

                readiness = report.get("release_readiness")
                if readiness:
                    verdict_emoji = {"GO": "✅", "GO_WITH_WARNINGS": "⚠️", "NO_GO": "🚫"}.get(readiness.get("verdict"), "❓")
                    response += f"**Release Readiness:** {verdict_emoji} {readiness.get('verdict', 'Unknown')}\n"
                    for b in readiness.get("blockers", []):
                        response += f"  🔴 {b}\n"
                    for w in readiness.get("warnings", []):
                        response += f"  🟡 {w}\n"

                await cl.Message(content=response).send()
            except json.JSONDecodeError:
                await cl.Message(content="❌ Could not parse report data.").send()
        else:
            await cl.Message(content="📝 No analyst report available yet.").send()

    elif user_input.lower() in ("security", "security report"):
        security_data = gui_instance.redis_client.get(f"analyst:{session_id}:security")
        if security_data:
            try:
                sec = json.loads(security_data)
                response = "🔒 **Security Assessment**\n\n"
                response += f"**Score:** {sec.get('security_score', 'N/A')} | **Risk Level:** {sec.get('risk_level', 'N/A')}\n\n"

                vulns = sec.get("vulnerabilities", [])
                if vulns:
                    response += f"**Vulnerabilities ({len(vulns)}):**\n"
                    for v in vulns[:10]:
                        sev_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(v.get("severity"), "⚪")
                        response += f"  {sev_emoji} {v.get('description', 'Unknown')}\n"

                recs = sec.get("recommendations", [])
                if recs:
                    response += "\n**Recommendations:**\n"
                    for r in recs[:5]:
                        response += f"  • {r}\n"

                await cl.Message(content=response).send()
            except json.JSONDecodeError:
                await cl.Message(content="❌ Could not parse security data.").send()
        else:
            await cl.Message(content="📝 No security assessment available yet.").send()

    elif user_input.lower() in ("performance", "perf", "performance report"):
        perf_data = gui_instance.redis_client.get(f"analyst:{session_id}:performance")
        if perf_data:
            try:
                perf = json.loads(perf_data)
                response = "⚡ **Performance Profile**\n\n"
                response += f"**Grade:** {perf.get('performance_grade', 'N/A')}\n\n"

                rt = perf.get("response_times", {})
                response += "**Response Times:**\n"
                response += f"  • Avg: {rt.get('avg_ms', 'N/A')}ms | P50: {rt.get('p50_ms', 'N/A')}ms\n"
                response += f"  • P95: {rt.get('p95_ms', 'N/A')}ms | P99: {rt.get('p99_ms', 'N/A')}ms\n\n"

                tp = perf.get("throughput", {})
                response += f"**Throughput:** {tp.get('rps', 'N/A')} req/s\n\n"

                bottlenecks = perf.get("bottlenecks", [])
                if bottlenecks:
                    response += "**Bottlenecks:**\n"
                    for b in bottlenecks:
                        response += f"  🔴 {b.get('component', 'Unknown')} — {b.get('evidence', '')}\n"

                if perf.get("regression_detected"):
                    response += "\n⚠️ **Performance regression detected**\n"

                await cl.Message(content=response).send()
            except json.JSONDecodeError:
                await cl.Message(content="❌ Could not parse performance data.").send()
        else:
            await cl.Message(content="📝 No performance profile available yet.").send()

    elif user_input.lower() in ("reliability", "sre", "reliability report"):
        rel_data = gui_instance.redis_client.get(f"sre:{session_id}:reliability")
        if rel_data:
            try:
                rel = json.loads(rel_data)
                health_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "🚫"}.get(rel.get("health_status"), "❓")
                response = "🏗️ **Site Reliability Assessment**\n\n"
                response += f"**Health:** {health_emoji} {rel.get('health_status', 'Unknown')}\n"
                response += f"**Uptime:** {rel.get('uptime_percentage', 'N/A')}%\n\n"

                lat = rel.get("latency", {})
                response += "**Latency:**\n"
                response += f"  • P50: {lat.get('p50_ms', 'N/A')}ms | P95: {lat.get('p95_ms', 'N/A')}ms | P99: {lat.get('p99_ms', 'N/A')}ms\n\n"

                sla = rel.get("sla_compliance", {})
                sla_emoji = "✅" if sla.get("met") else "🚫"
                response += f"**SLA Compliance:** {sla_emoji} {'Met' if sla.get('met') else 'Not Met'}\n"
                for v in sla.get("violations", []):
                    response += f"  🔴 {v}\n"

                risks = rel.get("reliability_risks", [])
                if risks:
                    response += "\n**Risks:**\n"
                    for r in risks:
                        response += f"  ⚠️ {r.get('risk', str(r))}\n"

                await cl.Message(content=response).send()
            except json.JSONDecodeError:
                await cl.Message(content="❌ Could not parse reliability data.").send()
        else:
            await cl.Message(content="📝 No reliability assessment available yet.").send()

    elif user_input.lower() in ("accessibility", "a11y", "accessibility report"):
        a11y_data = gui_instance.redis_client.get(f"accessibility:{session_id}:audit")
        if a11y_data:
            try:
                a11y = json.loads(a11y_data)
                response = "♿ **Accessibility Audit**\n\n"
                response += f"**Overall Score:** {a11y.get('overall_score', 'N/A')}%\n\n"

                wcag = a11y.get("wcag_compliance", {})
                response += f"**WCAG Compliance:** {wcag.get('achieved_level', 'N/A')} (score: {wcag.get('score', 'N/A')}%)\n"
                response += f"  Violations: {wcag.get('violations_count', 0)}\n\n"

                sr = a11y.get("screen_reader", {})
                response += f"**Screen Reader:** {sr.get('compatibility_score', 'N/A')}% compatible\n"

                kb = a11y.get("keyboard_navigation", {})
                response += f"**Keyboard Navigation:** {kb.get('keyboard_score', 'N/A')}%\n"

                color = a11y.get("color_contrast", {})
                response += f"**Color Contrast:** {color.get('contrast_score', 'N/A')}%\n"

                await cl.Message(content=response).send()
            except json.JSONDecodeError:
                await cl.Message(content="❌ Could not parse accessibility data.").send()
        else:
            await cl.Message(content="📝 No accessibility audit available yet.").send()

    elif user_input.lower() in ("api", "api report", "api testing"):
        api_data = gui_instance.redis_client.get(f"api:{session_id}:tests")
        if api_data:
            try:
                api = json.loads(api_data)
                response = "🔌 **API Integration Tests**\n\n"

                schema = api.get("schema_validation", {})
                response += f"**Schema Validation:** {schema.get('score', 'N/A')}% ({schema.get('violations_count', 0)} violations)\n"

                contract = api.get("contract_testing", {})
                verification = contract.get("verification", {})
                response += f"**Contract Testing:** {verification.get('passed', 0)}/{verification.get('total', 0)} passed\n"

                versioning = api.get("versioning", {})
                response += f"**Versioning:** {versioning.get('current_version', 'N/A')}\n"

                load = api.get("load_testing", {})
                response += f"**Load Testing:** {load.get('endpoints_tested', 0)} endpoints tested\n"

                await cl.Message(content=response).send()
            except json.JSONDecodeError:
                await cl.Message(content="❌ Could not parse API data.").send()
        else:
            await cl.Message(content="📝 No API integration tests available yet.").send()

    elif user_input.lower() in ("mobile", "mobile report", "device"):
        mobile_data = gui_instance.redis_client.get(f"mobile:{session_id}:tests")
        if mobile_data:
            try:
                mob = json.loads(mobile_data)
                response = "📱 **Mobile/Device Tests**\n\n"

                resp_test = mob.get("responsive_testing", {})
                response += f"**Responsive:** {resp_test.get('responsive_score', 'N/A')}% ({resp_test.get('breakpoints_tested', 0)} breakpoints)\n"

                device = mob.get("device_compatibility", {})
                response += f"**Device Compatibility:** {device.get('compatibility_rate', 'N/A')}%\n"

                network = mob.get("network_conditions", {})
                response += f"**Network Conditions:** {network.get('network_score', 'N/A')}%\n"

                ux = mob.get("mobile_ux", {})
                response += f"**Mobile UX:** {ux.get('ux_score', 'N/A')}%\n"

                await cl.Message(content=response).send()
            except json.JSONDecodeError:
                await cl.Message(content="❌ Could not parse mobile data.").send()
        else:
            await cl.Message(content="📝 No mobile/device tests available yet.").send()

    elif user_input.lower() in ("compliance", "gdpr", "pci", "compliance report"):
        comp_data = gui_instance.redis_client.get(f"compliance:{session_id}:audit")
        if comp_data:
            try:
                comp = json.loads(comp_data)
                response = "📋 **Compliance Audit**\n\n"

                gdpr = comp.get("gdpr_compliance", {})
                response += f"**GDPR:** {gdpr.get('gdpr_score', 'N/A')}% ({gdpr.get('violations_count', 0)} violations)\n"

                pci = comp.get("pci_dss_compliance", {})
                response += f"**PCI DSS:** {pci.get('pci_score', 'N/A')}% ({pci.get('violations_count', 0)} violations)\n"

                audit = comp.get("audit_trail", {})
                response += f"**Audit Trail:** {audit.get('audit_score', 'N/A')}%\n"

                policy = comp.get("policy_enforcement", {})
                response += f"**Policy Enforcement:** {policy.get('compliance_score', 'N/A')}%\n"

                await cl.Message(content=response).send()
            except json.JSONDecodeError:
                await cl.Message(content="❌ Could not parse compliance data.").send()
        else:
            await cl.Message(content="📝 No compliance audit available yet.").send()

    elif user_input.lower() in ("chaos", "resilience", "chaos report"):
        chaos_data = gui_instance.redis_client.get(f"chaos:{session_id}:tests")
        if chaos_data:
            try:
                chaos = json.loads(chaos_data)
                response = "💥 **Chaos & Resilience Tests**\n\n"

                svc = chaos.get("service_failure", {})
                response += f"**Service Failure:** {svc.get('resilience_score', 'N/A')}% resilient\n"

                net = chaos.get("network_partition", {})
                response += f"**Network Partition:** {net.get('network_resilience_score', 'N/A')}%\n"

                res = chaos.get("resource_exhaustion", {})
                response += f"**Resource Exhaustion:** {res.get('resource_resilience_score', 'N/A')}%\n"

                rec = chaos.get("recovery_validation", {})
                response += f"**Recovery:** {rec.get('recovery_score', 'N/A')}%\n"

                mttr = rec.get("mttr", {})
                if mttr:
                    response += f"  MTTR: {mttr.get('measured_mttr_seconds', 'N/A')}s (target: {mttr.get('target_mttr_seconds', 'N/A')}s)\n"

                await cl.Message(content=response).send()
            except json.JSONDecodeError:
                await cl.Message(content="❌ Could not parse chaos data.").send()
        else:
            await cl.Message(content="📝 No chaos/resilience tests available yet.").send()

    elif user_input.lower() in ("database", "db", "database report"):
        db_data = gui_instance.redis_client.get(f"sre:{session_id}:database")
        if db_data:
            try:
                db = json.loads(db_data)
                health_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "🚫"}.get(db.get("overall_health"), "❓")
                response = "🗄️ **Database Reliability Assessment**\n\n"
                response += f"**Type:** {db.get('db_type', 'N/A')} | **Health:** {health_emoji} {db.get('overall_health', 'Unknown')}\n\n"

                pool = db.get("connection_pool", {})
                response += "**Connection Pool:**\n"
                response += f"  • Attempts: {pool.get('total_attempts', 'N/A')} | Successes: {pool.get('successes', 'N/A')} | Failures: {pool.get('failures', 'N/A')}\n"
                response += f"  • Avg Connect: {pool.get('avg_connect_ms', 'N/A')}ms | P95: {pool.get('p95_connect_ms', 'N/A')}ms\n\n"

                txn = db.get("transaction_consistency", {})
                response += f"**Transaction Consistency:** {txn.get('scenarios_passed', 'N/A')}/{txn.get('scenarios_tested', 'N/A')} passed\n\n"

                recs = db.get("recommendations", [])
                if recs:
                    response += "**Recommendations:**\n"
                    for r in recs:
                        response += f"  • {r}\n"

                await cl.Message(content=response).send()
            except json.JSONDecodeError:
                await cl.Message(content="❌ Could not parse database data.").send()
        else:
            await cl.Message(content="📝 No database assessment available yet.").send()

    elif user_input.lower() in ("infrastructure", "infra", "infrastructure report"):
        infra_data = gui_instance.redis_client.get(f"sre:{session_id}:infrastructure")
        if infra_data:
            try:
                infra = json.loads(infra_data)
                health_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "🚫"}.get(infra.get("overall_health"), "❓")
                response = "🏗️ **Infrastructure Health Report**\n\n"
                response += f"**Overall Health:** {health_emoji} {infra.get('overall_health', 'Unknown')}\n\n"

                dns = infra.get("dns_resolution", {})
                response += f"**DNS Resolution:** {len(dns.get('resolved', []))} resolved, {len(dns.get('failures', []))} failed\n"

                svc = infra.get("service_discovery", {})
                response += f"**Services:** {len(svc.get('healthy', []))} healthy, {len(svc.get('unhealthy', []))} unhealthy\n\n"

                issues = infra.get("issues", [])
                if issues:
                    response += "**Issues:**\n"
                    for issue in issues:
                        response += f"  ⚠️ {issue.get('type', 'unknown')}: {issue.get('detail', '')}\n"

                recs = infra.get("recommendations", [])
                if recs:
                    response += "\n**Recommendations:**\n"
                    for r in recs:
                        response += f"  • {r}\n"

                await cl.Message(content=response).send()
            except json.JSONDecodeError:
                await cl.Message(content="❌ Could not parse infrastructure data.").send()
        else:
            await cl.Message(content="📝 No infrastructure assessment available yet.").send()

    else:
        # General help message
        await cl.Message(
            content="💡 **Available Commands:**\n\n"
            "• **Describe your testing requirements** - Start a new test plan\n"
            "• **'status'** - Check current session status\n"
            "• **'trace'** - View reasoning trace and agent collaboration\n"
            "• **'report'** - View comprehensive QA analyst report\n"
            "• **'security'** - View security assessment\n"
            "• **'performance'** - View performance profile\n"
            "• **'reliability'** - View site reliability assessment\n"
            "• **'accessibility'** - View accessibility audit\n"
            "• **'api'** - View API integration tests\n"
            "• **'mobile'** - View mobile/device tests\n"
            "• **'compliance'** - View compliance audit (GDPR/PCI)\n"
            "• **'chaos'** - View chaos/resilience tests\n"
            "• **'database'** - View database reliability assessment\n"
            "• **'infrastructure'** - View infrastructure health report\n"
            "• **'help'** - Show this help message\n\n"
            "You can also upload a PR or feature document to get started!"
        ).send()

@cl.on_file_upload
async def on_file_upload(files: List[cl.File]) -> Dict[str, Any]:
    """Handle file uploads"""
    session_id = cl.user_session.get("session_id")
    gui_instance = cl.user_session.get("gui")
    
    if not session_id or not gui_instance:
        await cl.Message(
            content="❌ Session error. Please restart the chat."
        ).send()
        return
    
    for file in files:
        try:
            # Read file content
            content = file.content.decode('utf-8')
            
            await cl.Message(
                content=f"📄 Processing uploaded file: {file.name}"
            ).send()
            
            # Parse requirements from file content
            requirements = {
                "title": f"Testing from {file.name}",
                "description": content[:1000] + "..." if len(content) > 1000 else content,
                "business_goals": "Ensure quality based on uploaded document",
                "constraints": "Requirements from uploaded file",
                "priority": "high",
                "submitted_by": "web_upload",
                "file_name": file.name,
                "submitted_at": datetime.now().isoformat()
            }
            
            # Submit to QA Manager
            result = await gui_instance.submit_requirements(session_id, requirements)
            
            if "error" in result:
                await cl.Message(
                    content=f"❌ Error processing file: {result['error']}"
                ).send()
            else:
                await cl.Message(
                    content=f"✅ Successfully processed {file.name} and created test plan!"
                ).send()
                
                # Show summary (similar to text input)
                test_plan = result.get("test_plan", {})
                response = f"📋 **Test Plan from {file.name}**\n\n"
                
                if test_plan.get("scenarios"):
                    response += "**Test Scenarios:**\n"
                    for scenario in test_plan["scenarios"][:5]:  # Show first 5
                        priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(scenario.get("priority"), "⚪")
                        response += f"{priority_emoji} **{scenario.get('name')}**\n"
                
                await cl.Message(content=response).send()
                
        except Exception as e:
            await cl.Message(
                content=f"❌ Error processing {file.name}: {str(e)}"
            ).send()

@cl.on_chat_end
async def on_chat_end() -> Dict[str, Any]:
    """Clean up when chat ends"""
    session_id = cl.user_session.get("session_id")
    if session_id:
        logger.info(f"Ending session: {session_id}")

# Health check endpoint
app = FastAPI()

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # Run Chainlit with FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)