# ADR-004: WebGUI Technology and Real-time Communication

## Status
Accepted

## Context
The system needs a web interface for human-in-the-loop interaction, real-time monitoring, and comprehensive reporting capabilities.

## Decision
Use Chainlit + FastAPI for the WebGUI with:

1. **Chainlit** for the primary chat interface and agent interaction
2. **FastAPI** for REST API endpoints and WebSocket support
3. **Redis Pub/Sub + WebSocket** for real-time updates
4. **JWT Authentication** with role-based access control
5. **Hybrid Session Storage** (Redis + File System + Database)

## Rationale
- **Chainlit** provides excellent LLM chat interface capabilities
- **FastAPI** gives us high-performance API and WebSocket support
- **Real-time Updates** essential for monitoring multi-agent workflows
- **Authentication** necessary for enterprise security requirements
- **Hybrid Storage** balances performance, persistence, and searchability

## Consequences
- Complex web architecture but comprehensive feature set
- Requires Redis for both agent communication and WebGUI real-time features
- Multiple storage backends increase operational complexity
- Provides enterprise-ready authentication and authorization

## Implementation
- `webgui/app.py` combines Chainlit chat with FastAPI endpoints
- `webgui/realtime.py` handles WebSocket infrastructure
- `webgui/auth.py` provides JWT-based authentication
- Modular components for dashboard, exports, history, and monitoring
- Session management spanning Redis (active), filesystem (persistence), and database (metadata)