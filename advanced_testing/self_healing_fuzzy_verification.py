import os
import sys
import json
import asyncio
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import requests
from playwright.async_api import async_playwright
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class AgenticSelfHealing:
    """Advanced self-healing system for UI automation"""
    
    def __init__(self):
        self.healing_strategies = {
            "computer_vision": self._computer_vision_healing,
            "semantic_analysis": self._semantic_healing,
            "dom_structure": self._dom_structure_healing,
            "machine_learning": self._ml_based_healing,
            "context_aware": self._context_aware_healing
        }
        self.healing_history = []
    
    async def heal_failed_selector(self, failed_selector: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive self-healing for failed selectors"""
        healing_result = {
            "original_selector": failed_selector,
            "healed_selector": None,
            "healing_method": None,
            "confidence": 0.0,
            "strategies_tried": [],
            "context_used": context
        }
        
        # Try each healing strategy in order of reliability
        for strategy_name, strategy_func in self.healing_strategies.items():
            try:
                result = await strategy_func(failed_selector, context)
                if result["confidence"] > healing_result["confidence"]:
                    healing_result.update(result)
                    healing_result["strategies_tried"].append(strategy_name)
                
                # If we find a high-confidence match, stop trying
                if healing_result["confidence"] > 0.85:
                    break
                    
            except Exception as e:
                logger.error(f"Healing strategy {strategy_name} failed: {e}")
                continue
        
        # Record healing attempt
        self.healing_history.append({
            "timestamp": datetime.now().isoformat(),
            "original_selector": failed_selector,
            "result": healing_result
        })
        
        return healing_result
    
    async def _computer_vision_healing(self, failed_selector: str, context: Dict) -> Dict[str, Any]:
        """Computer vision-based element detection"""
        if not context.get("screenshot_path"):
            return {"confidence": 0.0, "method": "computer_vision"}
        
        try:
            # Load and process screenshot
            image = cv2.imread(context["screenshot_path"])
            if image is None:
                return {"confidence": 0.0, "method": "computer_vision"}
            
            # Extract element type from selector
            element_type = self._extract_element_type(failed_selector)
            
            # Use template matching for common UI elements
            templates = self._get_dynamic_templates(element_type, context)
            best_match = {"confidence": 0.0, "location": None, "template": None}
            
            for template_name, template_img in templates.items():
                result = cv2.matchTemplate(image, template_img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_match["confidence"]:
                    best_match = {
                        "confidence": max_val,
                        "location": max_loc,
                        "template": template_name
                    }
            
            if best_match["confidence"] > 0.7:
                # Generate new selector based on location and context
                new_selector = await self._generate_cv_selector(best_match, context)
                return {
                    "healed_selector": new_selector,
                    "healing_method": "computer_vision",
                    "confidence": best_match["confidence"],
                    "location": best_match["location"]
                }
            
        except Exception as e:
            logger.error(f"Computer vision healing failed: {e}")
        
        return {"confidence": 0.0, "method": "computer_vision"}
    
    async def _semantic_healing(self, failed_selector: str, context: Dict) -> Dict[str, Any]:
        """Semantic analysis-based healing"""
        try:
            # Extract semantic meaning from failed selector
            semantic_hints = self._extract_semantic_hints(failed_selector)
            
            # Get page context for semantic analysis
            page_content = context.get("page_content", "")
            page_structure = context.get("page_structure", {})
            
            # Generate semantic alternatives
            alternatives = []
            
            for hint in semantic_hints:
                # Look for elements with similar semantic meaning
                semantic_selectors = [
                    f"[data-testid*='{hint}']",
                    f"[aria-label*='{hint}']",
                    f"[title*='{hint}']",
                    f"[alt*='{hint}']",
                    f"*:contains('{hint}')"
                ]
                
                for selector in semantic_selectors:
                    confidence = self._calculate_semantic_confidence(selector, hint, page_content)
                    if confidence > 0.6:
                        alternatives.append({
                            "selector": selector,
                            "confidence": confidence,
                            "method": "semantic_analysis"
                        })
            
            if alternatives:
                # Select best alternative
                best = max(alternatives, key=lambda x: x["confidence"])
                return {
                    "healed_selector": best["selector"],
                    "healing_method": "semantic_analysis",
                    "confidence": best["confidence"],
                    "alternatives_considered": len(alternatives)
                }
            
        except Exception as e:
            logger.error(f"Semantic healing failed: {e}")
        
        return {"confidence": 0.0, "method": "semantic_analysis"}
    
    async def _dom_structure_healing(self, failed_selector: str, context: Dict) -> Dict[str, Any]:
        """DOM structure-based healing"""
        try:
            # Analyze DOM structure from context
            dom_structure = context.get("dom_structure", {})
            
            # Extract element characteristics
            element_info = self._analyze_element_characteristics(failed_selector, dom_structure)
            
            # Generate structure-based alternatives
            alternatives = []
            
            if element_info.get("tag"):
                tag = element_info["tag"]
                
                # Try different attribute combinations
                attribute_combinations = [
                    f"{tag}[type='{element_info.get('type', '')}']",
                    f"{tag}[class*='{element_info.get('class', '')}']",
                    f"{tag}[id*='{element_info.get('id', '')}']",
                    f"{tag}:nth-child({element_info.get('position', 1)})",
                    f"{tag}.{element_info.get('class', '')}",
                    f"{tag}#{element_info.get('id', '')}"
                ]
                
                for selector in attribute_combinations:
                    confidence = self._calculate_structure_confidence(selector, element_info, dom_structure)
                    if confidence > 0.5:
                        alternatives.append({
                            "selector": selector,
                            "confidence": confidence,
                            "method": "dom_structure"
                        })
            
            if alternatives:
                best = max(alternatives, key=lambda x: x["confidence"])
                return {
                    "healed_selector": best["selector"],
                    "healing_method": "dom_structure",
                    "confidence": best["confidence"]
                }
            
        except Exception as e:
            logger.error(f"DOM structure healing failed: {e}")
        
        return {"confidence": 0.0, "method": "dom_structure"}
    
    async def _ml_based_healing(self, failed_selector: str, context: Dict) -> Dict[str, Any]:
        """Machine learning-based healing using historical data"""
        try:
            # Analyze historical healing patterns
            if not self.healing_history:
                return {"confidence": 0.0, "method": "machine_learning"}
            
            # Extract features from failed selector
            current_features = self._extract_selector_features(failed_selector)
            
            # Find similar historical cases
            similar_cases = []
            for case in self.healing_history[-50:]:  # Look at last 50 cases
                historical_selector = case["original_selector"]
                historical_features = self._extract_selector_features(historical_selector)
                
                # Calculate similarity
                similarity = self._calculate_feature_similarity(current_features, historical_features)
                
                if similarity > 0.7 and case["result"]["confidence"] > 0.8:
                    similar_cases.append({
                        "similarity": similarity,
                        "healed_selector": case["result"]["healed_selector"],
                        "confidence": case["result"]["confidence"] * similarity
                    })
            
            if similar_cases:
                # Select best match
                best_match = max(similar_cases, key=lambda x: x["confidence"])
                return {
                    "healed_selector": best_match["healed_selector"],
                    "healing_method": "machine_learning",
                    "confidence": best_match["confidence"],
                    "similar_cases": len(similar_cases)
                }
            
        except Exception as e:
            logger.error(f"ML-based healing failed: {e}")
        
        return {"confidence": 0.0, "method": "machine_learning"}
    
    async def _context_aware_healing(self, failed_selector: str, context: Dict) -> Dict[str, Any]:
        """Context-aware healing using page and user context"""
        try:
            # Extract context information
            page_url = context.get("page_url", "")
            user_flow = context.get("user_flow", "")
            previous_actions = context.get("previous_actions", [])
            
            # Analyze context patterns
            context_patterns = {
                "login_page": ["username", "password", "login", "submit"],
                "checkout_page": ["billing", "shipping", "payment", "submit"],
                "search_page": ["search", "query", "filter", "submit"],
                "profile_page": ["profile", "settings", "save", "update"]
            }
            
            # Identify current page context
            current_context = self._identify_page_context(page_url, user_flow)
            
            if current_context in context_patterns:
                pattern_keywords = context_patterns[current_context]
                
                # Generate context-aware selectors
                context_selectors = []
                for keyword in pattern_keywords:
                    if keyword in failed_selector.lower():
                        context_selectors.extend([
                            f"[data-context='{current_context}'][name*='{keyword}']",
                            f"[data-context='{current_context}'][id*='{keyword}']",
                            f"[data-context='{current_context}'][class*='{keyword}']"
                        ])
                
                if context_selectors:
                    # Evaluate context selectors
                    best_selector = None
                    best_confidence = 0.0
                    
                    for selector in context_selectors:
                        confidence = self._calculate_context_confidence(selector, current_context, context)
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_selector = selector
                    
                    if best_selector and best_confidence > 0.6:
                        return {
                            "healed_selector": best_selector,
                            "healing_method": "context_aware",
                            "confidence": best_confidence,
                            "context": current_context
                        }
            
        except Exception as e:
            logger.error(f"Context-aware healing failed: {e}")
        
        return {"confidence": 0.0, "method": "context_aware"}
    
    def _extract_element_type(self, selector: str) -> str:
        """Extract element type from selector"""
        if "button" in selector.lower():
            return "button"
        elif "input" in selector.lower():
            return "input"
        elif "select" in selector.lower():
            return "select"
        elif "a" in selector.lower():
            return "link"
        else:
            return "generic"
    
    def _get_dynamic_templates(self, element_type: str, context: Dict) -> Dict[str, np.ndarray]:
        """Generate dynamic templates based on element type and context"""
        templates = {}
        
        if element_type == "button":
            # Create button templates of different sizes
            templates["button_small"] = np.ones((25, 80), dtype=np.uint8) * 255
            templates["button_medium"] = np.ones((30, 120), dtype=np.uint8) * 255
            templates["button_large"] = np.ones((35, 160), dtype=np.uint8) * 255
            
        elif element_type == "input":
            # Create input field templates
            templates["input_text"] = np.ones((25, 200), dtype=np.uint8) * 255
            templates["input_password"] = np.ones((25, 180), dtype=np.uint8) * 255
            templates["input_email"] = np.ones((25, 220), dtype=np.uint8) * 255
        
        return templates
    
    async def _generate_cv_selector(self, match_info: Dict, context: Dict) -> str:
        """Generate selector from computer vision match"""
        location = match_info["location"]
        template = match_info["template"]
        
        # In a real implementation, this would use the location to find
        # the corresponding element in the DOM
        return f"[data-cv-location='{location[0]}_{location[1]}'][data-cv-template='{template}']"
    
    def _extract_semantic_hints(self, selector: str) -> List[str]:
        """Extract semantic hints from selector"""
        hints = []
        keywords = ["button", "input", "submit", "login", "click", "search", "filter", "save", "cancel"]
        
        selector_lower = selector.lower()
        for keyword in keywords:
            if keyword in selector_lower:
                hints.append(keyword)
        
        return hints
    
    def _calculate_semantic_confidence(self, selector: str, hint: str, page_content: str) -> float:
        """Calculate confidence for semantic selector"""
        # Simple confidence calculation based on page content
        base_confidence = 0.7
        
        if hint in page_content.lower():
            base_confidence += 0.2
        
        # Adjust based on selector specificity
        if "[data-testid" in selector:
            base_confidence += 0.1
        elif "[aria-label" in selector:
            base_confidence += 0.05
        
        return min(1.0, base_confidence)
    
    def _analyze_element_characteristics(self, selector: str, dom_structure: Dict) -> Dict[str, Any]:
        """Analyze element characteristics from DOM structure"""
        characteristics = {
            "tag": None,
            "class": None,
            "id": None,
            "type": None,
            "position": None
        }
        
        # Extract information from selector
        if "#" in selector:
            characteristics["id"] = selector.split("#")[1].split("[")[0].split(" ")[0]
        if "." in selector:
            characteristics["class"] = selector.split(".")[1].split("[")[0].split(" ")[0]
        if "[" in selector and "type=" in selector:
            type_part = [part for part in selector.split("[") if "type=" in part]
            if type_part:
                characteristics["type"] = type_part[0].split("type=")[1].split("'")[0].split('"')[0]
        
        # Extract tag name
        tag_part = selector.split("[")[0].split("#")[0].split(".")[0].split(" ")[0]
        if tag_part:
            characteristics["tag"] = tag_part
        
        return characteristics
    
    def _calculate_structure_confidence(self, selector: str, element_info: Dict, dom_structure: Dict) -> float:
        """Calculate confidence for structure-based selector"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on selector specificity
        if "#" in selector:  # ID selector
            confidence += 0.3
        if "." in selector:  # Class selector
            confidence += 0.2
        if "[type=" in selector:  # Type attribute
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _extract_selector_features(self, selector: str) -> Dict[str, Any]:
        """Extract features from selector for ML analysis"""
        features = {
            "length": len(selector),
            "has_id": "#" in selector,
            "has_class": "." in selector,
            "has_attribute": "[" in selector,
            "tag_type": self._extract_element_type(selector),
            "complexity": selector.count(" ") + selector.count(">") + selector.count("+")
        }
        
        return features
    
    def _calculate_feature_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between selector features"""
        similarity = 0.0
        total_features = len(features1)
        
        for key in features1:
            if key in features2:
                if isinstance(features1[key], type(features2[key])):
                    if features1[key] == features2[key]:
                        similarity += 1.0
                    else:
                        # For numeric features, calculate relative difference
                        if isinstance(features1[key], (int, float)):
                            diff = abs(features1[key] - features2[key])
                            max_val = max(features1[key], features2[key])
                            if max_val > 0:
                                similarity += 1.0 - (diff / max_val)
        
        return similarity / total_features if total_features > 0 else 0.0
    
    def _identify_page_context(self, page_url: str, user_flow: str) -> str:
        """Identify current page context"""
        url_lower = page_url.lower()
        flow_lower = user_flow.lower()
        
        if "login" in url_lower or "signin" in url_lower or "auth" in url_lower:
            return "login_page"
        elif "checkout" in url_lower or "payment" in url_lower or "billing" in url_lower:
            return "checkout_page"
        elif "search" in url_lower or "query" in url_lower:
            return "search_page"
        elif "profile" in url_lower or "account" in url_lower or "settings" in url_lower:
            return "profile_page"
        
        return "generic_page"
    
    def _calculate_context_confidence(self, selector: str, context: str, page_context: Dict) -> float:
        """Calculate confidence for context-aware selector"""
        confidence = 0.6  # Base confidence for context-aware selectors
        
        # Increase confidence based on context specificity
        if f"[data-context='{context}']" in selector:
            confidence += 0.2
        
        # Additional confidence based on page content relevance
        page_content = page_context.get("page_content", "")
        if context in page_content.lower():
            confidence += 0.1
        
        return min(1.0, confidence)

class FuzzyVerificationEngine:
    """Advanced fuzzy verification system for test results"""
    
    def __init__(self):
        self.verification_criteria = {
            "ui_layout": self._verify_ui_layout,
            "functionality": self._verify_functionality,
            "performance": self._verify_performance,
            "user_experience": self._verify_user_experience,
            "business_logic": self._verify_business_logic
        }
        self.verification_history = []
    
    async def perform_fuzzy_verification(self, test_results: Dict[str, Any], business_goals: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive fuzzy verification of test results"""
        verification_result = {
            "overall_score": 0.0,
            "confidence_level": "low",
            "business_alignment": 0.0,
            "detailed_scores": {},
            "recommendations": [],
            "verification_summary": "",
            "context_used": context
        }
        
        # Perform verification across different criteria
        total_score = 0.0
        criteria_count = 0
        
        for criterion_name, criterion_func in self.verification_criteria.items():
            try:
                score = await criterion_func(test_results, business_goals, context)
                verification_result["detailed_scores"][criterion_name] = score
                total_score += score
                criteria_count += 1
            except Exception as e:
                logger.error(f"Verification criterion {criterion_name} failed: {e}")
                verification_result["detailed_scores"][criterion_name] = 0.0
        
        # Calculate overall score
        if criteria_count > 0:
            verification_result["overall_score"] = total_score / criteria_count
        
        # Determine confidence level
        verification_result["confidence_level"] = self._determine_confidence_level(
            verification_result["overall_score"], test_results
        )
        
        # Calculate business alignment
        verification_result["business_alignment"] = self._calculate_business_alignment(
            test_results, business_goals, context
        )
        
        # Generate recommendations
        verification_result["recommendations"] = self._generate_verification_recommendations(
            verification_result["detailed_scores"], test_results
        )
        
        # Generate summary
        verification_result["verification_summary"] = self._generate_verification_summary(
            verification_result
        )
        
        # Record verification
        self.verification_history.append({
            "timestamp": datetime.now().isoformat(),
            "results": verification_result,
            "test_results": test_results,
            "business_goals": business_goals
        })
        
        return verification_result
    
    async def _verify_ui_layout(self, test_results: Dict, business_goals: str, context: Dict) -> float:
        """Verify UI layout and visual correctness"""
        score = 0.7  # Base score
        
        # Check for UI-related test results
        ui_tests = [test for test in test_results.get("test_results", []) 
                   if test.get("type") == "ui" or test.get("category") == "layout"]
        
        if ui_tests:
            passed_ui_tests = [test for test in ui_tests if test.get("status") == "passed"]
            if ui_tests:
                ui_pass_rate = len(passed_ui_tests) / len(ui_tests)
                score = 0.5 + (ui_pass_rate * 0.5)  # Scale between 0.5 and 1.0
        
        # Adjust for visual regression results
        visual_regression = test_results.get("visual_regression", {})
        if visual_regression.get("similarity_score", 0) > 0:
            score = (score + visual_regression["similarity_score"]) / 2
        
        # Consider responsive design results
        responsive_tests = test_results.get("responsive_design", {})
        if responsive_tests.get("passed", 0) > 0:
            responsive_score = responsive_tests.get("pass_rate", 0.7)
            score = (score + responsive_score) / 2
        
        return min(1.0, max(0.0, score))
    
    async def _verify_functionality(self, test_results: Dict, business_goals: str, context: Dict) -> float:
        """Verify core functionality"""
        score = 0.6  # Base score
        
        # Check functional test results
        functional_tests = [test for test in test_results.get("test_results", []) 
                           if test.get("type") == "functional"]
        
        if functional_tests:
            passed_functional = [test for test in functional_tests if test.get("status") == "passed"]
            if functional_tests:
                functional_pass_rate = len(passed_functional) / len(functional_tests)
                score = functional_pass_rate
        
        # Weight critical functionality higher
        critical_tests = [test for test in functional_tests if test.get("priority") == "critical"]
        if critical_tests:
            passed_critical = [test for test in critical_tests if test.get("status") == "passed"]
            critical_pass_rate = len(passed_critical) / len(critical_tests)
            # Critical tests have more weight
            score = (score * 0.3) + (critical_pass_rate * 0.7)
        
        return min(1.0, max(0.0, score))
    
    async def _verify_performance(self, test_results: Dict, business_goals: str, context: Dict) -> float:
        """Verify performance characteristics"""
        score = 0.8  # Base score
        
        # Check performance test results
        performance_metrics = test_results.get("performance_metrics", {})
        
        if performance_metrics:
            # Response time scoring
            avg_response_time = performance_metrics.get("avg_response_time", 1000)  # ms
            if avg_response_time < 500:
                response_time_score = 1.0
            elif avg_response_time < 1000:
                response_time_score = 0.8
            elif avg_response_time < 2000:
                response_time_score = 0.6
            else:
                response_time_score = 0.4
            
            # Throughput scoring
            throughput = performance_metrics.get("throughput", 100)  # requests per second
            throughput_score = min(1.0, throughput / 1000)
            
            # Error rate scoring
            error_rate = performance_metrics.get("error_rate", 0.01)  # percentage
            error_rate_score = max(0.0, 1.0 - (error_rate * 10))
            
            # Combine performance scores
            score = (response_time_score * 0.4) + (throughput_score * 0.3) + (error_rate_score * 0.3)
        
        return min(1.0, max(0.0, score))
    
    async def _verify_user_experience(self, test_results: Dict, business_goals: str, context: Dict) -> float:
        """Verify user experience aspects"""
        score = 0.7  # Base score
        
        # Check UX-related metrics
        ux_metrics = test_results.get("ux_metrics", {})
        
        if ux_metrics:
            # User satisfaction score
            satisfaction_score = ux_metrics.get("user_satisfaction", 0.7)
            
            # Task completion rate
            task_completion_rate = ux_metrics.get("task_completion_rate", 0.8)
            
            # Time on task
            avg_task_time = ux_metrics.get("avg_task_time", 60)  # seconds
            expected_task_time = ux_metrics.get("expected_task_time", 45)
            task_time_score = max(0.0, 1.0 - (avg_task_time - expected_task_time) / expected_task_time)
            
            # Combine UX scores
            score = (satisfaction_score * 0.4) + (task_completion_rate * 0.4) + (task_time_score * 0.2)
        
        return min(1.0, max(0.0, score))
    
    async def _verify_business_logic(self, test_results: Dict, business_goals: str, context: Dict) -> float:
        """Verify business logic compliance"""
        score = 0.6  # Base score
        
        # Check business logic test results
        business_tests = [test for test in test_results.get("test_results", []) 
                          if test.get("type") == "business" or test.get("category") == "logic"]
        
        if business_tests:
            passed_business = [test for test in business_tests if test.get("status") == "passed"]
            if business_tests:
                business_pass_rate = len(passed_business) / len(business_tests)
                score = business_pass_rate
        
        # Analyze alignment with business goals
        goal_alignment = self._analyze_goal_alignment(test_results, business_goals)
        score = (score + goal_alignment) / 2
        
        return min(1.0, max(0.0, score))
    
    def _determine_confidence_level(self, overall_score: float, test_results: Dict) -> str:
        """Determine confidence level based on score and test coverage"""
        test_coverage = test_results.get("test_coverage", 0.5)
        
        if overall_score > 0.9 and test_coverage > 0.8:
            return "very_high"
        elif overall_score > 0.8 and test_coverage > 0.7:
            return "high"
        elif overall_score > 0.7 and test_coverage > 0.6:
            return "medium"
        elif overall_score > 0.6:
            return "low"
        else:
            return "very_low"
    
    def _calculate_business_alignment(self, test_results: Dict, business_goals: str, context: Dict) -> float:
        """Calculate alignment with business goals"""
        alignment_score = 0.7  # Base score
        
        # Extract key business objectives from goals
        business_objectives = self._extract_business_objectives(business_goals)
        
        # Check test coverage of business objectives
        covered_objectives = 0
        for objective in business_objectives:
            if self._is_objective_covered(objective, test_results):
                covered_objectives += 1
        
        if business_objectives:
            alignment_score = covered_objectives / len(business_objectives)
        
        return min(1.0, max(0.0, alignment_score))
    
    def _extract_business_objectives(self, business_goals: str) -> List[str]:
        """Extract key business objectives from goals text"""
        objectives = []
        
        # Common business objective keywords
        objective_keywords = {
            "revenue": ["revenue", "sales", "income", "profit"],
            "customer_satisfaction": ["satisfaction", "customer", "experience", "happiness"],
            "efficiency": ["efficiency", "productivity", "speed", "performance"],
            "security": ["security", "safety", "protection", "compliance"],
            "scalability": ["scalability", "growth", "capacity", "load"],
            "usability": ["usability", "ease", "accessibility", "user"]
        }
        
        goals_lower = business_goals.lower()
        for objective, keywords in objective_keywords.items():
            if any(keyword in goals_lower for keyword in keywords):
                objectives.append(objective)
        
        return objectives
    
    def _is_objective_covered(self, objective: str, test_results: Dict) -> bool:
        """Check if a business objective is covered by test results"""
        test_categories = [test.get("category", "") for test in test_results.get("test_results", [])]
        
        objective_mapping = {
            "revenue": ["payment", "checkout", "billing", "transaction"],
            "customer_satisfaction": ["ui", "ux", "experience", "satisfaction"],
            "efficiency": ["performance", "speed", "response", "load"],
            "security": ["security", "auth", "vulnerability", "penetration"],
            "scalability": ["load", "stress", "capacity", "performance"],
            "usability": ["usability", "accessibility", "ui", "user"]
        }
        
        relevant_categories = objective_mapping.get(objective, [])
        return any(category in test_categories for category in relevant_categories)
    
    def _analyze_goal_alignment(self, test_results: Dict, business_goals: str) -> float:
        """Analyze alignment between test results and business goals"""
        # Simple text-based alignment analysis
        test_descriptions = " ".join([test.get("description", "") for test in test_results.get("test_results", [])])
        
        # Use TF-IDF for similarity calculation
        documents = [business_goals, test_descriptions]
        vectorizer = TfidfVectorizer().fit_transform(documents)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(vectorizer[0:1], vectorizer[1:2])[0][0]
        
        return float(similarity)
    
    def _generate_verification_recommendations(self, detailed_scores: Dict, test_results: Dict) -> List[str]:
        """Generate recommendations based on verification scores"""
        recommendations = []
        
        # Analyze each criterion score
        for criterion, score in detailed_scores.items():
            if score < 0.7:
                if criterion == "ui_layout":
                    recommendations.append("Improve UI layout consistency and visual design")
                elif criterion == "functionality":
                    recommendations.append("Focus on fixing core functional issues")
                elif criterion == "performance":
                    recommendations.append("Optimize performance and response times")
                elif criterion == "user_experience":
                    recommendations.append("Enhance user experience and usability")
                elif criterion == "business_logic":
                    recommendations.append("Review and improve business logic implementation")
        
        # Add general recommendations based on overall results
        overall_pass_rate = test_results.get("overall_pass_rate", 0.5)
        if overall_pass_rate < 0.8:
            recommendations.append("Increase test coverage and fix failing tests")
        
        test_coverage = test_results.get("test_coverage", 0.5)
        if test_coverage < 0.7:
            recommendations.append("Expand test coverage for better quality assurance")
        
        return recommendations
    
    def _generate_verification_summary(self, verification_result: Dict) -> str:
        """Generate human-readable verification summary"""
        overall_score = verification_result["overall_score"]
        confidence = verification_result["confidence_level"]
        business_alignment = verification_result["business_alignment"]
        
        summary = f"**Verification Summary**\n\n"
        summary += f"Overall Score: {overall_score:.2f}/1.00 ({confidence.upper()} confidence)\n"
        summary += f"Business Alignment: {business_alignment:.2f}/1.00\n\n"
        
        # Add criterion breakdown
        summary += "**Criterion Breakdown:**\n"
        for criterion, score in verification_result["detailed_scores"].items():
            criterion_name = criterion.replace("_", " ").title()
            summary += f"• {criterion_name}: {score:.2f}/1.00\n"
        
        # Add recommendations if any
        recommendations = verification_result.get("recommendations", [])
        if recommendations:
            summary += f"\n**Recommendations:**\n"
            for i, rec in enumerate(recommendations, 1):
                summary += f"{i}. {rec}\n"
        
        return summary