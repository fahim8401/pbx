# HPLink PBX Cloud

A production-ready, multi-tenant Cloud PBX platform built with Python (PJSIP), FastAPI, PostgreSQL, Next.js, and WHMCS integration.

## Features

- **Multi-Tenant Architecture**: Fully isolated tenants with customizable limits and plan templates
- **Python PBX Core**: Built on PJSIP (pjsua2) with support for UDP, TCP, TLS, and WebSocket (WSS) transports
- **RESTful API**: FastAPI backend with HMAC authentication for WHMCS integration
- **Modern Portals**: Admin and Client web portals built with Next.js, React, TailwindCSS, and shadcn/ui
- **WebRTC Softphone**: Browser-based softphone using SIP.js over WSS
- **IVR System**: Flexible IVR with DTMF handling, nested menus, and depth limits
- **Call Recording**: Configurable recording policies (none/external/all)
- **Usage Billing**: Integrated with WHMCS for usage metrics and overage billing
- **Plan Templates**: Reusable configuration templates with enforced limits
- **WHMCS Integration**: Full server module for automated provisioning and billing

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   WHMCS Server  │────▶│  FastAPI Server  │────▶│  PostgreSQL DB  │
│     Module      │     │  (HMAC Auth)     │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  PBX Core Engine │
                        │   (PJSIP/Python) │
                        └──────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
            ┌───────▼────────┐      ┌──────▼────────┐
            │  Admin Portal  │      │ Client Portal │
            │   (Next.js)    │      │  (Next.js +   │
            └────────────────┘      │    SIP.js)    │
                                    └───────────────┘
```

## Technology Stack

### Backend
- **PBX Engine**: Python 3.11 + PJSIP (pjsua2 bindings)
- **API**: FastAPI + SQLAlchemy + Alembic + Pydantic
- **Database**: PostgreSQL
- **Authentication**: 
  - HMAC-SHA256 for WHMCS integration
  - JWT for portal users

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI Library**: React 18
- **Styling**: TailwindCSS + shadcn/ui components
- **Icons**: Lucide React
- **State Management**: React Query (TanStack) + Zustand
- **WebRTC**: SIP.js over WSS

### Deployment
- **Process Manager**: systemd
- **Reverse Proxy**: NGINX or Caddy
- **Containerization**: Docker (optional)

## Quick Start

See the detailed [Installation Guide](#installation) below for complete setup instructions.

```bash
# 1. Clone repository
git clone https://github.com/fahim8401/pbx.git
cd pbx

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Install dependencies
# See Installation section for detailed steps

# 4. Run database migrations
cd api-server
alembic upgrade head

# 5. Start services
systemctl start hplink-api hplink-core
```

## Installation

See full installation guide in the sections below.

## API Documentation

Once running, API documentation is available at:
- Swagger UI: `https://api.hplinkpbx.com/docs`
- ReDoc: `https://api.hplinkpbx.com/redoc`

## Contributing

This is a proprietary project. For support, contact the development team.

## License

Proprietary - All rights reserved