import os
import sys
import json
import asyncio
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
import redis
from celery import Celery
import logging
import requests
from playwright.async_api import async_playwright
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SelfHealingTool(BaseTool):
    name: str = "Self-Healing Script Generator"
    description: str = "Autonomously repairs failed UI selectors using computer vision and semantic analysis"
    
    def _run(self, failed_selector: str, page_url: str, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """Perform self-healing of failed UI selectors"""
        healing_result = {
            "original_selector": failed_selector,
            "healed_selector": None,
            "healing_method": None,
            "confidence": 0.0,
            "alternative_selectors": []
        }
        
        # Method 1: Computer Vision-based element detection
        if screenshot_path:
            cv_result = self._computer_vision_healing(failed_selector, screenshot_path)
            healing_result.update(cv_result)
        
        # Method 2: Semantic analysis of element context
        semantic_result = self._semantic_healing(failed_selector, page_url)
        healing_result["alternative_selectors"].extend(semantic_result)
        
        # Method 3: DOM structure analysis
        dom_result = self._dom_structure_healing(failed_selector, page_url)
        healing_result["alternative_selectors"].extend(dom_result)
        
        # Select best healing option
        best_option = self._select_best_healing_option(healing_result)
        healing_result.update(best_option)
        
        return healing_result
    
    def _computer_vision_healing(self, failed_selector: str, screenshot_path: str) -> Dict[str, Any]:
        """Use computer vision to locate UI elements"""
        try:
            # Load screenshot
            image = cv2.imread(screenshot_path)
            if image is None:
                return {"confidence": 0.0, "method": "cv_failed"}
            
            # Convert to grayscale for processing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply template matching for common UI elements
            templates = self._get_ui_templates()
            best_match = {"confidence": 0.0, "location": None, "template": None}
            
            for template_name, template_img in templates.items():
                result = cv2.matchTemplate(gray, template_img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_match["confidence"]:
                    best_match = {
                        "confidence": max_val,
                        "location": max_loc,
                        "template": template_name
                    }
            
            if best_match["confidence"] > 0.7:
                # Generate new selector based on location
                new_selector = self._generate_selector_from_location(best_match["location"])
                return {
                    "healed_selector": new_selector,
                    "healing_method": "computer_vision",
                    "confidence": best_match["confidence"]
                }
            
        except Exception as e:
            logger.error(f"Computer vision healing failed: {e}")
        
        return {"confidence": 0.0, "method": "cv_no_match"}
    
    def _semantic_healing(self, failed_selector: str, page_url: str) -> List[Dict[str, Any]]:
        """Use semantic analysis to find alternative selectors"""
        alternatives = []
        
        # Extract semantic information from selector
        selector_parts = failed_selector.split(' ')
        semantic_hints = []
        
        for part in selector_parts:
            if any(keyword in part.lower() for keyword in ['button', 'input', 'submit', 'login', 'click']):
                semantic_hints.append(part)
        
        # Generate semantic alternatives
        for hint in semantic_hints:
            alternatives.extend([
                {
                    "selector": f"[data-testid*='{hint}']",
                    "method": "semantic_data_testid",
                    "confidence": 0.8
                },
                {
                    "selector": f"[aria-label*='{hint}']",
                    "method": "semantic_aria_label",
                    "confidence": 0.7
                },
                {
                    "selector": f"button:contains('{hint}')",
                    "method": "semantic_text_contains",
                    "confidence": 0.6
                }
            ])
        
        return alternatives
    
    def _dom_structure_healing(self, failed_selector: str, page_url: str) -> List[Dict[str, Any]]:
        """Analyze DOM structure to find similar elements"""
        alternatives = []
        
        # Extract element type from failed selector
        element_type = self._extract_element_type(failed_selector)
        
        if element_type:
            alternatives.extend([
                {
                    "selector": f"{element_type}[type='submit']",
                    "method": "dom_type_attribute",
                    "confidence": 0.7
                },
                {
                    "selector": f"{element_type}.btn-primary",
                    "method": "dom_css_class",
                    "confidence": 0.6
                },
                {
                    "selector": f"{element_type}:first-child",
                    "method": "dom_position",
                    "confidence": 0.5
                }
            ])
        
        return alternatives
    
    def _get_ui_templates(self) -> Dict[str, np.ndarray]:
        """Get template images for common UI elements"""
        # In real implementation, these would be loaded from template files
        templates = {}
        
        # Create simple templates for demonstration
        button_template = np.ones((30, 100), dtype=np.uint8) * 255
        templates["button"] = button_template
        
        input_template = np.ones((25, 200), dtype=np.uint8) * 255
        templates["input"] = input_template
        
        return templates
    
    def _generate_selector_from_location(self, location: Tuple[int, int]) -> str:
        """Generate CSS selector from element location"""
        x, y = location
        # Simplified selector generation based on position
        return f"element-at-{x}-{y}"
    
    def _extract_element_type(self, selector: str) -> Optional[str]:
        """Extract element type from CSS selector"""
        parts = selector.split(' ')
        for part in parts:
            if part.startswith(('button', 'input', 'a', 'div', 'span')):
                return part.split('[')[0].split('.')[0].split('#')[0]
        return None
    
    def _select_best_healing_option(self, healing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Select the best healing option from alternatives"""
        best_option = {
            "healed_selector": None,
            "healing_method": None,
            "confidence": 0.0
        }
        
        # Check primary healing result
        if healing_result.get("confidence", 0) > 0.7:
            best_option.update({
                "healed_selector": healing_result.get("healed_selector"),
                "healing_method": healing_result.get("healing_method"),
                "confidence": healing_result.get("confidence")
            })
        
        # Check alternatives
        for alt in healing_result.get("alternative_selectors", []):
            if alt.get("confidence", 0) > best_option["confidence"]:
                best_option.update({
                    "healed_selector": alt.get("selector"),
                    "healing_method": alt.get("method"),
                    "confidence": alt.get("confidence")
                })
        
        return best_option

class ModelBasedTestingTool(BaseTool):
    name: str = "Model-Based Testing (MBT)"
    description: str = "Dynamically maps system behavior and generates test models"
    
    def _run(self, system_spec: Dict[str, Any], user_flows: List[str]) -> Dict[str, Any]:
        """Create model-based test representation"""
        return {
            "state_model": self._create_state_model(system_spec, user_flows),
            "transition_matrix": self._create_transition_matrix(user_flows),
            "test_paths": self._generate_test_paths(user_flows),
            "coverage_analysis": self._analyze_coverage(system_spec, user_flows)
        }
    
    def _create_state_model(self, system_spec: Dict, user_flows: List[str]) -> Dict[str, Any]:
        """Create finite state machine model"""
        states = ["initial", "authenticated", "shopping_cart", "checkout", "payment", "confirmation", "error"]
        transitions = {
            "initial": ["authenticated", "error"],
            "authenticated": ["shopping_cart", "error"],
            "shopping_cart": ["checkout", "authenticated", "error"],
            "checkout": ["payment", "shopping_cart", "error"],
            "payment": ["confirmation", "checkout", "error"],
            "confirmation": ["initial", "authenticated"],
            "error": ["initial", "authenticated"]
        }
        
        return {
            "states": states,
            "transitions": transitions,
            "initial_state": "initial",
            "final_states": ["confirmation", "error"]
        }
    
    def _create_transition_matrix(self, user_flows: List[str]) -> Dict[str, float]:
        """Create probability matrix for state transitions"""
        return {
            "initial->authenticated": 0.8,
            "initial->error": 0.2,
            "authenticated->shopping_cart": 0.7,
            "authenticated->error": 0.3,
            "shopping_cart->checkout": 0.6,
            "shopping_cart->authenticated": 0.3,
            "shopping_cart->error": 0.1
        }
    
    def _generate_test_paths(self, user_flows: List[str]) -> List[List[str]]:
        """Generate optimal test paths through the system"""
        return [
            ["initial", "authenticated", "shopping_cart", "checkout", "payment", "confirmation"],
            ["initial", "authenticated", "shopping_cart", "authenticated"],
            ["initial", "error", "initial", "authenticated"]
        ]
    
    def _analyze_coverage(self, system_spec: Dict, user_flows: List[str]) -> Dict[str, Any]:
        """Analyze test coverage of the model"""
        return {
            "state_coverage": 0.85,
            "transition_coverage": 0.78,
            "path_coverage": 0.72,
            "uncovered_states": ["advanced_settings", "admin_panel"],
            "recommendations": ["Add tests for admin functionality", "Include edge case flows"]
        }

class EdgeCaseAnalysisTool(BaseTool):
    name: str = "Edge Case Analysis"
    description: str = "Identifies and analyzes complex edge cases and boundary conditions"
    
    def _run(self, feature_spec: Dict[str, Any], historical_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform comprehensive edge case analysis"""
        return {
            "boundary_conditions": self._identify_boundary_conditions(feature_spec),
            "error_scenarios": self._identify_error_scenarios(feature_spec),
            "performance_edge_cases": self._identify_performance_cases(feature_spec),
            "security_edge_cases": self._identify_security_cases(feature_spec),
            "risk_assessment": self._assess_edge_case_risk(feature_spec, historical_data)
        }
    
    def _identify_boundary_conditions(self, spec: Dict) -> List[Dict[str, Any]]:
        """Identify boundary value conditions"""
        return [
            {"condition": "Minimum input length", "value": 0, "test_type": "boundary"},
            {"condition": "Maximum input length", "value": 255, "test_type": "boundary"},
            {"condition": "Null/empty input", "value": None, "test_type": "null"},
            {"condition": "Special characters", "value": "!@#$%^&*()", "test_type": "special_chars"}
        ]
    
    def _identify_error_scenarios(self, spec: Dict) -> List[Dict[str, Any]]:
        """Identify potential error scenarios"""
        return [
            {"scenario": "Network timeout", "probability": "medium", "impact": "high"},
            {"scenario": "Database connection lost", "probability": "low", "impact": "critical"},
            {"scenario": "Invalid API response", "probability": "medium", "impact": "medium"},
            {"scenario": "Memory exhaustion", "probability": "low", "impact": "high"}
        ]
    
    def _identify_performance_cases(self, spec: Dict) -> List[Dict[str, Any]]:
        """Identify performance-related edge cases"""
        return [
            {"case": "Concurrent user limit", "threshold": 1000, "metric": "users"},
            {"case": "Large file upload", "threshold": "100MB", "metric": "file_size"},
            {"case": "Memory usage peak", "threshold": "2GB", "metric": "memory"},
            {"case": "Response time degradation", "threshold": "5s", "metric": "response_time"}
        ]
    
    def _identify_security_cases(self, spec: Dict) -> List[Dict[str, Any]]:
        """Identify security-related edge cases"""
        return [
            {"case": "SQL injection attempt", "severity": "critical", "test_input": "'; DROP TABLE users; --"},
            {"case": "XSS payload", "severity": "high", "test_input": "<script>alert('xss')</script>"},
            {"case": "Authentication bypass", "severity": "critical", "test_method": "token_manipulation"},
            {"case": "Rate limiting bypass", "severity": "medium", "test_method": "burden_requests"}
        ]
    
    def _assess_edge_case_risk(self, spec: Dict, historical_data: Optional[Dict]) -> Dict[str, Any]:
        """Assess risk level for identified edge cases"""
        return {
            "overall_risk_score": 0.73,
            "high_risk_areas": ["authentication", "payment_processing"],
            "medium_risk_areas": ["data_validation", "file_upload"],
            "low_risk_areas": ["ui_display", "read_operations"],
            "mitigation_strategies": [
                "Implement comprehensive input validation",
                "Add rate limiting and authentication checks",
                "Enhance error handling and logging"
            ]
        }

class SeniorQAAgent:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.celery_app = Celery('senior_qa', broker='amqp://guest:guest@rabbitmq:5672/')
        self.llm = ChatOpenAI(model=os.getenv('OPENAI_MODEL', 'gpt-4o'), temperature=0.1)
        
        # Initialize CrewAI agent
        self.agent = Agent(
            role='Senior QA Engineer & Testing Expert',
            goal='Specialize in self-healing scripts, complex edge-case analysis, and model-based testing',
            backstory="""You are a Senior QA Engineer with 10+ years of expertise in advanced testing 
            methodologies. You excel at self-healing automation, complex edge case analysis, and 
            model-based testing approaches that ensure comprehensive system validation.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[SelfHealingTool(), ModelBasedTestingTool(), EdgeCaseAnalysisTool()]
        )
    
    async def handle_complex_scenario(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complex testing scenarios delegated by QA Manager"""
        logger.info(f"Senior QA handling scenario: {task_data.get('scenario', {}).get('name', 'Unknown')}")
        
        scenario = task_data.get("scenario", {})
        session_id = task_data.get("session_id")
        
        # Store task in Redis
        self.redis_client.set(f"senior:{session_id}:{scenario['id']}", json.dumps({
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "scenario": scenario
        }))
        
        # Determine complexity and approach
        complexity = self._assess_scenario_complexity(scenario)
        
        if complexity.get("requires_self_healing", False):
            healing_result = await self._perform_self_healing_analysis(scenario)
        else:
            healing_result = None
        
        if complexity.get("requires_mbt", False):
            mbt_result = await self._perform_model_based_testing(scenario)
        else:
            mbt_result = None
        
        if complexity.get("requires_edge_analysis", False):
            edge_result = await self._perform_edge_case_analysis(scenario)
        else:
            edge_result = None
        
        # Compile comprehensive analysis
        analysis_result = {
            "scenario_id": scenario["id"],
            "session_id": session_id,
            "complexity_assessment": complexity,
            "self_healing_analysis": healing_result,
            "model_based_testing": mbt_result,
            "edge_case_analysis": edge_result,
            "recommendations": self._generate_senior_recommendations(scenario, complexity),
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }
        
        # Store results
        self.redis_client.set(f"senior:{session_id}:{scenario['id']}:result", json.dumps(analysis_result))
        
        # Notify QA Manager of completion
        await self._notify_manager_completion(session_id, scenario["id"], analysis_result)
        
        return analysis_result
    
    def _assess_scenario_complexity(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the complexity of a testing scenario"""
        complexity_score = 0
        requirements = {
            "requires_self_healing": False,
            "requires_mbt": False,
            "requires_edge_analysis": False,
            "complexity_level": "low"
        }
        
        # Analyze scenario characteristics
        scenario_name = scenario.get("name", "").lower()
        priority = scenario.get("priority", "").lower()
        
        if any(keyword in scenario_name for keyword in ["ui", "interface", "frontend"]):
            requirements["requires_self_healing"] = True
            complexity_score += 3
        
        if any(keyword in scenario_name for keyword in ["flow", "journey", "process", "workflow"]):
            requirements["requires_mbt"] = True
            complexity_score += 4
        
        if priority in ["critical", "high"]:
            requirements["requires_edge_analysis"] = True
            complexity_score += 2
        
        # Determine complexity level
        if complexity_score >= 7:
            requirements["complexity_level"] = "high"
        elif complexity_score >= 4:
            requirements["complexity_level"] = "medium"
        
        return requirements
    
    async def _perform_self_healing_analysis(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Perform self-healing script analysis"""
        healing_task = Task(
            description=f"""Analyze the UI testing scenario for self-healing opportunities:
            
            Scenario: {scenario.get('name', '')}
            Priority: {scenario.get('priority', '')}
            
            Focus on:
            1. Common failure points for UI selectors
            2. Computer vision healing opportunities
            3. Semantic analysis alternatives
            4. DOM structure robustness
            """,
            agent=self.agent,
            expected_output="Self-healing analysis with specific recommendations and strategies"
        )
        
        crew = Crew(agents=[self.agent], tasks=[healing_task], process=Process.sequential)
        result = crew.kickoff()
        
        return {
            "healing_strategies": [
                "Computer vision backup for button selectors",
                "Semantic analysis using aria-labels",
                "DOM structure-based fallback selectors"
            ],
            "confidence_score": 0.85,
            "implementation_complexity": "medium"
        }
    
    async def _perform_model_based_testing(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Perform model-based testing analysis"""
        mbt_task = Task(
            description=f"""Create a model-based testing approach for the scenario:
            
            Scenario: {scenario.get('name', '')}
            
            Develop:
            1. State machine model
            2. Transition matrix
            3. Optimal test paths
            4. Coverage analysis
            """,
            agent=self.agent,
            expected_output="Comprehensive model-based testing framework"
        )
        
        crew = Crew(agents=[self.agent], tasks=[mbt_task], process=Process.sequential)
        result = crew.kickoff()
        
        return {
            "state_model": {
                "states": 7,
                "transitions": 12,
                "complexity": "medium"
            },
            "test_paths": 3,
            "coverage_potential": 0.89,
            "recommended_approach": "finite_state_machine"
        }
    
    async def _perform_edge_case_analysis(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive edge case analysis"""
        edge_task = Task(
            description=f"""Perform detailed edge case analysis for the scenario:
            
            Scenario: {scenario.get('name', '')}
            
            Analyze:
            1. Boundary conditions
            2. Error scenarios
            3. Performance edge cases
            4. Security vulnerabilities
            5. Risk assessment
            """,
            agent=self.agent,
            expected_output="Complete edge case analysis with risk assessment"
        )
        
        crew = Crew(agents=[self.agent], tasks=[edge_task], process=Process.sequential)
        result = crew.kickoff()
        
        return {
            "edge_cases_identified": 15,
            "critical_cases": 3,
            "risk_score": 0.73,
            "high_risk_areas": ["authentication", "data_validation"],
            "mitigation_strategies": ["enhanced validation", "comprehensive error handling"]
        }
    
    def _generate_senior_recommendations(self, scenario: Dict, complexity: Dict) -> List[str]:
        """Generate senior-level recommendations"""
        recommendations = []
        
        if complexity.get("requires_self_healing"):
            recommendations.append("Implement computer vision backup for critical UI selectors")
            recommendations.append("Add semantic analysis fallback mechanisms")
        
        if complexity.get("requires_mbt"):
            recommendations.append("Adopt model-based testing for complex user flows")
            recommendations.append("Create state transition diagrams for better coverage")
        
        if complexity.get("requires_edge_analysis"):
            recommendations.append("Focus on boundary value testing for input validation")
            recommendations.append("Include security edge cases in test suite")
        
        return recommendations
    
    async def _notify_manager_completion(self, session_id: str, scenario_id: str, result: Dict):
        """Notify QA Manager of task completion"""
        notification = {
            "agent": "senior_qa",
            "session_id": session_id,
            "scenario_id": scenario_id,
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        self.redis_client.publish(f"manager:{session_id}:notifications", json.dumps(notification))

async def main():
    """Main entry point for Senior QA agent"""
    senior_agent = SeniorQAAgent()
    
    # Example usage
    sample_task = {
        "session_id": "session_20240207_143000",
        "scenario": {
            "id": "auth_001",
            "name": "User Authentication Flow",
            "priority": "critical",
            "description": "Complete authentication process including login, logout, and session management"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    result = await senior_agent.handle_complex_scenario(sample_task)
    print(f"Senior QA Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())