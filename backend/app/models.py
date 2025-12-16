from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    VIEWER = "viewer"


class TicketStatus(str, enum.Enum):
    NEW = "new"
    ANALYZING = "analyzing"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    RESOLVED = "resolved"
    FAILED = "failed"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(str, enum.Enum):
    PASSWORD_RESET = "password_reset"
    ACCOUNT_UNLOCK = "account_unlock"
    VPN_ISSUE = "vpn_issue"
    ACCESS_REQUEST = "access_request"
    DEVICE_COMPLIANCE = "device_compliance"
    EMAIL_ISSUE = "email_issue"
    SOFTWARE_INSTALL = "software_install"
    OTHER = "other"


class AutomationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    REQUIRES_APPROVAL = "requires_approval"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tickets_created = relationship("Ticket", back_populates="creator", foreign_keys="Ticket.created_by")
    audit_logs = relationship("AuditLog", back_populates="user")


class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    
    # Ticket details
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(TicketCategory), nullable=False)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    status = Column(Enum(TicketStatus), default=TicketStatus.NEW)
    
    # User information
    requester_email = Column(String, nullable=False, index=True)
    requester_name = Column(String)
    affected_user = Column(String, index=True)  # User being helped (may differ from requester)
    
    # Classification and diagnosis
    confidence_score = Column(Float)  # AI classification confidence
    diagnosis_result = Column(JSON)  # Diagnostic findings
    
    # Automation
    can_auto_resolve = Column(Boolean, default=False)
    auto_resolved = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    
    # Foreign Keys
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", back_populates="tickets_created", foreign_keys=[created_by])
    automations = relationship("AutomationExecution", back_populates="ticket")
    audit_logs = relationship("AuditLog", back_populates="ticket")
    approvals = relationship("ApprovalRequest", back_populates="ticket")


class AutomationExecution(Base):
    __tablename__ = "automation_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    
    # Automation details
    automation_type = Column(String, nullable=False)  # password_reset, vpn_fix, etc.
    status = Column(Enum(AutomationStatus), default=AutomationStatus.PENDING)
    
    # Execution details
    script_name = Column(String)
    parameters = Column(JSON)  # Script parameters
    before_state = Column(JSON)  # State before execution
    after_state = Column(JSON)  # State after execution
    output = Column(Text)  # Script output
    error_message = Column(Text)
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=2)
    
    # Safety
    rollback_possible = Column(Boolean, default=False)
    rollback_script = Column(String)
    rolled_back = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("Ticket", back_populates="automations")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Action details
    action = Column(String, nullable=False, index=True)
    resource_type = Column(String)  # ticket, automation, user, etc.
    resource_id = Column(String)
    
    # Before and after state
    before_state = Column(JSON)
    after_state = Column(JSON)
    
    # Context
    ip_address = Column(String)
    user_agent = Column(String)
    additional_data = Column(JSON)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    
    # Approval details
    automation_type = Column(String, nullable=False)
    reason = Column(Text)  # Why approval is needed
    risk_level = Column(String)  # low, medium, high, critical
    
    # Status
    status = Column(String, default="pending")  # pending, approved, rejected
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True))
    
    # Approver
    approver_id = Column(Integer, ForeignKey("users.id"))
    approver_comments = Column(Text)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="approvals")


class AutomationPolicy(Base):
    __tablename__ = "automation_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Policy details
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    category = Column(Enum(TicketCategory), nullable=False)
    
    # Conditions
    auto_execute = Column(Boolean, default=True)
    require_approval = Column(Boolean, default=False)
    approval_conditions = Column(JSON)  # Conditions requiring approval
    
    # Execution settings
    max_retries = Column(Integer, default=2)
    timeout_seconds = Column(Integer, default=300)
    rollback_on_failure = Column(Boolean, default=True)
    
    # Risk assessment
    risk_level = Column(String, default="low")
    
    # Active status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
