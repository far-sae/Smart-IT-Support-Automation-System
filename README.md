# Smart IT Support Automation System

A production-ready IT support automation system that automatically resolves IT tickets with 70%+ auto-resolution capability.

## Core Features

### Automated Resolution
- Password Reset and Account Unlock via M365/Azure AD
- VPN Diagnostics and Fix
- Device Compliance Enforcement via PowerShell
- Access Permission Management with Approval Workflows

### Intelligent Processing
- AI-Powered Ticket Classification
- Root Cause Diagnosis Engine
- Safe Automation Execution with Rollback
- RBAC-Based Approval Layer

### Complete Visibility
- Real-time Dashboard with Metrics
- Complete Audit Trail
- Execution History and Logs

## Quick Start with Docker

1. Clone and configure:
```bash
cd Smart\ IT\ Support\ Automation\ System
cp .env.example .env
# Edit .env with your credentials
```

2. Start the system:
```bash
docker-compose up -d
```

3. Access the application:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:3000/dashboard

4. Create admin user:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "username": "admin",
    "password": "admin123",
    "full_name": "System Admin",
    "role": "admin"
  }'
```

## Manual Setup

### Backend Setup

1. Install dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Run migrations:
```bash
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

4. Start backend:
```bash
uvicorn app.main:app --reload
```

5. Start Celery worker:
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm start
```

## Configuration

### Required Environment Variables

**Database:**
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

**Security:**
- `SECRET_KEY`: JWT secret key (min 32 chars)
- `ALGORITHM`: HS256
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 30

**Microsoft 365 / Azure AD:**
- `AZURE_CLIENT_ID`: App registration client ID
- `AZURE_CLIENT_SECRET`: App secret
- `AZURE_TENANT_ID`: Tenant ID

**Email:**
- `EMAIL_SMTP_SERVER`: SMTP server
- `EMAIL_USERNAME`: Email username
- `EMAIL_PASSWORD`: Email password

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register user
- `GET /api/v1/auth/me` - Get current user

### Tickets
- `GET /api/v1/tickets/` - List tickets
- `POST /api/v1/tickets/` - Create ticket
- `GET /api/v1/tickets/{id}` - Get ticket details
- `PATCH /api/v1/tickets/{id}` - Update ticket
- `POST /api/v1/tickets/{id}/close` - Close ticket

### Dashboard
- `GET /api/v1/dashboard/stats` - Get statistics
- `GET /api/v1/dashboard/activity` - Get recent activity
- `GET /api/v1/dashboard/metrics/resolution-time` - Resolution metrics
- `GET /api/v1/dashboard/metrics/category-performance` - Category performance

### Automation
- `GET /api/v1/automation/executions` - List executions
- `POST /api/v1/automation/executions/{id}/retry` - Retry failed automation
- `GET /api/v1/automation/approvals` - List approvals
- `POST /api/v1/automation/approvals/{id}/approve` - Approve automation
- `GET /api/v1/automation/policies` - List policies
- `POST /api/v1/automation/policies` - Create policy

## Testing

Create a test ticket:
```bash
curl -X POST http://localhost:8000/api/v1/tickets/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Password reset needed",
    "description": "I forgot my password and cannot login",
    "requester_email": "user@company.com",
    "requester_name": "John Doe",
    "priority": "high"
  }'
```

## Security Hardening

1. Change default SECRET_KEY
2. Use HTTPS in production
3. Configure CORS properly
4. Enable rate limiting
5. Use environment-specific credentials
6. Enable audit logging
7. Restrict API access by IP if needed
8. Use service accounts with minimal permissions

## Production Deployment

### Using Docker Compose

1. Update .env for production
2. Set `DEBUG=False`
3. Configure reverse proxy (nginx/traefik)
4. Enable HTTPS with Let's Encrypt
5. Set up database backups
6. Configure monitoring (Prometheus/Grafana)

### Kubernetes Deployment

See `k8s/` directory for manifests.

## Monitoring

- Application logs: `logs/app.log`
- Celery logs: Check Celery worker output
- Audit logs: Database `audit_logs` table
- Metrics: Dashboard statistics API

## Troubleshooting

**Automation not executing:**
- Check Celery worker is running
- Verify Redis connection
- Check automation policies

**M365 integration failing:**
- Verify Azure AD credentials
- Check app permissions in Azure
- Ensure proper scopes granted

**Database connection errors:**
- Verify PostgreSQL is running
- Check DATABASE_URL format
- Ensure database exists

## Contributing

This is a production system. For modifications:
1. Test thoroughly in development
2. Review security implications
3. Update documentation
4. Add tests for new features

## License

Proprietary - Internal Use Only

## Support

For issues and questions, contact your IT automation team.
