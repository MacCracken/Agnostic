# ADR-005: Authentication and Authorization Design

## Status
Accepted

## Context
The WebGUI requires a comprehensive authentication and authorization system to support:
1. Multi-tenant team environments
2. Role-based access control for different user types
3. Integration with enterprise SSO systems
4. Audit trails and compliance requirements
5. API access for external integrations
6. Session security and data isolation

The system needs to balance security requirements with usability for both internal teams and external stakeholders.

## Decision
We selected a **JWT-Based Multi-Provider Authentication Architecture**:

- **OAuth2/OIDC** - Enterprise SSO integration (Google, Azure AD, GitHub)
- **JWT Tokens** - Stateless authentication with refresh tokens
- **Role-Based Access Control (RBAC)** - Fine-grained permissions
- **Multi-tenant Isolation** - Team-based data separation
- **Audit Logging** - Comprehensive action tracking

## Consequences

### Positive
- **Enterprise Ready**: Supports common SSO providers
- **Scalable**: Stateless tokens scale horizontally
- **Flexible**: Multiple auth providers and custom providers
- **Secure**: Industry best practices for token management
- **Compliant**: Audit trails meet regulatory requirements
- **User-Friendly**: Single sign-on reduces friction

### Negative
- **Complexity**: Multiple auth flows increase system complexity
- **Token Management**: Need secure token refresh and revocation
- **Integration**: Requires coordination with IT departments
- **Performance**: Additional validation overhead on each request

## Rationale

### Evaluation of Alternatives

1. **Session-Based Authentication**
   - Pros: Simple to implement, server-controlled
   - Cons: Doesn't scale well, requires sticky sessions
   
2. **API Keys Only**
   - Pros: Simple, good for machine-to-machine
   - Cons: No user context, limited for interactive use
   
3. **Third-Party Auth Service**
   - Pros: Offloads complexity, professional features
   - Cons: Cost, vendor lock-in, data privacy concerns
   
4. **JWT Multi-Provider Architecture** (Selected)
   - Pros: Standards-based, scalable, flexible, enterprise-ready
   - Cons: More complex implementation

### Authentication Flow

```
User → Login Page → OAuth2 Provider → JWT Token → WebGUI
                                   ↓
                              Refresh Token
                                   ↓
                             API Access
```

### Role Hierarchy

**Roles:**
1. **Super Admin** - System-wide configuration, user management
2. **Org Admin** - Organization settings, team management, billing
3. **Team Lead** - Test plan creation, session management, team reports
4. **QA Engineer** - Test execution, basic reporting, agent interaction
5. **Viewer** - Read-only access to reports and dashboards
6. **API User** - Machine-to-machine access with scoped permissions

**Permissions:**
- `sessions:read` - View sessions and results
- `sessions:write` - Create and modify sessions
- `sessions:delete` - Remove sessions and data
- `agents:control` - Start/stop/configure agents
- `reports:generate` - Create and download reports
- `reports:export` - Export data in various formats
- `users:manage` - User and role management
- `system:configure` - System configuration and settings

### Multi-tenant Architecture

**Data Isolation:**
- Namespace-based data separation
- Team-aware Redis keys and database schemas
- File system isolation with per-team directories
- Audit trails track cross-tenant access attempts

**Organization Structure:**
```
Organization
├── Team Alpha
│   ├── Project A
│   └── Project B
└── Team Beta
    ├── Project C
    └── Project D
```

### Security Features

**Token Management:**
- Short-lived access tokens (15 minutes)
- Long-lived refresh tokens (7 days)
- Secure token storage (httpOnly cookies)
- Token revocation on logout and password changes

**Session Security:**
- CSRF protection with SameSite cookies
- Content Security Policy (CSP) headers
- Secure and HttpOnly cookie flags
- Automatic session timeout

**Audit Trail:**
- All user actions logged with timestamps
- Failed login attempts tracked
- Permission changes recorded
- Data access patterns monitored

## Implementation Notes

Key components:

1. **Auth Manager** (`webgui/auth/manager.py`)
   - OAuth2 provider integration
   - Token validation and refresh
   - User session management

2. **Permission Engine** (`webgui/auth/permissions.py`)
   - RBAC policy evaluation
   - Resource-based access control
   - Dynamic permission checking

3. **Middleware** (`webgui/auth/middleware.py`)
   - Request authentication
   - Permission validation
   - Audit logging

4. **User Management** (`webgui/auth/users.py`)
   - User profile management
   - Team and role assignment
   - SSO user provisioning

The architecture supports gradual rollout, starting with basic authentication and progressively adding enterprise features based on customer requirements.