#!/usr/bin/env python3
"""
Demo script for the Agentic QA Team System
This script demonstrates how to use the system programmatically
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from agents.manager.qa_manager import QAManagerAgent
from agents.senior.senior_qa import SeniorQAAgent
from agents.junior.junior_qa import JuniorQAAgent
from webgui.app import AgenticQAGUI

class AgenticQADemo:
    """Demo class for showcasing the Agentic QA Team System"""
    
    def __init__(self):
        self.manager = QAManagerAgent()
        self.senior_agent = SeniorQAAgent()
        self.junior_agent = JuniorQAAgent()
        self.gui = AgenticQAGUI()
        
    async def run_ecommerce_demo(self):
        """Run the e-commerce checkout testing demo"""
        print("🚀 Starting Agentic QA Team Demo")
        print("=" * 60)
        
        # Load demo requirements
        demo_file = Path(__file__).parent / "ecommerce_checkout_testing.json"
        with open(demo_file, 'r') as f:
            demo_requirements = json.load(f)
        
        print(f"📋 Demo: {demo_requirements['title']}")
        print(f"📝 Description: {demo_requirements['description']}")
        print(f"🎯 Business Goals: {demo_requirements['business_goals']}")
        print()
        
        # Step 1: Process requirements through QA Manager
        print("👔 Step 1: QA Manager Processing Requirements")
        print("-" * 50)
        
        manager_result = await self.manager.process_requirements(demo_requirements)
        
        print(f"✅ Session ID: {manager_result['session_id']}")
        print(f"📊 Status: {manager_result['status']}")
        print(f"📋 Test Plan Created: {len(manager_result['test_plan']['scenarios'])} scenarios")
        
        # Display test scenarios
        print("\n🎯 Generated Test Scenarios:")
        for scenario in manager_result['test_plan']['scenarios']:
            priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(scenario['priority'], "⚪")
            agent_emoji = {"senior": "👨‍💼", "junior": "👩‍💼"}.get(scenario['assigned_to'], "🤖")
            print(f"  {priority_emoji} {agent_emoji} {scenario['name']} ({scenario['priority']})")
        
        print(f"\n🔄 Next Steps: {', '.join(manager_result['next_steps'])}")
        print()
        
        # Step 2: Senior QA handles complex scenarios
        print("👨‍💼 Step 2: Senior QA Engineer Handling Complex Scenarios")
        print("-" * 50)
        
        session_id = manager_result['session_id']
        senior_scenarios = [s for s in manager_result['test_plan']['scenarios'] if s['assigned_to'] == 'senior']
        
        for scenario in senior_scenarios[:2]:  # Process first 2 senior scenarios
            print(f"\n🔍 Processing: {scenario['name']}")
            
            task_data = {
                "session_id": session_id,
                "scenario": scenario,
                "timestamp": datetime.now().isoformat()
            }
            
            senior_result = await self.senior_agent.handle_complex_scenario(task_data)
            
            print(f"  ✅ Status: {senior_result['status']}")
            print(f"  📊 Complexity: {senior_result['complexity_assessment']['complexity_level']}")
            
            if senior_result.get('self_healing_analysis'):
                print(f"  🔄 Self-Healing: {senior_result['self_healing_analysis']['confidence_score']:.2f} confidence")
            
            if senior_result.get('model_based_testing'):
                print(f"  📈 MBT Coverage: {senior_result['model_based_testing']['coverage_potential']:.2f}")
            
            if senior_result.get('edge_case_analysis'):
                print(f"  ⚠️  Edge Cases: {senior_result['edge_case_analysis']['risk_score']:.2f} risk score")
        
        print()
        
        # Step 3: Junior QA handles regression testing
        print("👩‍💼 Step 3: Junior QA Worker Executing Regression Tests")
        print("-" * 50)
        
        junior_scenarios = [s for s in manager_result['test_plan']['scenarios'] if s['assigned_to'] == 'junior']
        
        for scenario in junior_scenarios[:2]:  # Process first 2 junior scenarios
            print(f"\n🧪 Testing: {scenario['name']}")
            
            task_data = {
                "session_id": session_id,
                "scenario": scenario,
                "timestamp": datetime.now().isoformat()
            }
            
            junior_result = await self.junior_agent.execute_regression_test(task_data)
            
            test_execution = junior_result['test_execution']
            results = test_execution['results']
            
            print(f"  ✅ Status: {junior_result['status']}")
            print(f"  📊 Tests: {results['passed']} passed, {results['failed']} failed, {results['skipped']} skipped")
            print(f"  ⏱️  Execution Time: {test_execution['execution_time']:.2f}s")
            
            if test_execution.get('regression_detected'):
                print(f"  ⚠️  Regression Detected: Yes")
            else:
                print(f"  ✅ Regression Detected: No")
            
            if test_execution.get('root_cause_analysis'):
                rca = test_execution['root_cause_analysis']
                print(f"  🔍 Root Cause: {rca.get('most_common_cause', 'Unknown')}")
                print(f"  📊 Confidence: {rca.get('confidence_score', 0):.2f}")
        
        print()
        
        # Step 4: Final fuzzy verification
        print("🔮 Step 4: Final Fuzzy Verification")
        print("-" * 50)
        
        # Simulate test results for verification
        test_results = {
            "test_results": [
                {"status": "passed", "type": "functional", "category": "authentication"},
                {"status": "passed", "type": "integration", "category": "payment"},
                {"status": "failed", "type": "ui", "category": "checkout"},
                {"status": "passed", "type": "performance", "category": "load"}
            ],
            "overall_pass_rate": 0.85,
            "test_coverage": 0.92,
            "performance_metrics": {
                "avg_response_time": 850,
                "throughput": 450,
                "error_rate": 0.02
            },
            "visual_regression": {
                "similarity_score": 0.94
            },
            "ux_metrics": {
                "user_satisfaction": 0.88,
                "task_completion_rate": 0.91,
                "avg_task_time": 45
            }
        }
        
        verification_result = await self.manager.perform_fuzzy_verification(
            session_id, test_results
        )
        
        print(f"📊 Overall Score: {verification_result['overall_score']:.2f}/1.00")
        print(f"🎯 Confidence Level: {verification_result['confidence_level']}")
        print(f"📈 Business Alignment: {verification_result['business_alignment']}")
        
        print(f"\n📋 Detailed Scores:")
        for criterion, score in verification_result['detailed_scores'].items():
            criterion_name = criterion.replace('_', ' ').title()
            print(f"  • {criterion_name}: {score:.2f}/1.00")
        
        if verification_result.get('recommendations'):
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(verification_result['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print()
        
        # Step 5: Display reasoning trace
        print("📝 Step 5: Agent Collaboration Trace")
        print("-" * 50)
        
        reasoning_trace = await self.gui.get_reasoning_trace(session_id)
        
        if reasoning_trace:
            print("🔄 Agent Collaboration Timeline:")
            for event in reasoning_trace[-8:]:  # Show last 8 events
                agent_emoji = {"manager": "👔", "senior": "👨‍💼", "junior": "👩‍💼"}.get(event.get('agent'), "🤖")
                timestamp = event.get('timestamp', '')[:19] if event.get('timestamp') else 'Unknown'
                print(f"  {agent_emoji} {event.get('agent', 'Unknown').title()} - {event.get('message', 'No message')}")
                print(f"     _{timestamp}_")
        else:
            print("📝 No reasoning trace available")
        
        print()
        
        # Final summary
        print("🎉 Demo Complete!")
        print("=" * 60)
        print(f"✅ Session: {session_id}")
        print(f"📊 Test Scenarios: {len(manager_result['test_plan']['scenarios'])}")
        print(f"👔 Manager: ✅ Requirements processed")
        print(f"👨‍💼 Senior: ✅ Complex scenarios handled")
        print(f"👩‍💼 Junior: ✅ Regression tests executed")
        print(f"🔮 Verification: {verification_result['overall_score']:.2f} overall score")
        print()
        print("🚀 Ready to start your own Agentic QA Sprint!")
        print("🌐 Access the WebGUI at: http://localhost:8000")

async def main():
    """Main demo execution"""
    try:
        demo = AgenticQADemo()
        await demo.run_ecommerce_demo()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())