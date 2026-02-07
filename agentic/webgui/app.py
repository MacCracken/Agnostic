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
from chainlit.types import ThreadDict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to Python path
sys.path.append('/app')

class AgenticQAGUI:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
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
async def on_chat_start():
    """Initialize chat session"""
    await cl.Message(
        content="🤖 Welcome to the Agentic QA Team System!\n\n"
        "I'm your interface to a team of AI-powered QA agents:\n"
        "• **QA Manager**: Orchestrates test planning and verification\n"
        "• **Senior QA Engineer**: Handles complex testing and self-healing\n"
        "• **Junior QA Worker**: Executes regression tests and data generation\n\n"
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
async def on_message(message: cl.Message):
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
    
    else:
        # General help message
        await cl.Message(
            content="💡 **Available Commands:**\n\n"
            "• **Describe your testing requirements** - Start a new test plan\n"
            "• **'status'** - Check current session status\n"
            "• **'trace'** - View reasoning trace and agent collaboration\n"
            "• **'help'** - Show this help message\n\n"
            "You can also upload a PR or feature document to get started!"
        ).send()

@cl.on_file_upload
async def on_file_upload(files: List[cl.File]):
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
async def on_chat_end():
    """Clean up when chat ends"""
    session_id = cl.user_session.get("session_id")
    if session_id:
        logger.info(f"Ending session: {session_id}")

# Health check endpoint
app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # Run Chainlit with FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)