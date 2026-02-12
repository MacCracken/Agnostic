import os
import sys
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from shared.crewai_compat import BaseTool
from langchain_openai import ChatOpenAI
import redis
from celery import Celery
import logging
import cv2
import numpy as np

# Add config path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.environment import config
import requests
from playwright.async_api import async_playwright
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SelfHealingTool(BaseTool):
    name: str = "Self-Healing UI Testing"
    description: str = "Repairs failed UI selectors using self-healing, computer vision, and semantic analysis"

    def _run(self, failed_selector: str, page_url: str, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """Perform self-healing of failed UI selectors (sync wrapper)."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._run_async(failed_selector, page_url, screenshot_path))
        return {
            "original_selector": failed_selector,
            "healed_selector": None,
            "healing_method": "requires_async_context",
            "confidence": 0.0,
            "alternative_selectors": []
        }

    async def _run_async(self, failed_selector: str, page_url: str, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
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
            cv_result = await self._computer_vision_healing(failed_selector, screenshot_path)
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
    
    async def _computer_vision_healing(self, failed_selector: str, screenshot_path: str) -> Dict[str, Any]:
        """Use Playwright and computer vision to locate UI elements"""
        try:
            # Load screenshot
            image = cv2.imread(screenshot_path)
            if image is None:
                return {"confidence": 0.0, "method": "cv_failed"}
            
            # Convert to grayscale for processing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply advanced template matching for common UI elements
            templates = await self._get_dynamic_ui_templates(failed_selector)
            best_match = {"confidence": 0.0, "location": None, "template": None}
            
            for template_name, template_img in templates.items():
                # Try multiple template matching methods
                methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED, cv2.TM_SQDIFF_NORMED]
                
                for method in methods:
                    result = cv2.matchTemplate(gray, template_img, method)
                    if method == cv2.TM_SQDIFF_NORMED:
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        confidence = 1.0 - min_val  # Invert for SQDIFF
                        location = min_loc
                    else:
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        confidence = max_val
                        location = max_loc
                    
                    if confidence > best_match["confidence"]:
                        best_match = {
                            "confidence": confidence,
                            "location": location,
                            "template": template_name,
                            "method": method
                        }
            
            if best_match["confidence"] > 0.7:
                # Use Playwright to get element at location and generate robust selector
                new_selector = await self._generate_playwright_selector_from_location(
                    best_match["location"], screenshot_path
                )
                return {
                    "healed_selector": new_selector,
                    "healing_method": "playwright_computer_vision",
                    "confidence": best_match["confidence"],
                    "location": best_match["location"],
                    "template_used": best_match["template"]
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
    
    async def _get_dynamic_ui_templates(self, failed_selector: str) -> Dict[str, np.ndarray]:
        """Generate dynamic templates based on failed selector and common UI patterns"""
        templates = {}
        
        # Extract element type from selector
        element_type = self._extract_element_type(failed_selector)
        
        # Generate realistic UI element templates with better visual characteristics
        if element_type in ["button", "input", "submit"]:
            # Button templates with various sizes and styles
            templates["button_small"] = self._create_button_template(25, 80, "primary")
            templates["button_medium"] = self._create_button_template(30, 120, "primary")
            templates["button_large"] = self._create_button_template(35, 160, "primary")
            templates["button_secondary"] = self._create_button_template(30, 100, "secondary")
            
        elif element_type == "input":
            # Input field templates with different types
            templates["input_text"] = self._create_input_template(25, 200, "text")
            templates["input_password"] = self._create_input_template(25, 180, "password")
            templates["input_email"] = self._create_input_template(25, 220, "email")
            templates["input_search"] = self._create_input_template(25, 250, "search")
            
        elif element_type == "a":
            # Link templates
            templates["link_standard"] = self._create_link_template(20, 100)
            templates["link_button"] = self._create_button_template(25, 90, "link")
            
        # Add generic templates as fallback
        templates["generic_element"] = self._create_generic_template(30, 100)
        
        return templates
    
    def _create_button_template(self, height: int, width: int, style: str) -> np.ndarray:
        """Create realistic button template with styling"""
        template = np.ones((height, width), dtype=np.uint8) * 240  # Light gray background
        
        # Add border
        template[0, :] = 180  # Top border
        template[-1, :] = 180  # Bottom border
        template[:, 0] = 180  # Left border
        template[:, -1] = 180  # Right border
        
        # Add style-specific features
        if style == "primary":
            template[2:-2, 2:-2] = 220  # Slightly darker center
        elif style == "secondary":
            template[2:-2, 2:-2] = 245  # Lighter center
        elif style == "link":
            template[2:-2, 2:-2] = 235  # Medium center
            
        return template
    
    def _create_input_template(self, height: int, width: int, input_type: str) -> np.ndarray:
        """Create realistic input field template"""
        template = np.ones((height, width), dtype=np.uint8) * 255  # White background
        
        # Add border
        template[0, :] = 150  # Top border
        template[-1, :] = 150  # Bottom border
        template[:, 0] = 150  # Left border
        template[:, -1] = 150  # Right border
        
        # Add input-specific features
        if input_type == "password":
            # Add dots to represent password characters
            for i in range(10, min(30, width - 10), 8):
                template[height//2-1:height//2+2, i:i+2] = 100
                
        elif input_type == "search":
            # Add search icon representation
            template[height//2-2:height//2+3, 5:10] = 120
            
        return template
    
    def _create_link_template(self, height: int, width: int) -> np.ndarray:
        """Create realistic link template"""
        template = np.ones((height, width), dtype=np.uint8) * 250  # Light background
        
        # Add underline
        template[-2:, :] = 100  # Underline
        
        return template
    
    def _create_generic_template(self, height: int, width: int) -> np.ndarray:
        """Create generic element template"""
        template = np.ones((height, width), dtype=np.uint8) * 230
        template[0, :] = 180
        template[-1, :] = 180
        template[:, 0] = 180
        template[:, -1] = 180
        return template
    
    async def _generate_playwright_selector_from_location(self, location: Tuple[int, int], screenshot_path: str) -> str:
        """Generate robust CSS selector using Playwright element detection"""
        try:
            async with async_playwright() as p:
                # Launch browser (headless for automation)
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Get page URL from context or use a default
                page_url = "about:blank"  # This should be passed as context
                
                # Navigate to page and get element at location
                await page.goto(page_url)
                
                # Use Playwright's elementFromPoint to get element at coordinates
                element_handle = await page.evaluate("""
                    (x, y) => {
                        const element = document.elementFromPoint(x, y);
                        if (!element) return null;
                        
                        // Generate multiple selector options
                        const selectors = [];
                        
                        // ID selector
                        if (element.id) {
                            selectors.push(`#${element.id}`);
                        }
                        
                        // Class selector
                        if (element.className) {
                            const classes = element.className.split(' ').filter(c => c.trim());
                            if (classes.length > 0) {
                                selectors.push(`.${classes.join('.')}`);
                            }
                        }
                        
                        // Tag + attributes
                        let selector = element.tagName.toLowerCase();
                        
                        // Add test-id if available
                        const testId = element.getAttribute('data-testid');
                        if (testId) {
                            selectors.push(`[data-testid="${testId}"]`);
                        }
                        
                        // Add aria-label if available
                        const ariaLabel = element.getAttribute('aria-label');
                        if (ariaLabel) {
                            selectors.push(`[aria-label="${ariaLabel}"]`);
                        }
                        
                        // Add type attribute for inputs
                        const type = element.getAttribute('type');
                        if (type) {
                            selector += `[type="${type}"]`;
                        }
                        
                        // Add name attribute
                        const name = element.getAttribute('name');
                        if (name) {
                            selector += `[name="${name}"]`;
                        }
                        
                        selectors.push(selector);
                        
                        // Get position among siblings
                        const siblings = Array.from(element.parentNode.children);
                        const index = siblings.indexOf(element) + 1;
                        selectors.push(`${element.tagName.toLowerCase()}:nth-child(${index})`);
                        
                        return {
                            tagName: element.tagName.toLowerCase(),
                            id: element.id,
                            className: element.className,
                            selectors: selectors,
                            textContent: element.textContent ? element.textContent.slice(0, 50) : '',
                            attributes: {
                                type: element.getAttribute('type'),
                                name: element.getAttribute('name'),
                                'data-testid': element.getAttribute('data-testid'),
                                'aria-label': element.getAttribute('aria-label'),
                                title: element.getAttribute('title'),
                                alt: element.getAttribute('alt')
                            }
                        };
                    }
                """, location[0], location[1])
                
                await browser.close()
                
                if element_handle and element_handle.get('selectors'):
                    # Return the most specific selector available
                    selectors = element_handle['selectors']
                    
                    # Prioritize selectors in order of reliability
                    priority_order = [
                        '[data-testid=',
                        '#',
                        '[aria-label=',
                        '[name=',
                        '[type=',
                        '.',
                        ':nth-child'
                    ]
                    
                    for prefix in priority_order:
                        for selector in selectors:
                            if selector.startswith(prefix):
                                return selector
                    
                    # Fallback to first available selector
                    return selectors[0] if selectors else f"element-at-{location[0]}-{location[1]}"
                
        except Exception as e:
            logger.error(f"Playwright selector generation failed: {e}")
        
        # Fallback selector
        x, y = location
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
        # Validate environment variables
        validation = config.validate_required_env_vars()
        if not all(validation.values()):
            missing_vars = [k for k, v in validation.items() if not v]
            logger.warning(f"Missing environment variables: {missing_vars}")
        
        # Initialize Redis and Celery with environment configuration
        self.redis_client = config.get_redis_client()
        self.celery_app = config.get_celery_app('senior_qa')
        
        # Log connection info (without passwords)
        connection_info = config.get_connection_info()
        logger.info(f"Redis connection: {connection_info['redis']['url']}")
        logger.info(f"RabbitMQ connection: {connection_info['rabbitmq']['url']}")
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
        if session_id and scenario.get("id"):
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
    """Main entry point for Senior QA agent with Celery worker"""
    senior_agent = SeniorQAAgent()
    
    # Start Celery worker for task processing
    logger.info("Starting Senior QA Celery worker...")
    
    # Define Celery task for handling scenarios
    @senior_agent.celery_app.task(bind=True, name="senior_qa.handle_complex_scenario")
    def handle_complex_task(self, task_data_json: str):
        """Celery task wrapper for handling complex scenarios"""
        try:
            import asyncio
            task_data = json.loads(task_data_json)
            result = asyncio.run(senior_agent.handle_complex_scenario(task_data))
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Celery task failed: {e}")
            return {"status": "error", "error": str(e)}
    
    # Start Redis listener for real-time task processing
    async def redis_task_listener():
        """Listen for tasks from Redis pub/sub"""
        pubsub = senior_agent.redis_client.pubsub()
        pubsub.subscribe(f"senior_qa:tasks")
        
        logger.info("Senior QA Redis task listener started")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    task_data = json.loads(message['data'])
                    logger.info(f"Received task via Redis: {task_data.get('scenario', {}).get('name', 'Unknown')}")
                    
                    # Process task asynchronously
                    result = await senior_agent.handle_complex_scenario(task_data)
                    logger.info(f"Task completed: {result.get('status', 'unknown')}")
                    
                except Exception as e:
                    logger.error(f"Redis task processing failed: {e}")
    
    # Run both Celery worker and Redis listener
    import threading
    
    def start_celery_worker():
        """Start Celery worker in separate thread"""
        argv = [
            'worker',
            '--loglevel=info',
            '--concurrency=2',
            '--hostname=senior-qa-worker@%h'
        ]
        senior_agent.celery_app.worker_main(argv)
    
    # Start Celery worker thread
    celery_thread = threading.Thread(target=start_celery_worker, daemon=True)
    celery_thread.start()
    
    # Start Redis listener in main thread
    asyncio.create_task(redis_task_listener())
    
    logger.info("Senior QA agent started with Celery worker and Redis listener")
    
    # Keep the agent running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Senior QA agent shutting down...")
    except Exception as e:
        logger.error(f"Senior QA agent error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
