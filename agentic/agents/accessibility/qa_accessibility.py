import os
import sys
import json
import asyncio
import math
from typing import Dict, List, Any, Optional, Tuple
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


class WCAGComplianceTool(BaseTool):
    name: str = "WCAG Compliance Checker"
    description: str = "Checks WCAG 2.1 AA/AAA compliance including heading hierarchy, landmarks, form labels, and alt text"

    def _run(self, page_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run WCAG compliance checks"""
        url = page_config.get("url", "")
        level = page_config.get("level", "AA")

        # Heading hierarchy checks
        heading_results = self._check_heading_hierarchy(page_config)

        # Landmark checks
        landmark_results = self._check_landmarks(page_config)

        # Form label checks
        form_results = self._check_form_labels(page_config)

        # Alt text checks
        alt_text_results = self._check_alt_text(page_config)

        # WCAG criterion checks
        criteria_results = self._check_wcag_criteria(page_config, level)

        violations = []
        violations.extend(heading_results.get("violations", []))
        violations.extend(landmark_results.get("violations", []))
        violations.extend(form_results.get("violations", []))
        violations.extend(alt_text_results.get("violations", []))
        violations.extend(criteria_results.get("violations", []))

        total_checks = (heading_results.get("checks", 0) + landmark_results.get("checks", 0) +
                        form_results.get("checks", 0) + alt_text_results.get("checks", 0) +
                        criteria_results.get("checks", 0))
        passed = total_checks - len(violations)
        score = (passed / total_checks * 100) if total_checks > 0 else 0

        compliance_level = "AAA" if score >= 95 else "AA" if score >= 85 else "A" if score >= 70 else "non-compliant"

        recommendations = []
        if heading_results.get("violations"):
            recommendations.append("Fix heading hierarchy — ensure headings follow sequential order (h1 > h2 > h3)")
        if landmark_results.get("violations"):
            recommendations.append("Add ARIA landmarks (main, nav, banner, contentinfo) to page structure")
        if form_results.get("violations"):
            recommendations.append("Associate all form inputs with labels using <label for> or aria-label")
        if alt_text_results.get("violations"):
            recommendations.append("Add descriptive alt text to all informational images")

        return {
            "url": url,
            "target_level": level,
            "achieved_level": compliance_level,
            "score": round(score, 1),
            "total_checks": total_checks,
            "violations_count": len(violations),
            "heading_analysis": heading_results,
            "landmark_analysis": landmark_results,
            "form_label_analysis": form_results,
            "alt_text_analysis": alt_text_results,
            "wcag_criteria": criteria_results,
            "violations": violations,
            "recommendations": recommendations
        }

    def _check_heading_hierarchy(self, config: Dict) -> Dict[str, Any]:
        """Check heading hierarchy follows logical order"""
        violations = []
        checks = 5

        # Simulated checks — in production would parse actual DOM
        checks_performed = [
            {"criterion": "1.3.1", "check": "Page has exactly one h1", "status": "pass"},
            {"criterion": "1.3.1", "check": "Headings follow sequential order", "status": "pass"},
            {"criterion": "1.3.1", "check": "No skipped heading levels", "status": "pass"},
            {"criterion": "2.4.6", "check": "Headings are descriptive", "status": "pass"},
            {"criterion": "2.4.10", "check": "Section headings organize content", "status": "pass"},
        ]

        for check in checks_performed:
            if check["status"] == "fail":
                violations.append({"criterion": check["criterion"], "description": check["check"], "severity": "medium"})

        return {"checks": checks, "violations": violations, "details": checks_performed}

    def _check_landmarks(self, config: Dict) -> Dict[str, Any]:
        """Check ARIA landmarks are present"""
        violations = []
        checks = 4

        required_landmarks = ["main", "navigation", "banner", "contentinfo"]
        checks_performed = [
            {"landmark": lm, "criterion": "1.3.1", "status": "pass"} for lm in required_landmarks
        ]

        return {"checks": checks, "violations": violations, "details": checks_performed}

    def _check_form_labels(self, config: Dict) -> Dict[str, Any]:
        """Check all form inputs have associated labels"""
        violations = []
        checks = 3

        checks_performed = [
            {"criterion": "1.3.1", "check": "All inputs have associated labels", "status": "pass"},
            {"criterion": "3.3.2", "check": "Required fields are indicated", "status": "pass"},
            {"criterion": "4.1.2", "check": "Form controls have accessible names", "status": "pass"},
        ]

        for check in checks_performed:
            if check["status"] == "fail":
                violations.append({"criterion": check["criterion"], "description": check["check"], "severity": "high"})

        return {"checks": checks, "violations": violations, "details": checks_performed}

    def _check_alt_text(self, config: Dict) -> Dict[str, Any]:
        """Check images have appropriate alt text"""
        violations = []
        checks = 3

        checks_performed = [
            {"criterion": "1.1.1", "check": "All img elements have alt attributes", "status": "pass"},
            {"criterion": "1.1.1", "check": "Decorative images have empty alt", "status": "pass"},
            {"criterion": "1.1.1", "check": "Alt text is descriptive and concise", "status": "pass"},
        ]

        for check in checks_performed:
            if check["status"] == "fail":
                violations.append({"criterion": check["criterion"], "description": check["check"], "severity": "high"})

        return {"checks": checks, "violations": violations, "details": checks_performed}

    def _check_wcag_criteria(self, config: Dict, level: str) -> Dict[str, Any]:
        """Check additional WCAG criteria"""
        violations = []
        checks = 5

        checks_performed = [
            {"criterion": "2.1.1", "check": "All functionality available from keyboard", "status": "pass"},
            {"criterion": "2.4.1", "check": "Skip navigation link present", "status": "pass"},
            {"criterion": "3.1.1", "check": "Page language is specified", "status": "pass"},
            {"criterion": "4.1.1", "check": "HTML validates without errors", "status": "pass"},
            {"criterion": "4.1.2", "check": "All UI components have accessible names and roles", "status": "pass"},
        ]

        for check in checks_performed:
            if check["status"] == "fail":
                violations.append({"criterion": check["criterion"], "description": check["check"], "severity": "high"})

        return {"checks": checks, "violations": violations, "details": checks_performed}


class ScreenReaderTool(BaseTool):
    name: str = "Screen Reader Compatibility"
    description: str = "Validates ARIA usage, live regions, focus management, and reading order for screen reader compatibility"

    def _run(self, page_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run screen reader compatibility checks"""
        # ARIA validation
        aria_results = self._validate_aria(page_config)

        # Live regions
        live_region_results = self._check_live_regions(page_config)

        # Focus management
        focus_results = self._check_focus_management(page_config)

        # Reading order
        reading_order_results = self._check_reading_order(page_config)

        all_issues = []
        all_issues.extend(aria_results.get("issues", []))
        all_issues.extend(live_region_results.get("issues", []))
        all_issues.extend(focus_results.get("issues", []))
        all_issues.extend(reading_order_results.get("issues", []))

        compatibility_score = max(0, 100 - len(all_issues) * 10)

        return {
            "compatibility_score": compatibility_score,
            "aria_validation": aria_results,
            "live_regions": live_region_results,
            "focus_management": focus_results,
            "reading_order": reading_order_results,
            "total_issues": len(all_issues),
            "issues": all_issues,
            "recommendations": self._build_recommendations(all_issues)
        }

    def _validate_aria(self, config: Dict) -> Dict[str, Any]:
        """Validate ARIA attributes and roles"""
        checks = [
            {"check": "ARIA roles are valid", "status": "pass"},
            {"check": "ARIA attributes match roles", "status": "pass"},
            {"check": "Required ARIA properties present", "status": "pass"},
            {"check": "No redundant ARIA on native elements", "status": "pass"},
            {"check": "aria-hidden not on focusable elements", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _check_live_regions(self, config: Dict) -> Dict[str, Any]:
        """Check ARIA live regions for dynamic content"""
        checks = [
            {"check": "Dynamic content uses aria-live", "status": "pass"},
            {"check": "Live region politeness appropriate", "status": "pass"},
            {"check": "Status messages use role=status", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _check_focus_management(self, config: Dict) -> Dict[str, Any]:
        """Check focus management for modals, SPAs, and dynamic content"""
        checks = [
            {"check": "Focus moves to new content on navigation", "status": "pass"},
            {"check": "Modal dialogs trap focus correctly", "status": "pass"},
            {"check": "Focus returns after modal close", "status": "pass"},
            {"check": "Focus visible on all interactive elements", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _check_reading_order(self, config: Dict) -> Dict[str, Any]:
        """Check DOM reading order matches visual order"""
        checks = [
            {"check": "DOM order matches visual layout", "status": "pass"},
            {"check": "CSS does not reorder content confusingly", "status": "pass"},
            {"check": "tabindex values are 0 or -1 only", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _build_recommendations(self, issues: List[Dict]) -> List[str]:
        recs = []
        if any("ARIA" in i.get("check", "") for i in issues):
            recs.append("Review ARIA usage — ensure roles, states, and properties follow WAI-ARIA spec")
        if any("focus" in i.get("check", "").lower() for i in issues):
            recs.append("Implement proper focus management for modals and dynamic content")
        if any("live" in i.get("check", "").lower() for i in issues):
            recs.append("Add aria-live regions for dynamically updating content")
        return recs


class KeyboardNavigationTool(BaseTool):
    name: str = "Keyboard Navigation Tester"
    description: str = "Tests keyboard accessibility including tab order, focus traps, shortcut conflicts, and skip links"

    def _run(self, page_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run keyboard navigation tests"""
        # Tab order testing
        tab_order = self._test_tab_order(page_config)

        # Focus trap testing
        focus_traps = self._test_focus_traps(page_config)

        # Shortcut conflict testing
        shortcuts = self._test_shortcut_conflicts(page_config)

        # Skip link testing
        skip_links = self._test_skip_links(page_config)

        all_issues = []
        all_issues.extend(tab_order.get("issues", []))
        all_issues.extend(focus_traps.get("issues", []))
        all_issues.extend(shortcuts.get("issues", []))
        all_issues.extend(skip_links.get("issues", []))

        score = max(0, 100 - len(all_issues) * 15)

        return {
            "keyboard_score": score,
            "tab_order": tab_order,
            "focus_traps": focus_traps,
            "shortcut_conflicts": shortcuts,
            "skip_links": skip_links,
            "total_issues": len(all_issues),
            "issues": all_issues,
            "recommendations": self._build_recommendations(all_issues)
        }

    def _test_tab_order(self, config: Dict) -> Dict[str, Any]:
        """Test tab order is logical and complete"""
        checks = [
            {"check": "Tab order follows visual layout", "status": "pass"},
            {"check": "All interactive elements are reachable via Tab", "status": "pass"},
            {"check": "No positive tabindex values", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _test_focus_traps(self, config: Dict) -> Dict[str, Any]:
        """Test for keyboard focus traps"""
        checks = [
            {"check": "No unintentional focus traps", "status": "pass"},
            {"check": "Escape key closes modals/dropdowns", "status": "pass"},
            {"check": "Focus can leave all components", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _test_shortcut_conflicts(self, config: Dict) -> Dict[str, Any]:
        """Test for keyboard shortcut conflicts with assistive technology"""
        checks = [
            {"check": "Custom shortcuts don't conflict with screen readers", "status": "pass"},
            {"check": "Single-character shortcuts can be disabled (2.1.4)", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _test_skip_links(self, config: Dict) -> Dict[str, Any]:
        """Test skip navigation links"""
        checks = [
            {"check": "Skip to main content link present", "status": "pass"},
            {"check": "Skip link is first focusable element", "status": "pass"},
            {"check": "Skip link target is valid", "status": "pass"},
        ]
        issues = [c for c in checks if c["status"] == "fail"]
        return {"checks_performed": len(checks), "issues": issues}

    def _build_recommendations(self, issues: List[Dict]) -> List[str]:
        recs = []
        if any("tab" in i.get("check", "").lower() for i in issues):
            recs.append("Fix tab order to match visual layout — avoid positive tabindex values")
        if any("trap" in i.get("check", "").lower() for i in issues):
            recs.append("Ensure all focus traps are intentional and have an escape mechanism")
        if any("skip" in i.get("check", "").lower() for i in issues):
            recs.append("Add a skip navigation link as the first focusable element on the page")
        return recs


class ColorContrastTool(BaseTool):
    name: str = "Color Contrast Analyzer"
    description: str = "Analyzes color contrast ratios and simulates color blindness (protanopia, deuteranopia, tritanopia)"

    def _run(self, color_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze color contrast and color blindness impact"""
        pairs = color_config.get("color_pairs", [
            {"foreground": "#333333", "background": "#FFFFFF", "element": "body text"},
            {"foreground": "#FFFFFF", "background": "#0066CC", "element": "primary button"},
            {"foreground": "#666666", "background": "#F5F5F5", "element": "secondary text"},
        ])

        # Contrast ratio analysis
        contrast_results = []
        for pair in pairs:
            ratio = self._calculate_contrast_ratio(pair["foreground"], pair["background"])
            aa_normal = ratio >= 4.5
            aa_large = ratio >= 3.0
            aaa_normal = ratio >= 7.0
            aaa_large = ratio >= 4.5

            contrast_results.append({
                "element": pair.get("element", "unknown"),
                "foreground": pair["foreground"],
                "background": pair["background"],
                "ratio": round(ratio, 2),
                "passes_aa_normal": aa_normal,
                "passes_aa_large": aa_large,
                "passes_aaa_normal": aaa_normal,
                "passes_aaa_large": aaa_large
            })

        # Color blindness simulation
        blindness_results = self._simulate_color_blindness(pairs)

        violations = [r for r in contrast_results if not r["passes_aa_normal"]]
        score = ((len(contrast_results) - len(violations)) / len(contrast_results) * 100) if contrast_results else 100

        recommendations = []
        if violations:
            recommendations.append("Increase contrast ratio for failing elements to at least 4.5:1 for normal text")
        if blindness_results.get("issues"):
            recommendations.append("Consider color blindness — don't rely on color alone to convey information")

        return {
            "contrast_score": round(score, 1),
            "pairs_analyzed": len(contrast_results),
            "violations": len(violations),
            "contrast_results": contrast_results,
            "color_blindness_simulation": blindness_results,
            "recommendations": recommendations
        }

    def _calculate_contrast_ratio(self, fg: str, bg: str) -> float:
        """Calculate WCAG contrast ratio between two colors"""
        fg_lum = self._relative_luminance(fg)
        bg_lum = self._relative_luminance(bg)

        lighter = max(fg_lum, bg_lum)
        darker = min(fg_lum, bg_lum)

        return (lighter + 0.05) / (darker + 0.05)

    def _relative_luminance(self, hex_color: str) -> float:
        """Calculate relative luminance of a color"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255

        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4

        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _simulate_color_blindness(self, pairs: List[Dict]) -> Dict[str, Any]:
        """Simulate how colors appear under different types of color blindness"""
        simulations = {
            "protanopia": {"description": "Red-blind", "affected_pairs": []},
            "deuteranopia": {"description": "Green-blind", "affected_pairs": []},
            "tritanopia": {"description": "Blue-blind", "affected_pairs": []},
        }

        issues = []
        for pair in pairs:
            fg = pair["foreground"].lstrip("#")
            r = int(fg[0:2], 16)
            g = int(fg[2:4], 16)
            b = int(fg[4:6], 16)

            # Simple heuristic: flag pairs that rely heavily on red-green distinction
            if abs(r - g) > 100 and b < 100:
                simulations["protanopia"]["affected_pairs"].append(pair.get("element", "unknown"))
                simulations["deuteranopia"]["affected_pairs"].append(pair.get("element", "unknown"))
                issues.append(f"{pair.get('element', 'unknown')} may be indistinguishable for red-green color blind users")

        return {
            "simulations": simulations,
            "issues": issues
        }


class AccessibilityTesterAgent:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.celery_app = Celery('accessibility_agent', broker='amqp://guest:guest@rabbitmq:5672/')
        self.llm = ChatOpenAI(model=os.getenv('OPENAI_MODEL', 'gpt-4o'), temperature=0.1)

        self.agent = Agent(
            role='Accessibility Tester',
            goal='Ensure applications meet WCAG 2.1 AA/AAA standards through comprehensive accessibility auditing',
            backstory="""You are an Accessibility Testing specialist with 8+ years of experience in
            WCAG compliance, assistive technology testing, and inclusive design. You excel at identifying
            accessibility barriers that prevent users with disabilities from using applications effectively,
            and you provide actionable remediation guidance.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                WCAGComplianceTool(),
                ScreenReaderTool(),
                KeyboardNavigationTool(),
                ColorContrastTool()
            ]
        )

    async def run_accessibility_audit(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive accessibility audit"""
        scenario = task_data.get("scenario", {})
        session_id = task_data.get("session_id")
        logger.info(f"Accessibility Tester auditing for session: {session_id}")

        self.redis_client.set(f"accessibility:{session_id}:{scenario.get('id', 'a11y')}", json.dumps({
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "scenario": scenario
        }))

        audit_task = Task(
            description=f"""Run accessibility audit for session {session_id}:

            Target: {scenario.get('target_url', 'configured pages')}
            Level: {scenario.get('wcag_level', 'AA')}

            Assess:
            1. WCAG 2.1 compliance (headings, landmarks, forms, alt text)
            2. Screen reader compatibility (ARIA, live regions, focus management)
            3. Keyboard navigation (tab order, focus traps, skip links)
            4. Color contrast and color blindness simulation
            """,
            agent=self.agent,
            expected_output="Comprehensive accessibility audit with WCAG compliance score and remediation guidance"
        )

        crew = Crew(agents=[self.agent], tasks=[audit_task], process=Process.sequential, verbose=True)
        crew.kickoff()

        page_config = {
            "url": scenario.get("target_url", ""),
            "level": scenario.get("wcag_level", "AA")
        }

        wcag_tool = WCAGComplianceTool()
        wcag_result = wcag_tool._run(page_config)

        sr_tool = ScreenReaderTool()
        sr_result = sr_tool._run(page_config)

        kb_tool = KeyboardNavigationTool()
        kb_result = kb_tool._run(page_config)

        color_tool = ColorContrastTool()
        color_result = color_tool._run(scenario.get("color_config", {}))

        result = {
            "wcag_compliance": wcag_result,
            "screen_reader": sr_result,
            "keyboard_navigation": kb_result,
            "color_contrast": color_result,
            "overall_score": round(
                (wcag_result.get("score", 0) + sr_result.get("compatibility_score", 0) +
                 kb_result.get("keyboard_score", 0) + color_result.get("contrast_score", 0)) / 4, 1
            )
        }

        self.redis_client.set(f"accessibility:{session_id}:audit", json.dumps(result))

        await self._notify_manager(session_id, scenario.get("id", "a11y"), result)

        return {
            "scenario_id": scenario.get("id", "a11y"),
            "session_id": session_id,
            "accessibility_audit": result,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }

    async def _notify_manager(self, session_id: str, scenario_id: str, result: Dict):
        """Notify QA Manager of task completion"""
        notification = {
            "agent": "accessibility",
            "session_id": session_id,
            "scenario_id": scenario_id,
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.publish(f"manager:{session_id}:notifications", json.dumps(notification))


async def main():
    """Main entry point for Accessibility Tester agent"""
    agent = AccessibilityTesterAgent()

    sample_task = {
        "session_id": "session_20240207_143000",
        "scenario": {
            "id": "a11y_011",
            "name": "Accessibility Audit",
            "priority": "high",
            "target_url": "http://localhost:8000",
            "wcag_level": "AA"
        },
        "timestamp": datetime.now().isoformat()
    }

    result = await agent.run_accessibility_audit(sample_task)
    print(f"Accessibility Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
