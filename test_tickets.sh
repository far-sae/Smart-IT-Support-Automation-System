#!/bin/bash

# Get auth token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "🎫 Creating test tickets for automated resolution..."
echo ""

# Test Ticket 1: Password Reset
echo "1. Password Reset Ticket..."
curl -s -X POST "http://localhost:8000/api/v1/tickets/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Password reset needed urgently",
    "description": "I forgot my password and cannot login to my account. Please help me reset it.",
    "requester_email": "john.doe@company.com",
    "requester_name": "John Doe",
    "priority": "high"
  }' | grep -o '"ticket_number":"[^"]*' | cut -d'"' -f4

# Test Ticket 2: Account Unlock
echo "2. Account Unlock Ticket..."
curl -s -X POST "http://localhost:8000/api/v1/tickets/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Account locked - too many attempts",
    "description": "My account is locked due to multiple failed login attempts. I need it unlocked.",
    "requester_email": "jane.smith@company.com",
    "requester_name": "Jane Smith",
    "priority": "high"
  }' | grep -o '"ticket_number":"[^"]*' | cut -d'"' -f4

# Test Ticket 3: VPN Issue
echo "3. VPN Issue Ticket..."
curl -s -X POST "http://localhost:8000/api/v1/tickets/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "VPN connection not working",
    "description": "I cannot connect to VPN. Getting timeout errors. Need remote access.",
    "requester_email": "bob.wilson@company.com",
    "requester_name": "Bob Wilson",
    "priority": "medium"
  }' | grep -o '"ticket_number":"[^"]*' | cut -d'"' -f4

# Test Ticket 4: Device Compliance
echo "4. Device Compliance Ticket..."
curl -s -X POST "http://localhost:8000/api/v1/tickets/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Security updates needed",
    "description": "My device is showing compliance issues. Need security patches and antivirus update.",
    "requester_email": "alice.brown@company.com",
    "requester_name": "Alice Brown",
    "priority": "medium"
  }' | grep -o '"ticket_number":"[^"]*' | cut -d'"' -f4

echo ""
echo "✅ Test tickets created!"
echo "🤖 Watch them auto-resolve in the dashboard: http://localhost:3000/dashboard"
echo "📊 Check Celery logs: docker-compose logs -f celery_worker"
