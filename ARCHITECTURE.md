# HPLink PBX Cloud - Architecture Documentation

## Overview

HPLink PBX Cloud is a production-ready, multi-tenant Cloud PBX platform designed for WHMCS integration. The system provides automated provisioning, usage billing, and comprehensive PBX features including IVR, call recording, and WebRTC support.

## Architecture Principles

### 1. Multi-Tenancy
- Complete tenant isolation at database level
- Per-tenant resource limits enforced by Plan Templates
- Tenant-specific routing, IVR, and recordings

### 2. Security-First Design
- HMAC-SHA256 authentication for API access
- JWT tokens for portal users
- TLS/WSS for SIP signaling
- Password hashing with bcrypt
- Clock skew validation for replay attack prevention

### 3. Scalability
- Stateless API design
- Horizontal scaling support
- Connection pooling
- Async/await patterns
- WebSocket for real-time updates

### 4. Reliability
- Systemd service management
- Database-backed configuration
- Graceful degradation
- Comprehensive error handling and logging

## Component Architecture

### Core PBX Engine (Python + PJSIP)

**Responsibilities:**
- SIP call processing
- Media handling (RTP)
- Extension authentication
- Trunk management
- IVR execution
- Call recording
- Event publishing

**Key Modules:**
- `engine.py`: PJSIP endpoint initialization, transport management
- `auth_store.py`: Extension credential caching with lockout protection
- `trunks.py`: Trunk registration, priority-based routing
- `routing.py`: DID-to-destination and prefix-to-trunk routing
- `calls.py`: Call lifecycle, transfer, hold operations
- `ivr.py`: DTMF handling, nested menu support, depth limits
- `media.py`: Playback, MOH, recording, voicemail
- `events.py`: Event publishing to API/WebSocket
- `security.py`: Rate limiting, concurrency caps, fraud detection

**Design Decisions:**
- Cached authentication reduces API calls (5-minute TTL)
- Failed login attempts trigger temporary lockouts
- Priority-based trunk selection with failover
- Configurable transport support (UDP/TCP/TLS/WSS)

### API Server (FastAPI + PostgreSQL)

**Responsibilities:**
- Tenant provisioning and management
- Plan template configuration
- DID allocation and routing
- CDR storage and retrieval
- Usage metrics calculation
- WHMCS integration via HMAC

**Database Schema:**
- `tenants`: Core tenant data with status and limits
- `plan_templates`: Reusable configuration profiles
- `extensions`: SIP credentials per tenant
- `dids`: Phone number inventory and assignment
- `trunks`: Outbound carrier configurations
- `cdr`: Call Detail Records
- `recordings`: Recording metadata
- `ivr_trees`: IVR menu configurations
- `usage_snapshots`: Aggregated usage metrics
- `api_users`: HMAC authentication credentials
- `portal_users`: Portal login credentials

**API Design:**
- RESTful endpoints with clear resource hierarchy
- HMAC authentication for machine-to-machine
- JWT authentication for human users
- Pydantic schemas for validation
- Alembic for schema migrations

### WHMCS Module (PHP)

**Responsibilities:**
- Automated tenant provisioning
- Service suspension/resumption
- Package changes
- Usage billing integration
- Admin service display

**Key Features:**
- HMAC request signing
- Secure credential storage
- Usage metrics polling (cron)
- Module-specific database table for tenant mapping

**Security Considerations:**
- HMAC secret rotation support
- IP whitelist capability (via NGINX)
- Secure password generation
- Credential masking in logs

### WebSocket Service

**Responsibilities:**
- Real-time call event broadcasting
- Active call monitoring
- System statistics streaming

**Implementation:**
- FastAPI WebSocket endpoints
- Connection pooling
- Pub/sub pattern for event distribution
- Tenant-specific subscriptions

## Data Flow

### Tenant Provisioning Flow

```
WHMCS → API (HMAC) → Database → Response
  ↓
Portal User Creation
  ↓
Initial Configuration
```

