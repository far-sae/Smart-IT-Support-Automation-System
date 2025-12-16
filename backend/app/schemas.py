from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import (
    UserRole, TicketStatus, TicketPriority, TicketCategory,
    AutomationStatus
)


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Authentication
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Ticket Schemas
class TicketBase(BaseModel):
    subject: str
    description: str
    requester_email: EmailStr
    requester_name: Optional[str] = None
    affected_user: Optional[str] = None
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    affected_user: Optional[str] = None


class Ticket(TicketBase):
    id: int
    ticket_number: str
    category: TicketCategory
    status: TicketStatus
    confidence_score: Optional[float] = None
    diagnosis_result: Optional[Dict[str, Any]] = None
    can_auto_resolve: bool
    auto_resolved: bool
    requires_approval: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Automation Execution Schemas
class AutomationExecutionBase(BaseModel):
    automation_type: str
    parameters: Optional[Dict[str, Any]] = None


class AutomationExecutionCreate(AutomationExecutionBase):
    ticket_id: int


class AutomationExecution(AutomationExecutionBase):
    id: int
    ticket_id: int
    status: AutomationStatus
    script_name: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    output: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    retry_count: int
    rollback_possible: bool
    rolled_back: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Ticket with automations (defined after AutomationExecution)
class TicketWithAutomations(Ticket):
    automations: List[AutomationExecution] = []


# Audit Log Schemas
class AuditLogCreate(BaseModel):
    ticket_id: Optional[int] = None
    user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class AuditLog(AuditLogCreate):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Approval Request Schemas
class ApprovalRequestCreate(BaseModel):
    ticket_id: int
    automation_type: str
    reason: str
    risk_level: str


class ApprovalRequestUpdate(BaseModel):
    status: str
    approver_comments: Optional[str] = None


class ApprovalRequest(BaseModel):
    id: int
    ticket_id: int
    automation_type: str
    reason: str
    risk_level: str
    status: str
    requested_at: datetime
    responded_at: Optional[datetime] = None
    approver_id: Optional[int] = None
    approver_comments: Optional[str] = None
    
    class Config:
        from_attributes = True


# Automation Policy Schemas
class AutomationPolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: TicketCategory
    auto_execute: bool = True
    require_approval: bool = False
    approval_conditions: Optional[Dict[str, Any]] = None
    max_retries: int = 2
    timeout_seconds: int = 300
    rollback_on_failure: bool = True
    risk_level: str = "low"


class AutomationPolicyUpdate(BaseModel):
    description: Optional[str] = None
    auto_execute: Optional[bool] = None
    require_approval: Optional[bool] = None
    approval_conditions: Optional[Dict[str, Any]] = None
    max_retries: Optional[int] = None
    timeout_seconds: Optional[int] = None
    rollback_on_failure: Optional[bool] = None
    risk_level: Optional[str] = None
    is_active: Optional[bool] = None


class AutomationPolicy(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: TicketCategory
    auto_execute: bool
    require_approval: bool
    approval_conditions: Optional[Dict[str, Any]] = None
    max_retries: int
    timeout_seconds: int
    rollback_on_failure: bool
    risk_level: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Dashboard Statistics
class DashboardStats(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    auto_resolved_tickets: int
    auto_resolution_rate: float
    pending_approvals: int
    failed_automations: int
    tickets_by_category: Dict[str, int]
    tickets_by_status: Dict[str, int]
    recent_tickets: List[Ticket]
