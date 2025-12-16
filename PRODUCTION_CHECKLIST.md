# 🚀 Production Deployment Checklist

## ✅ Pre-Deployment

### 1. Infrastructure Setup
- [ ] Production server ready (Linux recommended: Ubuntu 20.04+, 4GB+ RAM, 2+ CPU cores)
- [ ] Domain name configured (e.g., support.yourcompany.com)
- [ ] DNS A record pointing to server IP
- [ ] Firewall configured (ports 80, 443, 22 open)
- [ ] Docker & Docker Compose installed
- [ ] PostgreSQL database provisioned (cloud or self-hosted)

### 2. Credentials & Configuration

#### Azure AD / Microsoft 365
- [ ] Azure AD app registration created
- [ ] Client ID obtained
- [ ] Client Secret generated
- [ ] Tenant ID noted
- [ ] API permissions granted:
  - [ ] User.ReadWrite.All
  - [ ] Directory.ReadWrite.All
  - [ ] Group.ReadWrite.All
- [ ] Admin consent granted

#### Email (SMTP)
- [ ] SMTP server configured
- [ ] Email credentials (app password for Gmail/M365)
- [ ] Test email sent successfully
- [ ] Sender address whitelisted

#### Optional Integrations
- [ ] Slack webhook URL (if using Slack)
- [ ] Teams webhook URL (if using Teams)
- [ ] VPN management API credentials (if applicable)

### 3. Security Configuration
- [ ] `.env` file updated with production values
- [ ] `DEBUG=False` in `.env`
- [ ] Strong `SECRET_KEY` generated (64+ characters)
- [ ] `REQUIRE_APPROVAL_FOR_CRITICAL=True`
- [ ] CORS origins set to production domain
- [ ] Database password changed from default
- [ ] Admin password will be changed after first login

### 4. SSL/TLS Certificates
- [ ] Let's Encrypt SSL certificates obtained
- [ ] Certificates copied to `nginx/ssl/`
- [ ] Auto-renewal configured

---

## 🔧 Deployment Steps

### Step 1: Clone & Configure
```bash
git clone <your-repo> /opt/it-support-automation
cd /opt/it-support-automation

# Update .env with production credentials
nano .env
```

### Step 2: Get SSL Certificates
```bash
chmod +x setup_ssl.sh
sudo ./setup_ssl.sh
```

### Step 3: Deploy
```bash
chmod +x deploy_production.sh
./deploy_production.sh
```

### Step 4: Verify Deployment
```bash
# Check services
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test health endpoint
curl https://support.yourcompany.com/health

# Test API docs
curl https://support.yourcompany.com/api/docs
```

---

## 🔐 Post-Deployment Security

### Change Default Credentials
1. Login with `admin` / `admin123`
2. Go to Settings → Change Password
3. Use strong password (16+ characters)

### Configure User Roles
- [ ] Create additional admin users
- [ ] Create agent users for support team
- [ ] Disable or remove default admin account

### Enable Audit Logging
- [ ] Verify audit logs are being created
- [ ] Set up log rotation
- [ ] Configure log monitoring/alerts

### Backup Configuration
```bash
# Backup database daily
0 2 * * * docker-compose exec postgres pg_dump -U postgres it_support_db > /backup/db_$(date +\%Y\%m\%d).sql

# Backup .env and configs
0 2 * * * tar -czf /backup/config_$(date +\%Y\%m\%d).tar.gz /opt/it-support-automation/.env /opt/it-support-automation/nginx
```

---

## 📊 Monitoring Setup

### Application Monitoring
- [ ] Set up Uptime monitoring (UptimeRobot, Pingdom, etc.)
- [ ] Configure health check alerts
- [ ] Monitor API response times
- [ ] Track error rates

### Infrastructure Monitoring
- [ ] CPU/Memory usage alerts
- [ ] Disk space monitoring
- [ ] Docker container health checks
- [ ] Log aggregation (ELK stack, Grafana, etc.)

### Business Metrics
- [ ] Auto-resolution rate tracking
- [ ] Average resolution time
- [ ] Ticket volume trends
- [ ] Integration failure alerts

---

## 🔄 Maintenance

### Regular Tasks
- **Daily**: Check logs for errors
- **Weekly**: Review auto-resolution metrics
- **Monthly**: Update dependencies, review security patches
- **Quarterly**: Backup restoration test, disaster recovery drill

### Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations (if any)
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## 🆘 Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Check database connection
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.database import engine; print(engine.connect())"
```

### Automation Failures
```bash
# Check Celery worker logs
docker-compose -f docker-compose.prod.yml logs celery_worker

# Check automation executions
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.database import SessionLocal; from app.models import AutomationExecution; db = SessionLocal(); print([e.error_message for e in db.query(AutomationExecution).filter_by(status='FAILED').all()])"
```

### SSL Certificate Renewal
```bash
# Manual renewal
sudo certbot renew

# Copy new certificates
sudo cp /etc/letsencrypt/live/support.yourcompany.com/*.pem nginx/ssl/

# Restart frontend
docker-compose -f docker-compose.prod.yml restart frontend
```

---

## 📞 Support

### Documentation
- API Docs: https://support.yourcompany.com/api/docs
- User Guide: `/docs/USER_GUIDE.md`
- Architecture: `/docs/ARCHITECTURE.md`

### Logs Location
- Application: `/opt/it-support-automation/logs/`
- Nginx: Docker container logs
- Celery: Docker container logs

### Contact
- Technical Issues: tech-support@yourcompany.com
- Security Issues: security@yourcompany.com
