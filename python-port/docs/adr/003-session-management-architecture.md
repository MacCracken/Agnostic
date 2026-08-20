# ADR-003: Session Management Architecture

## Status
Accepted

## Context
The WebGUI needs to manage testing sessions that can span hours to days, with:
1. Multiple concurrent users and sessions
2. Complex agent coordination and delegation
3. File uploads and large data transfers
4. Real-time progress tracking
5. Historical data access and comparison
6. Resource utilization monitoring

The existing system has basic session handling but needs enhancement for multi-user, long-running scenarios.

## Decision
We selected a **Hybrid Session Architecture** combining:

- **Redis** - Active session state and real-time data
- **File-based Persistence** - Session snapshots and large objects
- **Metadata Database** - Session catalog and search indices
- **Session Tiering** - Active, recent, and archival storage tiers

## Consequences

### Positive
- **Performance**: Fast access to active session data via Redis
- **Scalability**: Can handle thousands of concurrent sessions
- **Persistence**: Session data survives restarts and failures
- **Search Capability**: Fast metadata-based session discovery
- **Cost Efficiency**: Hot/cold data separation optimizes storage costs
- **Recovery**: Session snapshots enable crash recovery

### Negative
- **Complexity**: Multiple storage systems increase complexity
- **Consistency**: Need to keep Redis and persistent storage synchronized
- **Memory Usage**: Active sessions consume Redis memory
- **Data Migration**: Need processes for tiering archival data

## Rationale

### Evaluation of Alternatives

1. **Pure Redis Session Storage**
   - Pros: Simple, fast, single system
   - Cons: Memory intensive, no long-term persistence, limited search
   
2. **Relational Database (PostgreSQL)**
   - Pros: ACID compliance, strong querying, mature
   - Cons: Slower for real-time data, overhead for frequent updates
   
3. **Document Database (MongoDB)**
   - Pros: Flexible schema, good for session data
   - Cons: Still requires caching layer for performance
   
4. **Hybrid Architecture** (Selected)
   - Pros: Optimizes for each use case, scalable, performant
   - Cons: More complex, requires synchronization

### Session Lifecycle

1. **Creation**: Session metadata stored in database, active state in Redis
2. **Active Phase**: Real-time updates in Redis, periodic snapshots to disk
3. **Completion**: Final state persisted, Redis cleanup
4. **Archival**: Session moved to cold storage after retention period

### Storage Tiers

**Tier 1: Active Sessions (Redis)**
- Session state, agent status, real-time metrics
- TTL-based eviction for abandoned sessions
- Pub/Sub channels for live updates

**Tier 2: Recent Sessions (File System + Database)**
- Completed sessions within last 30 days
- JSON snapshots with metadata indices
- Fast recovery and comparison capabilities

**Tier 3: Archive Sessions (Object Storage)**
- Sessions older than 30 days
- Compressed format with metadata extraction
- Available for historical analysis and compliance

### Data Model

```json
{
  "session_id": "sess_123",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T14:30:00Z",
  "user_id": "user_456",
  "status": "completed",
  "metadata": {
    "test_plan": "ecommerce_regression",
    "environment": "staging",
    "agent_count": 5,
    "duration_minutes": 150
  },
  "storage": {
    "active": true,
    "snapshot_path": "/sessions/sess_123.json",
    "archive_path": null
  }
}
```

## Implementation Notes

Key components:

1. **Session Manager** (`webgui/session_manager.py`)
   - Session lifecycle management
   - Storage tier coordination
   - Cleanup and archival processes

2. **Session Store** (`webgui/session_store.py`)
   - Redis operations for active sessions
   - File I/O for snapshots
   - Database operations for metadata

3. **Session API** (`webgui/api/sessions.py`)
   - REST endpoints for session CRUD
   - Search and filter capabilities
   - Export and comparison functions

The architecture supports horizontal scaling with Redis Cluster and distributed file storage for cloud deployments.