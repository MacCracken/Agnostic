import os
import sys
import json
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import logging
import git
from pathlib import Path

logger = logging.getLogger(__name__)

class RiskBasedPrioritization:
    """Advanced risk-based test prioritization system"""
    
    def __init__(self):
        self.risk_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.feature_scaler = StandardScaler()
        self.historical_data = []
        self.risk_factors = {
            "code_change_complexity": 0.3,
            "historical_failure_rate": 0.25,
            "business_criticality": 0.2,
            "user_impact": 0.15,
            "security_sensitivity": 0.1
        }
    
    async def prioritize_tests(self, test_suite: Dict[str, Any], code_changes: List[Dict], 
                               historical_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Prioritize tests based on comprehensive risk analysis"""
        prioritization_result = {
            "original_order": [test["id"] for test in test_suite.get("test_cases", [])],
            "prioritized_order": [],
            "risk_scores": {},
            "risk_factors_analysis": {},
            "prioritization_strategy": "risk_based_comprehensive",
            "estimated_time_savings": 0.0,
            "confidence_score": 0.0
        }
        
        # Calculate risk scores for each test
        test_cases = test_suite.get("test_cases", [])
        risk_scores = {}
        
        for test_case in test_cases:
            risk_score = await self._calculate_comprehensive_risk_score(
                test_case, code_changes, historical_data
            )
            risk_scores[test_case["id"]] = risk_score
        
        prioritization_result["risk_scores"] = risk_scores
        
        # Sort tests by risk score (highest first)
        sorted_tests = sorted(test_cases, key=lambda x: risk_scores.get(x["id"], 0), reverse=True)
        prioritization_result["prioritized_order"] = [test["id"] for test in sorted_tests]
        
        # Analyze risk factors
        risk_factors_analysis = self._analyze_risk_factors(risk_scores, test_cases)
        prioritization_result["risk_factors_analysis"] = risk_factors_analysis
        
        # Calculate confidence score
        prioritization_result["confidence_score"] = self._calculate_prioritization_confidence(
            risk_scores, code_changes, historical_data
        )
        
        # Estimate time savings
        prioritization_result["estimated_time_savings"] = self._estimate_time_savings(
            test_cases, sorted_tests, risk_scores
        )
        
        return prioritization_result
    
    async def _calculate_comprehensive_risk_score(self, test_case: Dict, code_changes: List[Dict], 
                                                historical_data: Optional[List[Dict]]) -> float:
        """Calculate comprehensive risk score for a test case"""
        risk_components = {}
        
        # 1. Code change complexity impact
        code_change_risk = self._assess_code_change_impact(test_case, code_changes)
        risk_components["code_change_complexity"] = code_change_risk
        
        # 2. Historical failure rate
        historical_risk = self._assess_historical_failure_risk(test_case, historical_data)
        risk_components["historical_failure_rate"] = historical_risk
        
        # 3. Business criticality
        business_risk = self._assess_business_criticality(test_case)
        risk_components["business_criticality"] = business_risk
        
        # 4. User impact
        user_impact_risk = self._assess_user_impact(test_case)
        risk_components["user_impact"] = user_impact_risk
        
        # 5. Security sensitivity
        security_risk = self._assess_security_sensitivity(test_case)
        risk_components["security_sensitivity"] = security_risk
        
        # Calculate weighted risk score
        total_risk = 0.0
        for factor, weight in self.risk_factors.items():
            total_risk += risk_components.get(factor, 0.0) * weight
        
        return min(1.0, max(0.0, total_risk))
    
    def _assess_code_change_impact(self, test_case: Dict, code_changes: List[Dict]) -> float:
        """Assess risk from code changes"""
        if not code_changes:
            return 0.1  # Minimal risk if no changes
        
        impact_score = 0.0
        test_areas = test_case.get("areas", [])
        test_components = test_case.get("components", [])
        test_dependencies = test_case.get("dependencies", [])
        
        for change in code_changes:
            change_files = change.get("files", [])
            change_components = change.get("components", [])
            change_complexity = change.get("complexity", "medium")
            
            # File overlap analysis
            file_overlap = 0
            for test_area in test_areas:
                for file in change_files:
                    if test_area in file or file in test_area:
                        file_overlap += 1
            
            # Component overlap analysis
            component_overlap = len(set(test_components) & set(change_components))
            
            # Dependency impact
            dependency_impact = 0
            for dep in test_dependencies:
                if any(dep in file for file in change_files):
                    dependency_impact += 1
            
            # Complexity weighting
            complexity_weight = {"low": 0.5, "medium": 1.0, "high": 1.5, "critical": 2.0}.get(change_complexity, 1.0)
            
            # Calculate change impact
            change_impact = (file_overlap * 0.4 + component_overlap * 0.4 + dependency_impact * 0.2) * complexity_weight
            impact_score += change_impact
        
        # Normalize and cap the score
        normalized_score = min(1.0, impact_score / 10.0)
        return max(0.1, normalized_score)
    
    def _assess_historical_failure_risk(self, test_case: Dict, historical_data: Optional[List[Dict]]) -> float:
        """Assess risk based on historical failure patterns"""
        if not historical_data:
            return 0.3  # Default medium risk
        
        test_id = test_case["id"]
        test_type = test_case.get("type", "functional")
        
        # Find historical data for this test
        test_history = [h for h in historical_data if h.get("test_id") == test_id]
        
        if not test_history:
            # Use type-based historical data
            type_history = [h for h in historical_data if h.get("test_type") == test_type]
            if type_history:
                avg_failure_rate = sum(h.get("failure_rate", 0.1) for h in type_history) / len(type_history)
                return avg_failure_rate
            else:
                return 0.3  # Default medium risk
        
        # Calculate failure metrics
        recent_history = test_history[-10:]  # Last 10 runs
        failure_rate = sum(1 for h in recent_history if h.get("status") == "failed") / len(recent_history)
        
        # Weight recent failures more heavily
        weighted_failure_rate = 0.0
        total_weight = 0.0
        
        for i, run in enumerate(recent_history):
            weight = (i + 1) / len(recent_history)  # More recent = higher weight
            if run.get("status") == "failed":
                weighted_failure_rate += weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_failure_rate /= total_weight
        
        # Consider failure trend
        if len(recent_history) >= 5:
            recent_failures = sum(1 for h in recent_history[-5:] if h.get("status") == "failed")
            older_failures = sum(1 for h in recent_history[-10:-5] if h.get("status") == "failed")
            
            if recent_failures > older_failures:
                weighted_failure_rate *= 1.2  # Increasing failure trend
            elif recent_failures < older_failures:
                weighted_failure_rate *= 0.8  # Decreasing failure trend
        
        return min(1.0, max(0.1, weighted_failure_rate))
    
    def _assess_business_criticality(self, test_case: Dict) -> float:
        """Assess business criticality risk"""
        priority = test_case.get("priority", "medium").lower()
        test_tags = test_case.get("tags", [])
        test_name = test_case.get("name", "").lower()
        
        # Base criticality by priority
        priority_scores = {
            "critical": 0.9,
            "high": 0.7,
            "medium": 0.5,
            "low": 0.3
        }
        base_score = priority_scores.get(priority, 0.5)
        
        # Adjust based on business-critical keywords
        business_keywords = [
            "payment", "billing", "revenue", "checkout", "transaction",
            "login", "authentication", "security", "compliance",
            "registration", "user", "profile", "data"
        ]
        
        keyword_bonus = 0.0
        for keyword in business_keywords:
            if keyword in test_name or keyword in test_tags:
                keyword_bonus += 0.1
        
        # Cap the bonus
        keyword_bonus = min(0.3, keyword_bonus)
        
        return min(1.0, base_score + keyword_bonus)
    
    def _assess_user_impact(self, test_case: Dict) -> float:
        """Assess user impact risk"""
        test_type = test_case.get("type", "functional")
        user_facing = test_case.get("user_facing", True)
        test_name = test_case.get("name", "").lower()
        
        # Base impact by test type
        type_impact = {
            "ui": 0.9,
            "ux": 0.8,
            "functional": 0.7,
            "integration": 0.6,
            "api": 0.4,
            "performance": 0.5,
            "security": 0.8,
            "unit": 0.2
        }
        
        base_score = type_impact.get(test_type, 0.5)
        
        # Adjust for user-facing tests
        if not user_facing:
            base_score *= 0.5
        
        # User journey impact
        user_journey_keywords = ["login", "checkout", "search", "profile", "dashboard", "home"]
        journey_bonus = 0.0
        
        for keyword in user_journey_keywords:
            if keyword in test_name:
                journey_bonus += 0.15
        
        journey_bonus = min(0.3, journey_bonus)
        
        return min(1.0, base_score + journey_bonus)
    
    def _assess_security_sensitivity(self, test_case: Dict) -> float:
        """Assess security sensitivity risk"""
        test_type = test_case.get("type", "functional")
        test_tags = test_case.get("tags", [])
        test_name = test_case.get("name", "").lower()
        
        # Security-sensitive test types
        security_types = ["security", "penetration", "vulnerability", "auth", "compliance"]
        if test_type in security_types:
            return 0.9
        
        # Security keywords
        security_keywords = [
            "password", "token", "session", "auth", "login", "permission",
            "encryption", "ssl", "tls", "xss", "sql", "injection", "csrf",
            "vulnerability", "security", "compliance", "audit"
        ]
        
        security_score = 0.0
        for keyword in security_keywords:
            if keyword in test_name or keyword in test_tags:
                security_score += 0.2
        
        # Data handling sensitivity
        data_keywords = ["pii", "personal", "sensitive", "financial", "health", "payment"]
        for keyword in data_keywords:
            if keyword in test_name:
                security_score += 0.15
        
        return min(1.0, max(0.1, security_score))
    
    def _analyze_risk_factors(self, risk_scores: Dict, test_cases: List[Dict]) -> Dict[str, Any]:
        """Analyze risk factors across the test suite"""
        analysis = {
            "high_risk_tests": [],
            "medium_risk_tests": [],
            "low_risk_tests": [],
            "risk_distribution": {"high": 0, "medium": 0, "low": 0},
            "dominant_risk_factors": {},
            "risk_hotspots": []
        }
        
        # Categorize tests by risk level
        for test_case in test_cases:
            test_id = test_case["id"]
            risk_score = risk_scores.get(test_id, 0.0)
            
            if risk_score > 0.7:
                analysis["high_risk_tests"].append(test_id)
                analysis["risk_distribution"]["high"] += 1
            elif risk_score > 0.4:
                analysis["medium_risk_tests"].append(test_id)
                analysis["risk_distribution"]["medium"] += 1
            else:
                analysis["low_risk_tests"].append(test_id)
                analysis["risk_distribution"]["low"] += 1
        
        # Identify dominant risk factors
        factor_analysis = {}
        for test_case in test_cases:
            test_id = test_case["id"]
            test_areas = test_case.get("areas", [])
            test_components = test_case.get("components", [])
            
            for area in test_areas:
                if area not in factor_analysis:
                    factor_analysis[area] = {"count": 0, "total_risk": 0.0}
                factor_analysis[area]["count"] += 1
                factor_analysis[area]["total_risk"] += risk_scores.get(test_id, 0.0)
        
        # Calculate average risk per factor
        for factor, data in factor_analysis.items():
            avg_risk = data["total_risk"] / data["count"] if data["count"] > 0 else 0.0
            analysis["dominant_risk_factors"][factor] = {
                "test_count": data["count"],
                "average_risk": avg_risk,
                "risk_level": "high" if avg_risk > 0.7 else "medium" if avg_risk > 0.4 else "low"
            }
        
        # Identify risk hotspots (areas with high average risk)
        hotspots = sorted(
            [(factor, data["average_risk"]) for factor, data in analysis["dominant_risk_factors"].items()],
            key=lambda x: x[1],
            reverse=True
        )
        analysis["risk_hotspots"] = hotspots[:5]  # Top 5 hotspots
        
        return analysis
    
    def _calculate_prioritization_confidence(self, risk_scores: Dict, code_changes: List[Dict], 
                                            historical_data: Optional[List[Dict]]) -> float:
        """Calculate confidence in the prioritization"""
        confidence_factors = {}
        
        # Data availability confidence
        if historical_data and len(historical_data) > 10:
            confidence_factors["historical_data"] = 0.9
        elif historical_data:
            confidence_factors["historical_data"] = 0.6
        else:
            confidence_factors["historical_data"] = 0.3
        
        # Code change analysis confidence
        if code_changes:
            confidence_factors["code_changes"] = 0.8
        else:
            confidence_factors["code_changes"] = 0.4
        
        # Risk score distribution confidence
        if risk_scores:
            risk_variance = np.var(list(risk_scores.values()))
            if risk_variance > 0.1:  # Good variance in risk scores
                confidence_factors["risk_distribution"] = 0.8
            else:  # Low variance, less confident
                confidence_factors["risk_distribution"] = 0.5
        else:
            confidence_factors["risk_distribution"] = 0.3
        
        # Overall confidence (weighted average)
        weights = {"historical_data": 0.4, "code_changes": 0.3, "risk_distribution": 0.3}
        total_confidence = 0.0
        total_weight = 0.0
        
        for factor, weight in weights.items():
            total_confidence += confidence_factors.get(factor, 0.5) * weight
            total_weight += weight
        
        return total_confidence / total_weight if total_weight > 0 else 0.5
    
    def _estimate_time_savings(self, original_tests: List[Dict], prioritized_tests: List[Dict], 
                             risk_scores: Dict) -> float:
        """Estimate time savings from risk-based prioritization"""
        if not original_tests or not prioritized_tests:
            return 0.0
        
        # Assume average test execution time
        avg_test_time = 30  # seconds
        
        # Calculate time to find first failure with original order
        original_time_to_failure = 0.0
        for i, test in enumerate(original_tests):
            test_id = test["id"]
            risk_score = risk_scores.get(test_id, 0.0)
            
            # Probability of failure based on risk score
            failure_probability = risk_score
            
            # Expected time to detect failure
            original_time_to_failure += avg_test_time * (1 - failure_probability)
            
            # If this test fails, stop
            if failure_probability > 0.5:  # Assume high-risk tests are more likely to fail
                break
        
        # Calculate time to find first failure with prioritized order
        prioritized_time_to_failure = 0.0
        for i, test in enumerate(prioritized_tests):
            test_id = test["id"]
            risk_score = risk_scores.get(test_id, 0.0)
            
            failure_probability = risk_score
            prioritized_time_to_failure += avg_test_time * (1 - failure_probability)
            
            if failure_probability > 0.5:
                break
        
        # Time savings is the difference
        time_savings = original_time_to_failure - prioritized_time_to_failure
        return max(0.0, time_savings)

class ContextAwareExploratoryTesting:
    """Context-aware exploratory testing system"""
    
    def __init__(self):
        self.exploratory_strategies = {
            "business_flow": self._generate_business_flow_scenarios,
            "edge_case": self._generate_edge_case_scenarios,
            "user_persona": self._generate_persona_based_scenarios,
            "integration": self._generate_integration_scenarios,
            "performance": self._generate_performance_scenarios
        }
        self.context_history = []
    
    async def generate_exploratory_scenarios(self, application_context: Dict[str, Any], 
                                           user_behavior_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Generate context-aware exploratory test scenarios"""
        generation_result = {
            "application_context": application_context,
            "generated_scenarios": [],
            "scenario_categories": {},
            "coverage_analysis": {},
            "recommendations": [],
            "confidence_score": 0.0
        }
        
        # Analyze application context
        context_analysis = self._analyze_application_context(application_context)
        
        # Generate scenarios for each strategy
        all_scenarios = []
        for strategy_name, strategy_func in self.exploratory_strategies.items():
            try:
                scenarios = await strategy_func(application_context, user_behavior_data, context_analysis)
                all_scenarios.extend(scenarios)
                
                # Categorize scenarios
                generation_result["scenario_categories"][strategy_name] = {
                    "count": len(scenarios),
                    "scenarios": [s["id"] for s in scenarios]
                }
                
            except Exception as e:
                logger.error(f"Exploratory strategy {strategy_name} failed: {e}")
                continue
        
        generation_result["generated_scenarios"] = all_scenarios
        
        # Analyze coverage
        coverage_analysis = self._analyze_exploratory_coverage(all_scenarios, application_context)
        generation_result["coverage_analysis"] = coverage_analysis
        
        # Generate recommendations
        recommendations = self._generate_exploratory_recommendations(
            all_scenarios, context_analysis, coverage_analysis
        )
        generation_result["recommendations"] = recommendations
        
        # Calculate confidence score
        generation_result["confidence_score"] = self._calculate_generation_confidence(
            all_scenarios, context_analysis
        )
        
        # Store in history
        self.context_history.append({
            "timestamp": datetime.now().isoformat(),
            "context": application_context,
            "scenarios": all_scenarios,
            "result": generation_result
        })
        
        return generation_result
    
    def _analyze_application_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze application context for scenario generation"""
        analysis = {
            "application_type": self._identify_application_type(context),
            "key_features": self._extract_key_features(context),
            "user_journeys": self._identify_user_journeys(context),
            "integration_points": self._identify_integration_points(context),
            "risk_areas": self._identify_risk_areas(context),
            "complexity_factors": self._assess_complexity_factors(context)
        }
        return analysis
    
    def _identify_application_type(self, context: Dict) -> str:
        """Identify the type of application"""
        app_info = context.get("application_info", {})
        features = context.get("features", [])
        
        feature_indicators = {
            "e-commerce": ["cart", "checkout", "payment", "product", "order"],
            "social": ["profile", "post", "comment", "like", "follow"],
            "crm": ["lead", "customer", "deal", "contact", "pipeline"],
            "healthcare": ["patient", "appointment", "medical", "record", "prescription"],
            "education": ["course", "student", "lesson", "assignment", "grade"],
            "finance": ["account", "transaction", "transfer", "balance", "investment"]
        }
        
        all_features = " ".join(features).lower()
        
        for app_type, indicators in feature_indicators.items():
            if sum(1 for indicator in indicators if indicator in all_features) >= 2:
                return app_type
        
        return "generic"
    
    def _extract_key_features(self, context: Dict) -> List[str]:
        """Extract key features from context"""
        return context.get("features", [])
    
    def _identify_user_journeys(self, context: Dict) -> List[str]:
        """Identify common user journeys"""
        journeys = context.get("user_journeys", [])
        
        # If not provided, infer from features
        if not journeys:
            features = context.get("features", [])
            if "login" in features:
                journeys.append("authentication_flow")
            if "cart" in features and "checkout" in features:
                journeys.append("purchase_journey")
            if "profile" in features:
                journeys.append("user_management")
        
        return journeys
    
    def _identify_integration_points(self, context: Dict) -> List[str]:
        """Identify integration points"""
        integrations = context.get("integrations", [])
        
        # Common integration patterns
        if not integrations:
            features = context.get("features", [])
            if "payment" in features:
                integrations.append("payment_gateway")
            if "email" in features:
                integrations.append("email_service")
            if "search" in features:
                integrations.append("search_engine")
        
        return integrations
    
    def _identify_risk_areas(self, context: Dict) -> List[str]:
        """Identify potential risk areas"""
        risk_areas = []
        features = context.get("features", [])
        
        risk_indicators = {
            "authentication": ["login", "auth", "password", "token"],
            "payment": ["payment", "checkout", "billing", "transaction"],
            "data_integrity": ["database", "save", "update", "delete"],
            "performance": ["search", "filter", "load", "export"],
            "security": ["user", "profile", "permission", "admin"]
        }
        
        all_features = " ".join(features).lower()
        
        for risk_area, indicators in risk_indicators.items():
            if any(indicator in all_features for indicator in indicators):
                risk_areas.append(risk_area)
        
        return risk_areas
    
    def _assess_complexity_factors(self, context: Dict) -> Dict[str, Any]:
        """Assess complexity factors"""
        features = context.get("features", [])
        user_roles = context.get("user_roles", [])
        integrations = context.get("integrations", [])
        
        complexity = {
            "feature_count": len(features),
            "role_count": len(user_roles),
            "integration_count": len(integrations),
            "overall_complexity": "medium"
        }
        
        # Calculate overall complexity
        complexity_score = (len(features) * 0.4 + len(user_roles) * 0.3 + len(integrations) * 0.3)
        
        if complexity_score > 15:
            complexity["overall_complexity"] = "high"
        elif complexity_score < 8:
            complexity["overall_complexity"] = "low"
        
        return complexity
    
    async def _generate_business_flow_scenarios(self, context: Dict, user_data: Optional[List[Dict]], 
                                              analysis: Dict) -> List[Dict]:
        """Generate business flow-based exploratory scenarios"""
        scenarios = []
        user_journeys = analysis.get("user_journeys", [])
        
        for journey in user_journeys:
            scenario = {
                "id": f"business_flow_{journey}_{len(scenarios) + 1}",
                "type": "business_flow",
                "title": f"Exploratory: {journey.replace('_', ' ').title()}",
                "description": f"Context-aware exploratory testing of {journey}",
                "steps": self._generate_journey_steps(journey, context),
                "risk_areas": self._identify_journey_risks(journey, analysis),
                "success_criteria": self._define_journey_success_criteria(journey),
                "priority": "medium"
            }
            scenarios.append(scenario)
        
        return scenarios
    
    async def _generate_edge_case_scenarios(self, context: Dict, user_data: Optional[List[Dict]], 
                                           analysis: Dict) -> List[Dict]:
        """Generate edge case exploratory scenarios"""
        scenarios = []
        risk_areas = analysis.get("risk_areas", [])
        
        edge_case_types = [
            {"type": "boundary_values", "description": "Test at input boundaries"},
            {"type": "invalid_inputs", "description": "Test with invalid/malformed inputs"},
            {"type": "resource_exhaustion", "description": "Test with limited resources"},
            {"type": "concurrent_operations", "description": "Test simultaneous operations"},
            {"type": "error_conditions", "description": "Test various error conditions"}
        ]
        
        for edge_case in edge_case_types:
            for risk_area in risk_areas[:2]:  # Limit to top 2 risk areas
                scenario = {
                    "id": f"edge_case_{edge_case['type']}_{risk_area}_{len(scenarios) + 1}",
                    "type": "edge_case",
                    "title": f"Edge Case: {edge_case['type'].title()} in {risk_area.title()}",
                    "description": edge_case["description"],
                    "test_conditions": self._generate_edge_case_conditions(edge_case["type"], risk_area, context),
                    "expected_behaviors": self._define_edge_case_expectations(edge_case["type"], risk_area),
                    "priority": "high"
                }
                scenarios.append(scenario)
        
        return scenarios
    
    async def _generate_persona_based_scenarios(self, context: Dict, user_data: Optional[List[Dict]], 
                                              analysis: Dict) -> List[Dict]:
        """Generate persona-based exploratory scenarios"""
        scenarios = []
        user_roles = context.get("user_roles", ["user", "admin"])
        
        # Define personas based on roles
        personas = {
            "user": {"name": "Regular User", "characteristics": ["basic_usage", "error_prone"], "goals": ["complete_tasks", "get_help"]},
            "admin": {"name": "Administrator", "characteristics": ["advanced_usage", "system_management"], "goals": ["maintain_system", "troubleshoot"]},
            "guest": {"name": "Guest User", "characteristics": ["limited_access", "exploration"], "goals": ["explore", "register"]},
            "power_user": {"name": "Power User", "characteristics": ["expert_usage", "efficiency_focused"], "goals": ["optimize_workflow", "advanced_features"]}
        }
        
        for role in user_roles:
            if role in personas:
                persona = personas[role]
                scenario = {
                    "id": f"persona_{role}_{len(scenarios) + 1}",
                    "type": "persona_based",
                    "title": f"Persona Testing: {persona['name']}",
                    "description": f"Test from perspective of {persona['name']}",
                    "persona": persona,
                    "test_scenarios": self._generate_persona_scenarios(persona, context),
                    "success_metrics": self._define_persona_success_metrics(persona),
                    "priority": "medium"
                }
                scenarios.append(scenario)
        
        return scenarios
    
    async def _generate_integration_scenarios(self, context: Dict, user_data: Optional[List[Dict]], 
                                            analysis: Dict) -> List[Dict]:
        """Generate integration-focused exploratory scenarios"""
        scenarios = []
        integration_points = analysis.get("integration_points", [])
        
        for integration in integration_points:
            scenario = {
                "id": f"integration_{integration}_{len(scenarios) + 1}",
                "type": "integration",
                "title": f"Integration Testing: {integration.replace('_', ' ').title()}",
                "description": f"Exploratory testing of {integration} integration",
                "integration_point": integration,
                "test_scenarios": self._generate_integration_test_scenarios(integration, context),
                "failure_conditions": self._identify_integration_failure_conditions(integration),
                "recovery_scenarios": self._define_integration_recovery_scenarios(integration),
                "priority": "high"
            }
            scenarios.append(scenario)
        
        return scenarios
    
    async def _generate_performance_scenarios(self, context: Dict, user_data: Optional[List[Dict]], 
                                            analysis: Dict) -> List[Dict]:
        """Generate performance-focused exploratory scenarios"""
        scenarios = []
        
        performance_scenarios = [
            {"type": "load_testing", "description": "Test system under expected load"},
            {"type": "stress_testing", "description": "Test system beyond expected limits"},
            {"type": "volume_testing", "description": "Test with large data volumes"},
            {"type": "endurance_testing", "description": "Test system over extended periods"},
            {"type": "spike_testing", "description": "Test with sudden load increases"}
        ]
        
        for perf_scenario in performance_scenarios:
            scenario = {
                "id": f"performance_{perf_scenario['type']}_{len(scenarios) + 1}",
                "type": "performance",
                "title": f"Performance: {perf_scenario['type'].title()}",
                "description": perf_scenario["description"],
                "test_conditions": self._generate_performance_test_conditions(perf_scenario["type"], context),
                "metrics_to_monitor": self._define_performance_metrics(perf_scenario["type"]),
                "acceptance_criteria": self._define_performance_criteria(perf_scenario["type"]),
                "priority": "medium"
            }
            scenarios.append(scenario)
        
        return scenarios
    
    def _generate_journey_steps(self, journey: str, context: Dict) -> List[str]:
        """Generate steps for a user journey"""
        journey_steps = {
            "authentication_flow": [
                "Navigate to login page",
                "Enter valid credentials",
                "Submit login form",
                "Verify successful authentication",
                "Check user session state"
            ],
            "purchase_journey": [
                "Browse products",
                "Add item to cart",
                "Proceed to checkout",
                "Enter shipping information",
                "Enter payment details",
                "Complete purchase",
                "Verify order confirmation"
            ],
            "user_management": [
                "Navigate to profile",
                "Update personal information",
                "Change password",
                "Verify changes saved",
                "Log out and log back in"
            ]
        }
        
        return journey_steps.get(journey, [f"Execute {journey} steps"])
    
    def _identify_journey_risks(self, journey: str, analysis: Dict) -> List[str]:
        """Identify risks for a specific journey"""
        risk_mapping = {
            "authentication_flow": ["session_timeout", "invalid_credentials", "account_lockout"],
            "purchase_journey": ["payment_failure", "inventory_issues", "shipping_problems"],
            "user_management": ["data_corruption", "permission_errors", "validation_failures"]
        }
        
        return risk_mapping.get(journey, ["general_failure"])
    
    def _define_journey_success_criteria(self, journey: str) -> List[str]:
        """Define success criteria for a journey"""
        success_criteria = {
            "authentication_flow": [
                "User can successfully log in",
                "Session is properly established",
                "User is redirected to correct page"
            ],
            "purchase_journey": [
                "Order is successfully placed",
                "Payment is processed",
                "User receives order confirmation"
            ],
            "user_management": [
                "Changes are saved correctly",
                "Data validation works",
                "User experience is smooth"
            ]
        }
        
        return success_criteria.get(journey, ["Journey completes successfully"])
    
    def _generate_edge_case_conditions(self, edge_type: str, risk_area: str, context: Dict) -> List[str]:
        """Generate test conditions for edge cases"""
        conditions = {
            "boundary_values": [
                f"Test {risk_area} with minimum valid input",
                f"Test {risk_area} with maximum valid input",
                f"Test {risk_area} with values just outside boundaries"
            ],
            "invalid_inputs": [
                f"Test {risk_area} with null/empty values",
                f"Test {risk_area} with malformed data",
                f"Test {risk_area} with special characters"
            ],
            "resource_exhaustion": [
                f"Test {risk_area} with limited memory",
                f"Test {risk_area} with full disk space",
                f"Test {risk_area} with network timeouts"
            ],
            "concurrent_operations": [
                f"Test {risk_area} with simultaneous users",
                f"Test {risk_area} with concurrent modifications",
                f"Test {risk_area} with race conditions"
            ],
            "error_conditions": [
                f"Test {risk_area} with service unavailable",
                f"Test {risk_area} with network failures",
                f"Test {risk_area} with database errors"
            ]
        }
        
        return conditions.get(edge_type, [f"Test {risk_area} edge conditions"])
    
    def _define_edge_case_expectations(self, edge_type: str, risk_area: str) -> List[str]:
        """Define expected behaviors for edge cases"""
        return [
            "System handles errors gracefully",
            "User receives meaningful error messages",
            "System remains stable",
            "No data corruption occurs"
        ]
    
    def _generate_persona_scenarios(self, persona: Dict, context: Dict) -> List[str]:
        """Generate test scenarios for a persona"""
        characteristics = persona.get("characteristics", [])
        
        if "basic_usage" in characteristics:
            return [
                "Follow standard user workflow",
                "Use common features",
                "Test help and support options"
            ]
        elif "advanced_usage" in characteristics:
            return [
                "Use advanced features",
                "Test keyboard shortcuts",
                "Customize settings and preferences"
            ]
        elif "error_prone" in characteristics:
            return [
                "Make common mistakes",
                "Enter invalid data",
                "Test error recovery"
            ]
        else:
            return ["Test persona-specific workflows"]
    
    def _define_persona_success_metrics(self, persona: Dict) -> List[str]:
        """Define success metrics for a persona"""
        goals = persona.get("goals", [])
        
        metrics = []
        for goal in goals:
            if "complete" in goal.lower():
                metrics.append("Task completion rate")
            elif "efficiency" in goal.lower():
                metrics.append("Time to complete tasks")
            elif "help" in goal.lower():
                metrics.append("Help system effectiveness")
            else:
                metrics.append(f"Goal achievement: {goal}")
        
        return metrics or ["User satisfaction"]
    
    def _generate_integration_test_scenarios(self, integration: str, context: Dict) -> List[str]:
        """Generate integration test scenarios"""
        integration_scenarios = {
            "payment_gateway": [
                "Test successful payment processing",
                "Test payment failure scenarios",
                "Test refund processing",
                "Test timeout scenarios"
            ],
            "email_service": [
                "Test email delivery",
                "Test email template rendering",
                "Test bounce handling",
                "Test unsubscribe functionality"
            ],
            "search_engine": [
                "Test search accuracy",
                "Test search performance",
                "Test search with special characters",
                "Test empty search results"
            ]
        }
        
        return integration_scenarios.get(integration, [f"Test {integration} functionality"])
    
    def _identify_integration_failure_conditions(self, integration: str) -> List[str]:
        """Identify potential integration failure conditions"""
        return [
            "Service unavailable",
            "Network timeout",
            "Invalid response format",
            "Authentication failure",
            "Rate limiting exceeded"
        ]
    
    def _define_integration_recovery_scenarios(self, integration: str) -> List[str]:
        """Define integration recovery scenarios"""
        return [
            "Automatic retry mechanism",
            "Graceful degradation",
            "Fallback to alternative service",
            "User notification of issues",
            "Manual recovery options"
        ]
    
    def _generate_performance_test_conditions(self, perf_type: str, context: Dict) -> List[str]:
        """Generate performance test conditions"""
        conditions = {
            "load_testing": [
                "Simulate expected user load",
                "Test during peak hours",
                "Test with realistic user behavior"
            ],
            "stress_testing": [
                "Exceed expected capacity",
                "Test system limits",
                "Identify breaking points"
            ],
            "volume_testing": [
                "Test with large datasets",
                "Test data processing limits",
                "Test storage capacity"
            ],
            "endurance_testing": [
                "Run extended duration tests",
                "Test for memory leaks",
                "Test system stability over time"
            ],
            "spike_testing": [
                "Simulate sudden load increases",
                "Test recovery after spikes",
                "Test system elasticity"
            ]
        }
        
        return conditions.get(perf_type, [f"Test {perf_type} conditions"])
    
    def _define_performance_metrics(self, perf_type: str) -> List[str]:
        """Define metrics to monitor for performance tests"""
        common_metrics = [
            "Response time",
            "Throughput",
            "Error rate",
            "Resource utilization"
        ]
        
        type_specific = {
            "stress_testing": ["Time to failure", "Recovery time"],
            "endurance_testing": ["Memory usage trend", "Performance degradation"],
            "spike_testing": ["Response during spike", "Recovery time after spike"]
        }
        
        return common_metrics + type_specific.get(perf_type, [])
    
    def _define_performance_criteria(self, perf_type: str) -> List[str]:
        """Define acceptance criteria for performance tests"""
        criteria = {
            "load_testing": [
                "Response time < 2 seconds",
                "Error rate < 1%",
                "System remains stable"
            ],
            "stress_testing": [
                "System fails gracefully",
                "No data corruption",
                "Recovery within acceptable time"
            ],
            "volume_testing": [
                "Process large datasets without failure",
                "Performance remains acceptable",
                "Memory usage within limits"
            ]
        }
        
        return criteria.get(perf_type, ["Performance meets requirements"])
    
    def _analyze_exploratory_coverage(self, scenarios: List[Dict], context: Dict) -> Dict[str, Any]:
        """Analyze coverage provided by exploratory scenarios"""
        coverage = {
            "feature_coverage": {},
            "risk_coverage": {},
            "journey_coverage": {},
            "overall_coverage_score": 0.0
        }
        
        # Analyze feature coverage
        features = context.get("features", [])
        covered_features = set()
        
        for scenario in scenarios:
            scenario_features = scenario.get("covered_features", [])
            covered_features.update(scenario_features)
        
        coverage["feature_coverage"] = {
            "total_features": len(features),
            "covered_features": len(covered_features),
            "coverage_percentage": len(covered_features) / len(features) if features else 0.0,
            "uncovered_features": list(set(features) - covered_features)
        }
        
        # Analyze risk coverage
        risk_areas = context.get("risk_areas", [])
        covered_risks = set()
        
        for scenario in scenarios:
            scenario_risks = scenario.get("risk_areas", [])
            covered_risks.update(scenario_risks)
        
        coverage["risk_coverage"] = {
            "total_risks": len(risk_areas),
            "covered_risks": len(covered_risks),
            "coverage_percentage": len(covered_risks) / len(risk_areas) if risk_areas else 0.0,
            "uncovered_risks": list(set(risk_areas) - covered_risks)
        }
        
        # Calculate overall coverage score
        feature_score = coverage["feature_coverage"]["coverage_percentage"]
        risk_score = coverage["risk_coverage"]["coverage_percentage"]
        coverage["overall_coverage_score"] = (feature_score + risk_score) / 2
        
        return coverage
    
    def _generate_exploratory_recommendations(self, scenarios: List[Dict], analysis: Dict, 
                                            coverage: Dict) -> List[str]:
        """Generate recommendations based on exploratory scenario analysis"""
        recommendations = []
        
        # Coverage-based recommendations
        overall_coverage = coverage.get("overall_coverage_score", 0.0)
        if overall_coverage < 0.7:
            recommendations.append("Increase exploratory test coverage for better quality assurance")
        
        # Risk-based recommendations
        uncovered_risks = coverage.get("risk_coverage", {}).get("uncovered_risks", [])
        if uncovered_risks:
            recommendations.append(f"Add exploratory scenarios for uncovered risk areas: {', '.join(uncovered_risks)}")
        
        # Feature-based recommendations
        uncovered_features = coverage.get("feature_coverage", {}).get("uncovered_features", [])
        if uncovered_features:
            recommendations.append(f"Consider testing uncovered features: {', '.join(uncovered_features[:3])}")
        
        # Scenario type recommendations
        scenario_types = set(s.get("type", "") for s in scenarios)
        if "edge_case" not in scenario_types:
            recommendations.append("Add edge case exploratory scenarios for robustness testing")
        if "persona_based" not in scenario_types:
            recommendations.append("Add persona-based scenarios for better user experience testing")
        
        return recommendations
    
    def _calculate_generation_confidence(self, scenarios: List[Dict], analysis: Dict) -> float:
        """Calculate confidence in scenario generation"""
        confidence_factors = {}
        
        # Scenario count confidence
        if len(scenarios) > 10:
            confidence_factors["scenario_count"] = 0.9
        elif len(scenarios) > 5:
            confidence_factors["scenario_count"] = 0.7
        else:
            confidence_factors["scenario_count"] = 0.5
        
        # Context quality confidence
        context_quality = 0.0
        if analysis.get("key_features"):
            context_quality += 0.3
        if analysis.get("user_journeys"):
            context_quality += 0.3
        if analysis.get("risk_areas"):
            context_quality += 0.2
        if analysis.get("integration_points"):
            context_quality += 0.2
        
        confidence_factors["context_quality"] = context_quality
        
        # Diversity confidence
        scenario_types = set(s.get("type", "") for s in scenarios)
        diversity_score = len(scenario_types) / 5.0  # 5 is the max number of types
        confidence_factors["diversity"] = min(1.0, diversity_score)
        
        # Overall confidence
        weights = {"scenario_count": 0.3, "context_quality": 0.4, "diversity": 0.3}
        total_confidence = 0.0
        
        for factor, weight in weights.items():
            total_confidence += confidence_factors.get(factor, 0.5) * weight
        
        return total_confidence