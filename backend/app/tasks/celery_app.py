from celery import Celery
from app.config import get_settings
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Ticket, AutomationExecution, TicketStatus, AutomationStatus, AuditLog
from app.engines.diagnosis_engine import diagnosis_engine
from app.engines.automation_engine import automation_engine
from app.engines.integrations.email_integration import email_integration
from datetime import datetime
import structlog

logger = structlog.get_logger()
settings = get_settings()

# Initialize Celery
celery_app = Celery(
    'it_support_automation',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@celery_app.task(name='process_ticket_automation')
def process_ticket_automation(ticket_id: int):
    """Background task to process and execute ticket automation"""
    db = SessionLocal()
    
    try:
        logger.info("Processing ticket automation", ticket_id=ticket_id)
        
        # Get ticket
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            logger.error("Ticket not found", ticket_id=ticket_id)
            return {'success': False, 'error': 'Ticket not found'}
        
        # Update ticket status to analyzing
        ticket.status = TicketStatus.ANALYZING
        db.commit()
        
        # Run diagnosis synchronously (Celery tasks are not async)
        import asyncio
        diagnosis_result = asyncio.run(diagnosis_engine.diagnose(
            ticket.category,
            {
                'affected_user': ticket.affected_user,
                'requester_email': ticket.requester_email,
                'description': ticket.description,
                'subject': ticket.subject
            }
        ))
        
        # Store diagnosis result
        ticket.diagnosis_result = diagnosis_result
        db.commit()
        
        # Create audit log
        create_audit_log(
            db,
            ticket_id=ticket.id,
            action='diagnosis_completed',
            resource_type='ticket',
            resource_id=str(ticket.id),
            after_state=diagnosis_result
        )
        
        # Check if automation is possible
        if not diagnosis_result.get('automation_possible'):
            ticket.status = TicketStatus.IN_PROGRESS
            ticket.can_auto_resolve = False
            db.commit()
            logger.info("Ticket requires manual intervention", ticket_id=ticket_id)
            return {'success': True, 'message': 'Manual intervention required'}
        
        # Check if approval is required
        if diagnosis_result.get('requires_approval') or settings.REQUIRE_APPROVAL_FOR_CRITICAL:
            ticket.status = TicketStatus.AWAITING_APPROVAL
            ticket.requires_approval = True
            db.commit()
            logger.info("Ticket requires approval", ticket_id=ticket_id)
            return {'success': True, 'message': 'Approval required'}
        
        # Execute automation
        if settings.AUTO_RESOLVE_ENABLED:
            return execute_automation(db, ticket, diagnosis_result)
        else:
            logger.info("Auto-resolution disabled", ticket_id=ticket_id)
            return {'success': True, 'message': 'Auto-resolution disabled'}
            
    except Exception as e:
        logger.error("Error processing ticket automation", ticket_id=ticket_id, error=str(e))
        if ticket:
            ticket.status = TicketStatus.FAILED
            db.commit()
        return {'success': False, 'error': str(e)}
        
    finally:
        db.close()


def execute_automation(db: Session, ticket: Ticket, diagnosis_result: dict):
    """Execute the automation for a ticket"""
    import asyncio
    
    try:
        ticket.status = TicketStatus.IN_PROGRESS
        db.commit()
        
        # Create automation execution record
        automation_exec = AutomationExecution(
            ticket_id=ticket.id,
            automation_type=diagnosis_result['recommended_action'],
            status=AutomationStatus.PENDING,
            parameters={
                'user_email': ticket.affected_user,
                'affected_user': ticket.affected_user
            }
        )
        db.add(automation_exec)
        db.commit()
        
        # Execute automation
        automation_exec.status = AutomationStatus.RUNNING
        automation_exec.started_at = datetime.utcnow()
        db.commit()
        
        result = asyncio.run(automation_engine.execute_automation(
            automation_exec.automation_type,
            automation_exec.parameters,
            ticket.id
        ))
        
        automation_exec.completed_at = datetime.utcnow()
        automation_exec.duration_seconds = result.duration
        automation_exec.output = result.output
        automation_exec.before_state = result.before_state
        automation_exec.after_state = result.after_state
        
        if result.success:
            automation_exec.status = AutomationStatus.SUCCESS
            ticket.status = TicketStatus.RESOLVED
            ticket.resolved_at = datetime.utcnow()
            ticket.auto_resolved = True
            
            # Send resolution email
            asyncio.run(email_integration.send_ticket_resolved_email(
                ticket.requester_email,
                ticket.ticket_number,
                result.output
            ))
            
            logger.info("Automation successful", ticket_id=ticket.id)
        else:
            automation_exec.status = AutomationStatus.FAILED
            automation_exec.error_message = result.error
            ticket.status = TicketStatus.FAILED
            
            logger.error("Automation failed", ticket_id=ticket.id, error=result.error)
        
        db.commit()
        
        # Create audit log
        create_audit_log(
            db,
            ticket_id=ticket.id,
            action='automation_executed',
            resource_type='automation',
            resource_id=str(automation_exec.id),
            before_state=result.before_state,
            after_state=result.after_state
        )
        
        return {'success': result.success, 'output': result.output}
        
    except Exception as e:
        logger.error("Error executing automation", ticket_id=ticket.id, error=str(e))
        if automation_exec:
            automation_exec.status = AutomationStatus.FAILED
            automation_exec.error_message = str(e)
        ticket.status = TicketStatus.FAILED
        db.commit()
        return {'success': False, 'error': str(e)}


@celery_app.task(name='execute_approved_automation')
def execute_approved_automation(ticket_id: int, approver_id: int):
    """Execute automation after approval"""
    db = SessionLocal()
    
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return {'success': False, 'error': 'Ticket not found'}
        
        # Create audit log for approval
        create_audit_log(
            db,
            ticket_id=ticket.id,
            user_id=approver_id,
            action='automation_approved',
            resource_type='ticket',
            resource_id=str(ticket.id)
        )
        
        # Execute automation
        return execute_automation(db, ticket, ticket.diagnosis_result)
        
    except Exception as e:
        logger.error("Error executing approved automation", ticket_id=ticket_id, error=str(e))
        return {'success': False, 'error': str(e)}
        
    finally:
        db.close()


@celery_app.task(name='retry_failed_automation')
def retry_failed_automation(automation_id: int):
    """Retry a failed automation"""
    db = SessionLocal()
    
    try:
        automation_exec = db.query(AutomationExecution).filter(
            AutomationExecution.id == automation_id
        ).first()
        
        if not automation_exec:
            return {'success': False, 'error': 'Automation not found'}
        
        if automation_exec.retry_count >= automation_exec.max_retries:
            return {'success': False, 'error': 'Max retries exceeded'}
        
        # Increment retry count
        automation_exec.retry_count += 1
        db.commit()
        
        # Get ticket
        ticket = automation_exec.ticket
        
        # Execute automation again
        return execute_automation(db, ticket, ticket.diagnosis_result)
        
    except Exception as e:
        logger.error("Error retrying automation", automation_id=automation_id, error=str(e))
        return {'success': False, 'error': str(e)}
        
    finally:
        db.close()


def create_audit_log(
    db: Session,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    ticket_id: int = None,
    user_id: int = None,
    before_state: dict = None,
    after_state: dict = None,
    additional_data: dict = None
):
    """Helper to create audit log entries"""
    audit_log = AuditLog(
        ticket_id=ticket_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before_state=before_state,
        after_state=after_state,
        additional_data=additional_data
    )
    db.add(audit_log)
    db.commit()
    return audit_log
