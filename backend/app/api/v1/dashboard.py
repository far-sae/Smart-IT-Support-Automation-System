from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict
from datetime import datetime, timedelta
from app.database import get_db
from app.models import (
    Ticket as TicketModel,
    User as UserModel,
    AutomationExecution,
    AuditLog,
    TicketStatus,
    TicketCategory,
    AutomationStatus
)
from app.schemas import DashboardStats
from app.auth import get_current_active_user

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get dashboard statistics"""
    
    # Total tickets
    total_tickets = db.query(func.count(TicketModel.id)).scalar()
    
    # Open tickets (not resolved or closed)
    open_tickets = db.query(func.count(TicketModel.id)).filter(
        TicketModel.status.in_([TicketStatus.NEW, TicketStatus.ANALYZING, TicketStatus.IN_PROGRESS])
    ).scalar()
    
    # Resolved tickets
    resolved_tickets = db.query(func.count(TicketModel.id)).filter(
        TicketModel.status == TicketStatus.RESOLVED
    ).scalar()
    
    # Auto-resolved tickets
    auto_resolved_tickets = db.query(func.count(TicketModel.id)).filter(
        TicketModel.auto_resolved == True
    ).scalar()
    
    # Auto-resolution rate
    auto_resolution_rate = (auto_resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0
    
    # Pending approvals
    pending_approvals = db.query(func.count(TicketModel.id)).filter(
        TicketModel.status == TicketStatus.AWAITING_APPROVAL
    ).scalar()
    
    # Failed automations
    failed_automations = db.query(func.count(AutomationExecution.id)).filter(
        AutomationExecution.status == AutomationStatus.FAILED
    ).scalar()
    
    # Tickets by category
    tickets_by_category_raw = db.query(
        TicketModel.category,
        func.count(TicketModel.id)
    ).group_by(TicketModel.category).all()
    
    tickets_by_category = {
        category.value: count for category, count in tickets_by_category_raw
    }
    
    # Tickets by status
    tickets_by_status_raw = db.query(
        TicketModel.status,
        func.count(TicketModel.id)
    ).group_by(TicketModel.status).all()
    
    tickets_by_status = {
        status.value: count for status, count in tickets_by_status_raw
    }
    
    # Recent tickets
    recent_tickets = db.query(TicketModel).order_by(
        desc(TicketModel.created_at)
    ).limit(10).all()
    
    return DashboardStats(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        resolved_tickets=resolved_tickets,
        auto_resolved_tickets=auto_resolved_tickets,
        auto_resolution_rate=round(auto_resolution_rate, 2),
        pending_approvals=pending_approvals,
        failed_automations=failed_automations,
        tickets_by_category=tickets_by_category,
        tickets_by_status=tickets_by_status,
        recent_tickets=recent_tickets
    )


@router.get("/activity")
async def get_recent_activity(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    limit: int = 50
):
    """Get recent system activity from audit logs"""
    
    activity = db.query(AuditLog).order_by(
        desc(AuditLog.timestamp)
    ).limit(limit).all()
    
    return activity


@router.get("/metrics/resolution-time")
async def get_resolution_time_metrics(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    days: int = 30
):
    """Get average resolution time metrics"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get resolved tickets in the time period
    resolved_tickets = db.query(TicketModel).filter(
        TicketModel.status == TicketStatus.RESOLVED,
        TicketModel.created_at >= cutoff_date,
        TicketModel.resolved_at.isnot(None)
    ).all()
    
    if not resolved_tickets:
        return {
            'average_resolution_minutes': 0,
            'median_resolution_minutes': 0,
            'auto_resolved_average': 0,
            'manual_resolved_average': 0,
            'total_resolved': 0
        }
    
    # Calculate resolution times
    resolution_times = []
    auto_resolution_times = []
    manual_resolution_times = []
    
    for ticket in resolved_tickets:
        if ticket.resolved_at and ticket.created_at:
            duration = (ticket.resolved_at - ticket.created_at).total_seconds() / 60  # minutes
            resolution_times.append(duration)
            
            if ticket.auto_resolved:
                auto_resolution_times.append(duration)
            else:
                manual_resolution_times.append(duration)
    
    # Calculate statistics
    avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    median_resolution = sorted(resolution_times)[len(resolution_times) // 2] if resolution_times else 0
    avg_auto = sum(auto_resolution_times) / len(auto_resolution_times) if auto_resolution_times else 0
    avg_manual = sum(manual_resolution_times) / len(manual_resolution_times) if manual_resolution_times else 0
    
    return {
        'average_resolution_minutes': round(avg_resolution, 2),
        'median_resolution_minutes': round(median_resolution, 2),
        'auto_resolved_average': round(avg_auto, 2),
        'manual_resolved_average': round(avg_manual, 2),
        'total_resolved': len(resolved_tickets),
        'auto_resolved_count': len(auto_resolution_times),
        'manual_resolved_count': len(manual_resolution_times)
    }


@router.get("/metrics/category-performance")
async def get_category_performance(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get automation success rate by ticket category"""
    
    categories = db.query(TicketCategory).distinct().all()
    
    performance = {}
    
    for category in [TicketCategory.PASSWORD_RESET, TicketCategory.ACCOUNT_UNLOCK, 
                     TicketCategory.VPN_ISSUE, TicketCategory.DEVICE_COMPLIANCE,
                     TicketCategory.ACCESS_REQUEST]:
        total = db.query(func.count(TicketModel.id)).filter(
            TicketModel.category == category
        ).scalar()
        
        auto_resolved = db.query(func.count(TicketModel.id)).filter(
            TicketModel.category == category,
            TicketModel.auto_resolved == True
        ).scalar()
        
        success_rate = (auto_resolved / total * 100) if total > 0 else 0
        
        performance[category.value] = {
            'total': total,
            'auto_resolved': auto_resolved,
            'success_rate': round(success_rate, 2)
        }
    
    return performance
