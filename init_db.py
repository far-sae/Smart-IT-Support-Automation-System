#!/usr/bin/env python3
"""
Database initialization script
Creates initial admin user and default automation policies
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal
from app.models import User, UserRole, AutomationPolicy, TicketCategory
from app.auth import get_password_hash


def create_admin_user(db):
    """Create default admin user if not exists"""
    admin_email = "admin@company.com"
    
    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        print(f"✅ Admin user already exists: {admin_email}")
        return
    
    admin = User(
        email=admin_email,
        username="admin",
        full_name="System Administrator",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    
    db.add(admin)
    db.commit()
    
    print(f"✅ Created admin user: {admin_email}")
    print(f"   Username: admin")
    print(f"   Password: admin123")
    print(f"   ⚠️  CHANGE THIS PASSWORD IN PRODUCTION!")


def create_default_policies(db):
    """Create default automation policies"""
    policies = [
        {
            "name": "Password Reset - Auto",
            "description": "Automatically reset passwords for all users",
            "category": TicketCategory.PASSWORD_RESET,
            "auto_execute": True,
            "require_approval": False,
            "risk_level": "low",
            "max_retries": 2,
            "timeout_seconds": 300
        },
        {
            "name": "Account Unlock - Auto",
            "description": "Automatically unlock user accounts",
            "category": TicketCategory.ACCOUNT_UNLOCK,
            "auto_execute": True,
            "require_approval": False,
            "risk_level": "low",
            "max_retries": 2,
            "timeout_seconds": 300
        },
        {
            "name": "VPN Fix - Auto",
            "description": "Automatically diagnose and fix VPN issues",
            "category": TicketCategory.VPN_ISSUE,
            "auto_execute": True,
            "require_approval": False,
            "risk_level": "medium",
            "max_retries": 2,
            "timeout_seconds": 300
        },
        {
            "name": "Device Compliance - Auto",
            "description": "Automatically check and enforce device compliance",
            "category": TicketCategory.DEVICE_COMPLIANCE,
            "auto_execute": True,
            "require_approval": False,
            "risk_level": "medium",
            "max_retries": 2,
            "timeout_seconds": 600
        },
        {
            "name": "Access Request - Approval Required",
            "description": "Grant access with manager approval",
            "category": TicketCategory.ACCESS_REQUEST,
            "auto_execute": False,
            "require_approval": True,
            "risk_level": "high",
            "max_retries": 1,
            "timeout_seconds": 300
        }
    ]
    
    created_count = 0
    
    for policy_data in policies:
        existing = db.query(AutomationPolicy).filter(
            AutomationPolicy.name == policy_data["name"]
        ).first()
        
        if existing:
            continue
        
        policy = AutomationPolicy(**policy_data)
        db.add(policy)
        created_count += 1
    
    db.commit()
    
    if created_count > 0:
        print(f"✅ Created {created_count} default automation policies")
    else:
        print("✅ All default policies already exist")


def main():
    print("========================================")
    print("Database Initialization")
    print("========================================")
    print()
    
    # Create all tables first
    print("Creating database tables...")
    from app.database import Base, engine
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    print()
    
    db = SessionLocal()
    
    try:
        create_admin_user(db)
        create_default_policies(db)
        
        print()
        print("========================================")
        print("Initialization Complete!")
        print("========================================")
        print()
        print("You can now login with:")
        print("  Username: admin")
        print("  Password: admin123")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