1. WHMCS calls `/api/v1/tenants` with HMAC signature
2. API validates signature and clock skew
3. Tenant created with plan template limits
4. Portal admin user created with random password
5. Credentials returned to WHMCS
6. WHMCS stores mapping in custom table

### Call Flow (Inbound)

```
Carrier → PBX Core → Auth Check → Routing → IVR/Extension
                        ↓
                   Event → API → CDR
```

1. SIP INVITE received on transport
2. DID lookup in routing table
3. Route to target (IVR, extension, queue)
4. Execute IVR if configured
5. Bridge call to destination
6. Record if policy enabled
7. On hangup, create CDR entry
8. Send metrics to API

### Call Flow (Outbound)

```
Extension → PBX Core → Auth → Permission Check → Trunk → Carrier
                                    ↓
                               Prefix Match
                                    ↓
                            Concurrency Check
```

1. Extension authenticates (cached or API)
2. Check tenant call direction permission
3. Verify destination against allowed/blocked prefixes
4. Check concurrency limit
5. Select trunk by priority
6. Send INVITE to trunk
7. Record and log as configured

### Usage Billing Flow

```
WHMCS Cron → API → Calculate Metrics → Return
                ↓
         Update WHMCS Usage
```

1. WHMCS cron calls `/api/v1/usage/metrics`
2. API aggregates CDR billsec by direction
3. Calculate storage from recordings
4. Return metrics object
5. WHMCS updates usage billing
6. Invoice generated for overages

## Plan Templates

Plan templates are reusable configuration profiles that define tenant limits and capabilities.

### Structure

```json
{
  "limits_json": {
    "extensions_limit": 10,
    "did_limit": 2,
    "concurrency": 5,
    "recording_rule": "external",
    "queue_seats": 3,
    "ivr_depth_max": 5,
    "storage_gb": 5,
    "cdr_visibility": "all",
    "call_direction": "both",
    "billing_mode": "postpaid",
    "allowed_prefixes": ["+1", "+44"],
    "blocked_prefixes": ["+1900"]
  },
  "routing_json": {
    "default_routing": "ivr"
  },
  "propagate_updates": true
}
```

### Enforcement

- `extensions_limit`: Hard limit in database and API
- `did_limit`: Enforced during DID allocation
- `concurrency`: Checked before call establishment
- `recording_rule`: Applied in media handler
- `call_direction`: Validated in routing logic
- `allowed_prefixes`/`blocked_prefixes`: Checked on outbound calls
- `ivr_depth_max`: Enforced in IVR session

### Propagation

When `propagate_updates` is `true`:
- Changes to template automatically update all using tenants
- Useful for policy enforcement
- Can be overridden per tenant if needed

## IVR System Design

### Node Structure

```python
{
  "node_id": "root",
  "welcome_prompt": "welcome.wav",
  "invalid_prompt": "invalid.wav",
  "timeout_seconds": 5,
  "max_retries": 3,
  "options": {
    "0": {"action": "extension", "value": "101"},
    "1": {"action": "repeat"},
    "2": {"action": "submenu", "value": "child_node_id"}
  }
}
```

### Supported Actions

- `extension`: Transfer to extension
- `queue`: Transfer to queue
- `ring_group`: Ring multiple extensions
- `submenu`: Navigate to child menu
- `voicemail`: Send to voicemail
- `repeat`: Replay current menu

### Features

- DTMF collection with timeout
- Invalid input handling with retries
- Nested menus with depth limits
- Support for multiple languages (file naming)

## Security Hardening

### HMAC Authentication

1. Request components: `USER|METHOD|PATH|TIMESTAMP|BODY_HASH`
2. Signature: `HMAC-SHA256(SECRET, message)`
3. Headers: `X-PBX-API-USER`, `X-PBX-TIMESTAMP`, `X-PBX-SIGNATURE`
4. Validation: Clock skew ≤ 300 seconds
5. Protection: Replay attack prevention

