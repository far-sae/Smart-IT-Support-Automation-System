from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    Ticket as TicketModel,
    User as UserModel,
    UserRole,
    AutomationExecution,
    ApprovalRequest,
    AutomationPolicy,
    TicketStatus
)
from app.schemas import (
    AutomationPolicy as AutomationPolicySchema,
    AutomationPolicyCreate,
    AutomationPolicyUpdate,
    ApprovalRequest as ApprovalRequestSchema,
    ApprovalRequestUpdate
)
from app.auth import get_current_active_user, require_role
from app.tasks.celery_app import execute_approved_automation, retry_failed_automation
from datetime import datetime

router = APIRouter()


@router.get("/executions")
async def list_automation_executions(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    ticket_id: int = None,
    skip: int = 0,
    limit: int = 100
):
    """List automation execution history"""
    query = db.query(AutomationExecution)
    
    if ticket_id:
        query = query.filter(AutomationExecution.ticket_id == ticket_id)
    
    executions = query.order_by(AutomationExecution.created_at.desc()).offset(skip).limit(limit).all()
    
    return executions


@router.post("/executions/{execution_id}/retry")
async def retry_automation(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role([UserRole.ADMIN, UserRole.TECHNICIAN]))
):
    """Retry a failed automation"""
    execution = db.query(AutomationExecution).filter(
        AutomationExecution.id == execution_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Automation execution not found")
    
    if execution.retry_count >= execution.max_retries:
        raise HTTPException(status_code=400, detail="Max retries exceeded")
    
    # Queue retry task
    retry_failed_automation.delay(execution_id)
    
    return {"message": "Automation retry queued", "execution_id": execution_id}


@router.get("/approvals")
async def list_approval_requests(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    status: str = "pending"
):
    """List approval requests"""
    query = db.query(ApprovalRequest)
    
    if status:
        query = query.filter(ApprovalRequest.status == status)
    
    approvals = query.order_by(ApprovalRequest.requested_at.desc()).all()
    
    return approvals


@router.post("/approvals/{approval_id}/approve")
async def approve_automation(
    approval_id: int,
    update_data: ApprovalRequestUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role([UserRole.ADMIN, UserRole.TECHNICIAN]))
):
    """Approve an automation request"""
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.id == approval_id
    ).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval already processed")
    
    # Update approval
    approval.status = update_data.status
    approval.approver_id = current_user.id
    approval.approver_comments = update_data.approver_comments
    approval.responded_at = datetime.utcnow()
    
    db.commit()
    
    # If approved, execute automation
    if update_data.status == "approved":
        ticket = approval.ticket
        ticket.status = TicketStatus.IN_PROGRESS
        db.commit()
        
        execute_approved_automation.delay(ticket.id, current_user.id)
        
        return {"message": "Automation approved and queued for execution", "ticket_id": ticket.id}
    else:
        return {"message": "Automation rejected"}


@router.get("/policies", response_model=list[AutomationPolicySchema])
async def list_automation_policies(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """List automation policies"""
    policies = db.query(AutomationPolicy).all()
    return policies


@router.post("/policies", response_model=AutomationPolicySchema)
async def create_automation_policy(
    policy_data: AutomationPolicyCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new automation policy"""
    # Check if policy with same name exists
    existing = db.query(AutomationPolicy).filter(
        AutomationPolicy.name == policy_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Policy with this name already exists")
    
    policy = AutomationPolicy(**policy_data.dict())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    return policy


@router.patch("/policies/{policy_id}", response_model=AutomationPolicySchema)
async def update_automation_policy(
    policy_id: int,
    policy_update: AutomationPolicyUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role([UserRole.ADMIN]))
):
    """Update an automation policy"""
    policy = db.query(AutomationPolicy).filter(AutomationPolicy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    update_data = policy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)
    
    db.commit()
    db.refresh(policy)
    
    return policy


@router.delete("/policies/{policy_id}")
async def delete_automation_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role([UserRole.ADMIN]))
):
    """Delete an automation policy"""
    policy = db.query(AutomationPolicy).filter(AutomationPolicy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    db.delete(policy)
    db.commit()
    
    return {"message": "Policy deleted successfully"}
