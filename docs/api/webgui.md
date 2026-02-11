# WebGUI API Reference

## Overview

The WebGUI provides a Chainlit-based interface for human-in-the-loop interaction with the QA agent system.

## Base Configuration
- **URL**: `http://localhost:8000`
- **Framework**: Chainlit 1.1.304 + FastAPI
- **Authentication**: Session-based with Redis storage

## REST API Endpoints

### Session Management
```http
POST /api/session/create
GET  /api/session/{session_id}
DELETE /api/session/{session_id}
```

### Agent Operations
```http
GET  /api/agents/status           # Agent health status
GET  /api/agents/{agent_name}      # Specific agent info
POST /api/agents/{agent_name}/task # Submit task to agent
```

### Task Management
```http
POST /api/tasks                    # Create new task
GET  /api/tasks/{task_id}          # Get task details
GET  /api/tasks                    # List all tasks
PUT  /api/tasks/{task_id}/status   # Update task status
```

### File Operations
```http
POST /api/files/upload            # Upload test files
GET  /api/files/{file_id}         # Download file
GET  /api/files                    # List uploaded files
```

## WebSocket Events

### Real-time Communication
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Listen for task updates
ws.on('task_update', (data) => {
    console.log('Task status:', data);
});

// Listen for agent status
ws.on('agent_status', (data) => {
    console.log('Agent health:', data);
});
```

### Event Types
- `task_created` - New task submitted
- `task_updated` - Task status changed
- `agent_status` - Agent health update
- `message` - General notifications
- `reasoning_trace` - LLM reasoning steps

## Request/Response Formats

### Task Submission
```json
{
    "session_id": "uuid-string",
    "agent": "qa_manager",
    "tool": "TestPlanDecompositionTool", 
    "parameters": {
        "requirements": "User registration flow",
        "context": {"app_type": "web"}
    },
    "priority": "high"
}
```

### Task Response
```json
{
    "task_id": "uuid-string",
    "status": "completed",
    "result": {
        "test_plan": [...],
        "scenarios": [...],
        "confidence": 0.95
    },
    "reasoning_trace": [
        {"step": "analyze_requirements", "output": "..."},
        {"step": "generate_scenarios", "output": "..."}
    ],
    "execution_time": 2.3,
    "agent": "qa_manager"
}
```

### Agent Status
```json
{
    "agents": {
        "qa_manager": {
            "status": "active",
            "last_heartbeat": "2026-02-10T23:30:00Z",
            "current_tasks": 2,
            "memory_usage": "125MB"
        },
        "qa_analyst": {
            "status": "idle", 
            "last_heartbeat": "2026-02-10T23:29:45Z",
            "current_tasks": 0,
            "memory_usage": "98MB"
        }
    }
}
```

## File Upload Support

### Supported Formats
- **Test Plans**: JSON, YAML
- **Test Data**: CSV, JSON, XML
- **Screenshots**: PNG, JPG (for visual testing)
- **Logs**: TXT, LOG

### Upload Process
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('type', 'test_data');
formData.append('session_id', sessionId);

fetch('/api/files/upload', {
    method: 'POST',
    body: formData
}).then(response => response.json());
```

## Authentication & Sessions

### Session Creation
```http
POST /api/session/create
{
    "user_agent": "Mozilla/5.0...",
    "preferences": {
        "theme": "dark",
        "notifications": true
    }
}
```

### Session Response
```json
{
    "session_id": "uuid-string",
    "expires_at": "2026-02-11T01:30:00Z",
    "csrf_token": "random-string"
}
```

## Error Handling

### Error Response Format
```json
{
    "error": {
        "code": "AGENT_UNAVAILABLE",
        "message": "QA Manager agent is not responding",
        "details": {
            "agent": "qa_manager",
            "last_seen": "2026-02-10T23:25:00Z"
        }
    },
    "request_id": "uuid-string"
}
```

### Common Error Codes
- `AGENT_UNAVAILABLE` - Agent not responding
- `INVALID_PARAMETERS` - Malformed request
- `SESSION_EXPIRED` - Authentication required
- `FILE_TOO_LARGE` - Upload size exceeded
- `RATE_LIMITED` - Too many requests

## Rate Limiting

### Limits
- **Tasks**: 10 per minute per session
- **File Upload**: 5 per minute per session  
- **API Calls**: 100 per minute per IP

### Headers
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1644527400
```

## Integration Examples

### JavaScript Client
```javascript
class QAClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.sessionId = null;
    }
    
    async createSession() {
        const response = await fetch(`${this.baseUrl}/api/session/create`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        this.sessionId = response.session_id;
        return response;
    }
    
    async submitTask(agent, tool, parameters) {
        return await fetch(`${this.baseUrl}/api/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': this.sessionId
            },
            body: JSON.stringify({agent, tool, parameters})
        });
    }
}
```

### Python Client
```python
import requests
import websocket

class WebGUIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        
    def create_session(self):
        response = requests.post(f"{self.base_url}/api/session/create")
        self.session_id = response.json()["session_id"]
        return self.session_id
        
    def submit_task(self, agent: str, tool: str, parameters: dict):
        headers = {"X-Session-ID": self.session_id}
        data = {"agent": agent, "tool": tool, "parameters": parameters}
        response = requests.post(f"{self.base_url}/api/tasks", 
                               json=data, headers=headers)
        return response.json()
```