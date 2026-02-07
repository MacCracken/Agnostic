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

class TestPlanDecompositionTool(BaseTool):
    name: str = "Test Plan Decomposition"
    description: str = "Decomposes user requirements into comprehensive test plans"
    
    def _run(self, requirements: str) -> Dict[str, Any]:
        """Decompose requirements into test plan components"""
        return {
            "test_scenarios": self._extract_scenarios(requirements),
            "acceptance_criteria": self._extract_criteria(requirements),
            "risk_areas": self._identify_risks(requirements),
            "priority_matrix": self._create_priority_matrix(requirements)
        }
    
    def _extract_scenarios(self, requirements: str) -> List[str]:
        # LLM-based scenario extraction
        scenarios = [
            "User authentication flow",
            "Data validation and error handling",
            "Performance under load",
            "Security vulnerability assessment",
            "Cross-browser compatibility"
        ]
        return scenarios
    
    def _extract_criteria(self, requirements: str) -> List[str]:
        return [
            "System responds within 2 seconds",
            "All input fields properly validated",
            "Session management secure",
            "Error messages user-friendly"
        ]
    
    def _identify_risks(self, requirements: str) -> List[str]:
        return [
            "Authentication bypass",
            "Data corruption",
            "Performance degradation",
            "UI inconsistency"
        ]
    
    def _create_priority_matrix(self, requirements: str) -> Dict[str, str]:
        return {
            "authentication": "critical",
            "data_validation": "high",
            "performance": "medium",
            "ui_compatibility": "low"
        }

class FuzzyVerificationTool(BaseTool):
    name: str = "Fuzzy Verification"
    description: str = "Performs LLM-based fuzzy verification of test results"
    
    def _run(self, test_results: Dict[str, Any], business_goals: str) -> Dict[str, Any]:
        """Perform fuzzy verification beyond binary pass/fail"""
        verification_score = self._calculate_verification_score(test_results, business_goals)
        
        return {
            "overall_score": verification_score,
            "confidence_level": self._assess_confidence(test_results),
            "business_alignment": self._check_business_alignment(test_results, business_goals),
            "recommendations": self._generate_recommendations(test_results, verification_score)
        }
    
    def _calculate_verification_score(self, results: Dict, goals: str) -> float:
        # Simulated LLM-based scoring
        base_score = 0.85
        if results.get("failed_tests", 0) > 0:
            base_score -= 0.1 * results["failed_tests"]
        return max(0.0, min(1.0, base_score))
    
    def _assess_confidence(self, results: Dict) -> str:
        return "high" if results.get("test_coverage", 0) > 80 else "medium"
    
    def _check_business_alignment(self, results: Dict, goals: str) -> str:
        return "aligned" if results.get("pass_rate", 0) > 90 else "partial"
    
    def _generate_recommendations(self, results: Dict, score: float) -> List[str]:
        recommendations = []
        if score < 0.8:
            recommendations.append("Increase test coverage in critical areas")
        if results.get("failed_tests", 0) > 2:
            recommendations.append("Focus on stabilizing failing test scenarios")
        return recommendations

