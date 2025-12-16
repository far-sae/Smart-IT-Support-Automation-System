from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import (
    Ticket as TicketModel,
    User as UserModel,
    TicketStatus,
    TicketCategory,
    AutomationExecution,
    AuditLog
)
from app.schemas import Ticket, TicketCreate, TicketUpdate, TicketWithAutomations
from app.auth import get_current_active_user
from app.engines.ticket_classifier import ticket_classifier
from app.tasks.celery_app import process_ticket_automation
import structlog
import uuid

logger = structlog.get_logger()
router = APIRouter()


def generate_ticket_number() -> str:
    """Generate unique ticket number"""
    prefix = "IT"
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = str(uuid.uuid4())[:6].upper()
    return f"{prefix}-{timestamp}-{random_suffix}"


@router.post("/", response_model=Ticket, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Create a new IT support ticket"""
    logger.info("Creating new ticket", requester=ticket_data.requester_email)
    
    # Classify the ticket
    classification = ticket_classifier.classify(
        ticket_data.subject,
        ticket_data.description
    )
    
    # Extract affected user
    affected_user = ticket_data.affected_user
    if not affected_user:
        affected_user = ticket_classifier.extract_user_from_ticket(
            ticket_data.subject,
            ticket_data.description,
            ticket_data.requester_email
        )
    
    # Create ticket
    db_ticket = TicketModel(
        ticket_number=generate_ticket_number(),
        subject=ticket_data.subject,
        description=ticket_data.description,
        requester_email=ticket_data.requester_email,
        requester_name=ticket_data.requester_name,
        affected_user=affected_user,
        priority=classification['priority'],
        category=classification['category'],
        confidence_score=classification['confidence'],
        can_auto_resolve=classification['can_auto_resolve'],
        status=TicketStatus.NEW,
        created_by=current_user.id
    )
    
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    
    # Create audit log
    audit_log = AuditLog(
        ticket_id=db_ticket.id,
        user_id=current_user.id,
        action='ticket_created',
        resource_type='ticket',
        resource_id=str(db_ticket.id),
        after_state={
            'ticket_number': db_ticket.ticket_number,
            'category': db_ticket.category.value,
            'priority': db_ticket.priority.value
        }
    )
    db.add(audit_log)
    db.commit()
    
    # Trigger automation processing in background
    if db_ticket.can_auto_resolve:
        process_ticket_automation.delay(db_ticket.id)
        logger.info("Queued ticket for automation", ticket_id=db_ticket.id)
    
    return db_ticket


@router.get("/", response_model=List[Ticket])
async def list_tickets(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    status: Optional[TicketStatus] = None,
    category: Optional[TicketCategory] = None,
    auto_resolved: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
):
    """List tickets with optional filters"""
    query = db.query(TicketModel)
    
    # Apply filters
    if status:
        query = query.filter(TicketModel.status == status)
    if category:
        query = query.filter(TicketModel.category == category)
    if auto_resolved is not None:
        query = query.filter(TicketModel.auto_resolved == auto_resolved)
    
    # Order by created date descending
    query = query.order_by(desc(TicketModel.created_at))
    
    # Pagination
    tickets = query.offset(skip).limit(limit).all()
    
    return tickets


@router.get("/{ticket_id}", response_model=TicketWithAutomations)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get ticket details with automation history"""
    ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return ticket


@router.patch("/{ticket_id}", response_model=Ticket)
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Update ticket information"""
    ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Store before state
    before_state = {
        'status': ticket.status.value if ticket.status else None,
        'priority': ticket.priority.value if ticket.priority else None
    }
    
    # Update fields
    update_data = ticket_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)
    
    db.commit()
    db.refresh(ticket)
    
    # Create audit log
    audit_log = AuditLog(
        ticket_id=ticket.id,
        user_id=current_user.id,
        action='ticket_updated',
        resource_type='ticket',
        resource_id=str(ticket.id),
        before_state=before_state,
        after_state={
            'status': ticket.status.value if ticket.status else None,
            'priority': ticket.priority.value if ticket.priority else None
        }
    )
    db.add(audit_log)
    db.commit()
    
    return ticket


@router.post("/{ticket_id}/close", response_model=Ticket)
async def close_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Close a ticket"""
    ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.status = TicketStatus.CLOSED
    ticket.closed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ticket)
    
    # Create audit log
    audit_log = AuditLog(
        ticket_id=ticket.id,
        user_id=current_user.id,
        action='ticket_closed',
        resource_type='ticket',
        resource_id=str(ticket.id)
    )
    db.add(audit_log)
    db.commit()
    
    return ticket


@router.get("/{ticket_id}/audit-logs")
async def get_ticket_audit_logs(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get audit logs for a ticket"""
    ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    audit_logs = db.query(AuditLog).filter(
        AuditLog.ticket_id == ticket_id
    ).order_by(desc(AuditLog.timestamp)).all()
    
    return audit_logs
