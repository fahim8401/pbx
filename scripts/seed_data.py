#!/usr/bin/env python3
"""
Seed script to populate initial data for HPLink PBX Cloud
Creates example plan templates, API users, and test data
"""
import sys
import os
from uuid import uuid4
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api-server'))

from app.db import SessionLocal
from app.models import (
    PlanTemplate,
    APIUser,
    APIUserRole,
    PortalUser,
    UserRole,
    Tenant,
    TenantStatus,
    BillingMode,
    Extension,
    DID,
    DIDStatus,
    IVRTree,
)
from app.deps import hash_password


def seed_data():
    """Seed initial data"""
    db = SessionLocal()
    
    try:
        print("🌱 Seeding HPLink PBX Cloud data...")
        
        # 1. Create API Users
        print("\n📝 Creating API users...")
        
        # WHMCS API user
        whmcs_user = APIUser(
            id=uuid4(),
            username="whmcs-integration",
            secret_hash="whmcs-secret-change-this",  # In production, hash this
            role=APIUserRole.WHMCS,
            enabled=True,
        )
        db.add(whmcs_user)
        print(f"  ✓ Created WHMCS API user: {whmcs_user.username}")
        
        # PBX Core API user
        pbx_user = APIUser(
            id=uuid4(),
            username="pbx-core",
            secret_hash="pbx-secret-change-this",
            role=APIUserRole.SYSTEM,
            enabled=True,
        )
        db.add(pbx_user)
        print(f"  ✓ Created PBX Core API user: {pbx_user.username}")
        
        # Admin API user
        admin_user = APIUser(
            id=uuid4(),
            username="admin",
            secret_hash="admin-secret-change-this",
            role=APIUserRole.ADMIN,
            enabled=True,
        )
        db.add(admin_user)
        print(f"  ✓ Created Admin API user: {admin_user.username}")
        
        # 2. Create Plan Templates
        print("\n📋 Creating plan templates...")
        
        # Inbound Only - Basic
        inbound_template = PlanTemplate(
            id=uuid4(),
            name="Inbound Only - Basic",
            description="Basic inbound-only plan with IVR support",
            limits_json={
                "extensions_limit": 5,
                "did_limit": 1,
                "concurrency": 3,
                "recording_rule": "none",
                "queue_seats": 0,
                "ivr_depth_max": 3,
                "storage_gb": 1,
                "cdr_visibility": "30d",
                "call_direction": "inbound",
                "billing_mode": "postpaid",
                "allowed_prefixes": [],
                "blocked_prefixes": ["*"],  # Block all outbound
            },
            routing_json={
                "default_routing": "ivr",
            },
            propagate_updates=False,
        )
        db.add(inbound_template)
        print(f"  ✓ Created plan: {inbound_template.name}")
        
        # Local Business
        business_template = PlanTemplate(
            id=uuid4(),
            name="Local Business",
            description="Local and mobile calling with recording",
            limits_json={
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
                "allowed_prefixes": ["+1", "+44"],  # US/UK
                "blocked_prefixes": ["+1900"],  # Premium
            },
            routing_json={
                "default_routing": "extension",
            },
            propagate_updates=True,
        )
        db.add(business_template)
        print(f"  ✓ Created plan: {business_template.name}")
        
        # Call Center Basic
        callcenter_template = PlanTemplate(
            id=uuid4(),
            name="Call Center Basic",
            description="Call center with queue and full recording",
            limits_json={
                "extensions_limit": 20,
                "did_limit": 5,
                "concurrency": 20,
                "recording_rule": "all",
                "queue_seats": 10,
                "ivr_depth_max": 5,
                "storage_gb": 20,
                "cdr_visibility": "all",
                "call_direction": "both",
                "billing_mode": "prepaid",
                "allowed_prefixes": [],  # All allowed
                "blocked_prefixes": [],
            },
            routing_json={
                "default_routing": "queue",
            },
            propagate_updates=True,
        )
        db.add(callcenter_template)
        print(f"  ✓ Created plan: {callcenter_template.name}")
        
        db.commit()
        
        # 3. Create Sample Tenant
        print("\n🏢 Creating sample tenant...")
        
        sample_tenant = Tenant(
            id=uuid4(),
            name="Demo Company",
            domain="demo",
            status=TenantStatus.ACTIVE,
            plan_template_id=business_template.id,
            limits_json=business_template.limits_json,
            billing_mode=BillingMode.POSTPAID,
        )
        db.add(sample_tenant)
        db.commit()
        print(f"  ✓ Created tenant: {sample_tenant.name} (domain: {sample_tenant.domain})")
        
        # 4. Create Portal Admin User for Sample Tenant
        print("\n👤 Creating portal users...")
        
        portal_admin = PortalUser(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            email="admin@demo.com",
            pass_hash=hash_password("demo123"),
            role=UserRole.TENANT_ADMIN,
        )
        db.add(portal_admin)
        print(f"  ✓ Created portal admin: {portal_admin.email} (password: demo123)")
        
        # 5. Create Sample Extensions
        print("\n📞 Creating sample extensions...")
        
        extensions = [
            Extension(
                id=uuid4(),
                tenant_id=sample_tenant.id,
                username="101",
                secret_hash=hash_password("ext101pass"),
                webrtc=True,
                voicemail_email="user101@demo.com",
            ),
            Extension(
                id=uuid4(),
                tenant_id=sample_tenant.id,
                username="102",
                secret_hash=hash_password("ext102pass"),
                webrtc=True,
                voicemail_email="user102@demo.com",
            ),
        ]
        
        for ext in extensions:
            db.add(ext)
            print(f"  ✓ Created extension: {ext.username}")
        
        # 6. Create Sample DIDs
        print("\n📱 Creating sample DIDs...")
        
        did1 = DID(
            id=uuid4(),
            e164="+14155551234",
            tenant_id=sample_tenant.id,
            status=DIDStatus.ASSIGNED,
            routing_json={"target_type": "ivr", "target_value": "main-menu"},
        )
        db.add(did1)
        print(f"  ✓ Created DID: {did1.e164} (assigned to {sample_tenant.name})")
        
        did2 = DID(
            id=uuid4(),
            e164="+14155555678",
            tenant_id=None,
            status=DIDStatus.FREE,
        )
        db.add(did2)
        print(f"  ✓ Created DID: {did2.e164} (free)")
        
        # 7. Create Sample IVR
        print("\n🎵 Creating sample IVR...")
        
        ivr_tree = IVRTree(
            id=uuid4(),
            tenant_id=sample_tenant.id,
            name="Main Menu",
            json={
                "tree_id": str(uuid4()),
                "tenant_id": str(sample_tenant.id),
                "name": "Main Menu",
                "root": {
                    "welcome_prompt": "welcome.wav",
                    "invalid_prompt": "invalid.wav",
                    "timeout_seconds": 5,
                    "max_retries": 3,
                    "options": {
                        "0": {
                            "action": "extension",
                            "value": "101",
                        },
                        "1": {
                            "action": "repeat",
                        },
                        "2": {
                            "action": "extension",
                            "value": "102",
                        },
                    },
                },
                "children": [],
            },
        )
        db.add(ivr_tree)
        print(f"  ✓ Created IVR: {ivr_tree.name}")
        
        db.commit()
        
        print("\n✅ Seed data created successfully!")
        print("\n" + "="*60)
        print("IMPORTANT CREDENTIALS - Save these!")
        print("="*60)
        print(f"\nAPI Users:")
        print(f"  WHMCS: {whmcs_user.username} / whmcs-secret-change-this")
        print(f"  PBX Core: {pbx_user.username} / pbx-secret-change-this")
        print(f"  Admin: {admin_user.username} / admin-secret-change-this")
        print(f"\nPortal Login:")
        print(f"  Email: {portal_admin.email}")
        print(f"  Password: demo123")
        print(f"  Tenant: {sample_tenant.name} ({sample_tenant.domain})")
        print(f"\nExtensions:")
        print(f"  101 / ext101pass")
        print(f"  102 / ext102pass")
        print(f"\nDID: {did1.e164} -> Main Menu IVR")
        print(f"\nPlan Template IDs:")
        print(f"  Inbound Only: {inbound_template.id}")
        print(f"  Local Business: {business_template.id}")
        print(f"  Call Center: {callcenter_template.id}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