### Rate Limiting

- Per-IP request limiting
- Failed auth attempt tracking
- Temporary lockouts (15 minutes after 5 failures)
- Configurable thresholds

### Network Security

- TLS for all web traffic
- WSS for WebRTC signaling
- SRTP for media encryption
- Firewall rules for SIP ports
- Optional IP whitelisting

### Data Protection

- Password hashing with bcrypt
- Sensitive data masking in logs
- Secure random password generation
- Database encryption at rest (PostgreSQL)

## Performance Considerations

### Database

- Indexed columns: username, e164, email, timestamps
- Connection pooling (SQLAlchemy)
- Query optimization with eager loading
- Partitioning for CDR table (future)

### Caching

- Extension auth cache (5-minute TTL)
- Plan template in-memory cache
- Redis for distributed caching (optional)

### Concurrency

- Async/await in FastAPI
- Multiple uvicorn workers
- WebSocket connection pooling
- Non-blocking I/O in PBX core

### Media

- RTP proxy for NAT traversal
- G.711 codec for compatibility
- Opus for WebRTC
- Recording compression

## Monitoring and Operations

### Logging

- Structured logging with levels
- systemd journal integration
- Module-specific log namespaces
- Sensitive data redaction

### Metrics

- Active call count (global and per-tenant)
- Concurrent calls vs. limits
- Failed auth attempts
- API request rates
- Database query performance

### Health Checks

- `/health` endpoint
- Database connectivity
- PBX core status
- Trunk registration status

### Alerting (Future)

- Email notifications
- Webhook integration
- Prometheus metrics export
- Grafana dashboards

## Deployment Topology

### Recommended Setup (Production)

```
┌──────────────────────────────────────────────────┐
│                   Internet                        │
└───────────────────┬──────────────────────────────┘
                    │
         ┌──────────▼──────────┐
         │  Reverse Proxy      │
         │  (NGINX/Caddy)      │
         │  - TLS Termination  │
         │  - Load Balancing   │
         └──────────┬──────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
   ┌────▼────┐ ┌───▼────┐ ┌───▼─────┐
   │ API x2  │ │PBX Core│ │WebSocket│
   │ (8000)  │ │ (5060) │ │  (8001) │
   └────┬────┘ └───┬────┘ └────┬────┘
        │          │           │
        └──────────┼───────────┘
                   │
            ┌──────▼──────┐
            │  PostgreSQL │
            │   + Backup  │
            └─────────────┘
```

### Scaling Strategy

- Horizontal: Add more API workers
- Vertical: Increase database resources
- Geographic: Multi-region deployments
- Caching: Redis for hot data

## Future Enhancements

### Phase 2
- Admin and Client portals (Next.js)
- Advanced IVR editor UI
- Call queuing system
- Ring groups
- Call analytics dashboard

### Phase 3
- SMS/MMS support
- Voicemail transcription
- AI-powered features (sentiment, transcription)
- Advanced fraud detection
- Geographic redundancy

### Phase 4
- Video calling support
- Team collaboration features
- CRM integrations
- Advanced reporting
- White-label capabilities

## Troubleshooting Guide

### Common Issues

1. **PBX won't start**: Check PJSIP installation, port availability
2. **API 401 errors**: Verify HMAC secret matches, check clock sync
3. **No audio**: Check firewall rules for RTP ports, verify codec support
4. **Database errors**: Check connection string, permissions
5. **WHMCS provisioning fails**: Verify API connectivity, check HMAC signature

### Debug Mode

Enable detailed logging:
```bash
# In .env
PBX_LOG_LEVEL=DEBUG
```

View real-time logs:
```bash
sudo journalctl -u hplink-api -f
sudo journalctl -u hplink-core -f
```

## Conclusion

HPLink PBX Cloud provides a comprehensive, production-ready platform for multi-tenant VoIP services. The architecture prioritizes security, scalability, and ease of integration with WHMCS for automated provisioning and billing.
