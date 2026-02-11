#!/usr/bin/env python3
"""
Script to demonstrate the LLM integration updates for tools.
This script shows the transformation from static data to real LLM-driven analysis.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.llm_integration import llm_service

async def demonstrate_llm_integration():
    """Demonstrate LLM integration capabilities."""
    
    print("🤖 LLM Integration Demonstration")
    print("=" * 50)
    
    # Test 1: Scenario Generation
    print("\n1. Test Scenario Generation")
    requirements = "Build a user authentication system with MFA support"
    
    try:
        scenarios = await llm_service.generate_test_scenarios(requirements)
        print(f"✅ Generated {len(scenarios)} scenarios:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"   {i}. {scenario}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Risk Identification
    print("\n2. Test Risk Identification")
    
    try:
        risks = await llm_service.identify_test_risks(requirements)
        print(f"✅ Identified {len(risks)} risks:")
        for i, risk in enumerate(risks, 1):
            print(f"   {i}. {risk}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: Fuzzy Verification
    print("\n3. Test Fuzzy Verification")
    test_results = {
        "total_tests": 100,
        "passed": 85,
        "failed": 15,
        "coverage": 78.5
    }
    business_goals = "Ensure secure and reliable user authentication"
    
    try:
        verification = await llm_service.perform_fuzzy_verification(test_results, business_goals)
        print("✅ LLM-based verification:")
        print(f"   Overall Score: {verification.get('overall_score', 0)}")
        print(f"   Confidence: {verification.get('confidence_level', 'unknown')}")
        print(f"   Business Alignment: {verification.get('business_alignment', 'unknown')}")
        print(f"   Recommendations: {len(verification.get('recommendations', []))}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 4: Security Analysis
    print("\n4. Test Security Analysis")
    scan_results = {
        "target_url": "https://example.com",
        "security_headers": {"missing": ["X-Frame-Options"]},
        "tls_configuration": {"issues": []},
        "vulnerabilities": [
            {"type": "SQL Injection", "severity": "high"},
            {"type": "XSS", "severity": "medium"}
        ]
    }
    
    try:
        analysis = await llm_service.analyze_security_findings(scan_results)
        print("✅ LLM-based security analysis:")
        print(f"   Risk Level: {analysis.get('risk_level', 'unknown')}")
        print(f"   Business Impact: {analysis.get('business_impact', 'unknown')}")
        print(f"   Remediation Items: {len(analysis.get('remediation_priority', []))}")
        print(f"   Executive Summary: {analysis.get('executive_summary', 'No summary')}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 5: Performance Profiling
    print("\n5. Test Performance Profiling")
    performance_data = {
        "endpoints": ["/api/auth", "/api/users"],
        "avg_response_time": 1.8,
        "95th_percentile": 3.2,
        "error_rate": 0.02,
        "throughput": 450
    }
    
    try:
        profile = await llm_service.generate_performance_profile(performance_data)
        print("✅ LLM-based performance profiling:")
        print(f"   Performance Grade: {profile.get('performance_grade', 'unknown')}")
        print(f"   Bottlenecks: {profile.get('bottlenecks', [])}")
        print(f"   Optimization Recommendations: {len(profile.get('optimization_recommendations', []))}")
        print(f"   SLA Impact: {profile.get('sla_impact', 'unknown')}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 LLM Integration Demo Complete!")
    print("\nKey Benefits:")
    print("✅ Real-time, intelligent test scenario generation")
    print("✅ Context-aware risk identification")
    print("✅ Business-aligned verification scoring")
    print("✅ Expert-level security analysis")
    print("✅ Performance bottleneck detection")
    print("✅ Fallback to safe defaults when LLM unavailable")


if __name__ == "__main__":
    asyncio.run(demonstrate_llm_integration())