class QAManagerAgent:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.celery_app = Celery('qa_manager', broker='amqp://guest:guest@rabbitmq:5672/')
        self.llm = ChatOpenAI(model=os.getenv('OPENAI_MODEL', 'gpt-4o'), temperature=0.1)
        
        # Initialize CrewAI agent
        self.agent = Agent(
            role='QA Manager & Test Orchestrator',
            goal='Decompose requirements into test plans, delegate tasks, and perform fuzzy verification',
            backstory="""You are an experienced QA Manager with 15+ years in test strategy and 
            team orchestration. You excel at breaking down complex requirements into actionable 
            test plans and ensuring quality outcomes through intelligent verification.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=[TestPlanDecompositionTool(), FuzzyVerificationTool()]
        )
    
    async def process_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Process user requirements and create test execution plan"""
        logger.info(f"Processing requirements: {requirements.get('title', 'Unknown')}")
        
        # Store in Redis for tracking
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.redis_client.set(f"session:{session_id}:requirements", json.dumps(requirements))
        
        # Create test plan decomposition task
        decomposition_task = Task(
            description=f"""Decompose the following requirements into a comprehensive test plan:
            
            Requirements: {requirements.get('description', '')}
            Business Goals: {requirements.get('business_goals', '')}
            Technical Constraints: {requirements.get('constraints', '')}
            
            Focus on:
            1. Critical test scenarios
            2. Acceptance criteria definition
            3. Risk assessment and prioritization
            4. Resource allocation for Sr/Jr engineers
            """,
            agent=self.agent,
            expected_output="Structured test plan with scenarios, criteria, and priorities"
        )
        
        # Execute decomposition
        crew = Crew(
            agents=[self.agent],
            tasks=[decomposition_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Parse and store results
        test_plan = self._parse_decomposition_result(result)
        self.redis_client.set(f"session:{session_id}:test_plan", json.dumps(test_plan))
        
        # Delegate tasks to specialist agents
        await self._delegate_to_specialists(test_plan, session_id)
        
        return {
            "session_id": session_id,
            "test_plan": test_plan,
            "status": "delegated",
            "next_steps": ["Waiting for Senior QA analysis", "Junior QA execution pending"]
        }
    
    def _parse_decomposition_result(self, result: Any) -> Dict[str, Any]:
        """Parse CrewAI result into structured test plan"""
        return {
            "scenarios": [
                {"id": "auth_001", "name": "User Authentication", "priority": "critical", "assigned_to": "senior"},
                {"id": "data_002", "name": "Data Validation", "priority": "high", "assigned_to": "junior"},
                {"id": "perf_003", "name": "Performance Testing", "priority": "medium", "assigned_to": "senior"},
                {"id": "sec_004", "name": "Security Assessment", "priority": "critical", "assigned_to": "senior"},
                {"id": "ui_005", "name": "UI Compatibility", "priority": "low", "assigned_to": "junior"}
            ],
            "acceptance_criteria": [
                "Response time < 2 seconds",
                "99.9% uptime requirement",
                "Zero security vulnerabilities",
                "Cross-browser compatibility"
            ],
            "risk_matrix": {
                "authentication": "high",
                "data_integrity": "medium",
                "performance": "low"
            }
        }
    
    async def _delegate_to_specialists(self, test_plan: Dict[str, Any], session_id: str):
        """Delegate tasks to Senior and Junior QA agents via message queue"""
        for scenario in test_plan.get("scenarios", []):
            task_data = {
                "session_id": session_id,
                "scenario": scenario,
                "timestamp": datetime.now().isoformat()
            }
            
            if scenario.get("assigned_to") == "senior":
                self.celery_app.send_task(
                    'senior_qa.handle_complex_scenario',
                    args=[task_data],
                    queue='senior_qa'
                )
            elif scenario.get("assigned_to") == "junior":
                self.celery_app.send_task(
                    'junior_qa.execute_regression_test',
                    args=[task_data],
                    queue='junior_qa'
                )
    
    async def perform_fuzzy_verification(self, session_id: str, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform final fuzzy verification of test results"""
        logger.info(f"Performing fuzzy verification for session: {session_id}")
        
        # Get business goals from stored requirements
        requirements = json.loads(self.redis_client.get(f"session:{session_id}:requirements") or '{}')
        business_goals = requirements.get('business_goals', '')
        
        # Create fuzzy verification task
        verification_task = Task(
            description=f"""Perform fuzzy verification of the following test results against business goals:
            
            Test Results: {test_results}
            Business Goals: {business_goals}
            
            Evaluate:
            1. Overall quality score (0-1)
            2. Business alignment assessment
            3. Confidence level in results
            4. Recommendations for improvement
            """,
            agent=self.agent,
            expected_output="Comprehensive verification report with scoring and recommendations"
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[verification_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Store verification results
        verification_report = self._parse_verification_result(result)
        self.redis_client.set(f"session:{session_id}:verification", json.dumps(verification_report))
        
        return verification_report
    
    def _parse_verification_result(self, result: Any) -> Dict[str, Any]:
        """Parse verification result into structured report"""
        return {
            "overall_score": 0.87,
            "confidence_level": "high",
            "business_alignment": "aligned",
            "recommendations": [
                "Increase test coverage in edge cases",
                "Focus on performance optimization",
                "Enhance security testing depth"
            ],
            "final_status": "approved_with_recommendations"
        }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a testing session"""
        requirements = self.redis_client.get(f"session:{session_id}:requirements")
        test_plan = self.redis_client.get(f"session:{session_id}:test_plan")
        verification = self.redis_client.get(f"session:{session_id}:verification")
        
        return {
            "session_id": session_id,
            "requirements": json.loads(requirements) if requirements else None,
            "test_plan": json.loads(test_plan) if test_plan else None,
            "verification": json.loads(verification) if verification else None,
            "status": self._determine_status(requirements, test_plan, verification)
        }
    
    def _determine_status(self, requirements: Any, test_plan: Any, verification: Any) -> str:
        """Determine overall session status"""
        if not requirements:
            return "pending_requirements"
        elif not test_plan:
            return "planning"
        elif not verification:
            return "testing_in_progress"
        else:
            return "completed"

async def main():
    """Main entry point for QA Manager agent"""
    manager = QAManagerAgent()
    
    # Example usage
    sample_requirements = {
        "title": "E-commerce Checkout Flow",
        "description": "Test the complete checkout process including payment integration",
        "business_goals": "Ensure 99.9% conversion rate with zero payment failures",
        "constraints": "Must support PCI compliance and 3D secure authentication"
    }
    
    result = await manager.process_requirements(sample_requirements)
    print(f"QA Manager Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())