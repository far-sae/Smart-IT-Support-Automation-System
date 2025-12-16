from typing import Dict, Any, Optional
from app.models import TicketCategory
import asyncio


class DiagnosisEngine:
    """Diagnose IT issues and determine root causes"""
    
    async def diagnose(self, category: TicketCategory, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main diagnosis dispatcher
        Returns diagnosis result with:
        - root_cause: identified issue
        - recommended_action: what should be done
        - automation_possible: can this be automated
        - risk_level: low/medium/high/critical
        """
        diagnosis_methods = {
            TicketCategory.PASSWORD_RESET: self._diagnose_password_issue,
            TicketCategory.ACCOUNT_UNLOCK: self._diagnose_account_lock,
            TicketCategory.VPN_ISSUE: self._diagnose_vpn_issue,
            TicketCategory.DEVICE_COMPLIANCE: self._diagnose_device_compliance,
            TicketCategory.ACCESS_REQUEST: self._diagnose_access_request,
        }
        
        diagnosis_method = diagnosis_methods.get(category, self._diagnose_generic)
        return await diagnosis_method(ticket_data)
    
    async def _diagnose_password_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnose password-related issues"""
        affected_user = data.get('affected_user', data.get('requester_email'))
        description = data.get('description', '').lower()
        
        # Determine specific issue
        if 'expired' in description:
            root_cause = "password_expired"
        elif 'forgot' in description or 'forgotten' in description:
            root_cause = "password_forgotten"
        elif "doesn't work" in description or "not working" in description:
            root_cause = "password_incorrect"
        else:
            root_cause = "password_reset_needed"
        
        return {
            'root_cause': root_cause,
            'affected_user': affected_user,
            'recommended_action': 'password_reset',
            'automation_possible': True,
            'risk_level': 'low',
            'requires_verification': True,
            'verification_method': 'email',
            'details': {
                'user': affected_user,
                'action': 'Reset password and send temporary password via email'
            }
        }
    
    async def _diagnose_account_lock(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnose account lockout issues"""
        affected_user = data.get('affected_user', data.get('requester_email'))
        description = data.get('description', '').lower()
        
        # Determine lock reason
        if 'too many' in description or 'attempts' in description:
            root_cause = "too_many_failed_attempts"
        elif 'disabled' in description:
            root_cause = "account_disabled"
        elif 'suspended' in description:
            root_cause = "account_suspended"
        else:
            root_cause = "account_locked"
        
        return {
            'root_cause': root_cause,
            'affected_user': affected_user,
            'recommended_action': 'unlock_account',
            'automation_possible': True,
            'risk_level': 'low',
            'requires_verification': True,
            'verification_method': 'multi_factor',
            'details': {
                'user': affected_user,
                'action': 'Unlock account and verify user identity'
            }
        }
    
    async def _diagnose_vpn_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnose VPN connectivity issues"""
        affected_user = data.get('affected_user', data.get('requester_email'))
        description = data.get('description', '').lower()
        
        # Determine VPN issue type
        if 'certificate' in description or 'cert' in description:
            root_cause = "vpn_certificate_expired"
            action = "renew_vpn_certificate"
        elif 'credentials' in description or 'password' in description:
            root_cause = "vpn_credentials_invalid"
            action = "reset_vpn_credentials"
        elif 'timeout' in description or 'slow' in description:
            root_cause = "vpn_connection_timeout"
            action = "reset_vpn_connection"
        elif 'disconnect' in description:
            root_cause = "vpn_disconnected"
            action = "reconnect_vpn"
        else:
            root_cause = "vpn_connection_failed"
            action = "diagnose_vpn_connection"
        
        return {
            'root_cause': root_cause,
            'affected_user': affected_user,
            'recommended_action': action,
            'automation_possible': True,
            'risk_level': 'medium',
            'requires_verification': False,
            'details': {
                'user': affected_user,
                'action': f'VPN diagnostics and {action}',
                'steps': [
                    'Check VPN client version',
                    'Verify user VPN access',
                    'Reset VPN profile if needed',
                    'Test connectivity'
                ]
            }
        }
    
    async def _diagnose_device_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnose device compliance issues"""
        affected_user = data.get('affected_user', data.get('requester_email'))
        description = data.get('description', '').lower()
        
        issues = []
        if 'patch' in description or 'update' in description:
            issues.append('missing_patches')
        if 'antivirus' in description or 'av' in description:
            issues.append('antivirus_outdated')
        if 'encryption' in description:
            issues.append('disk_not_encrypted')
        if 'firewall' in description:
            issues.append('firewall_disabled')
        
        if not issues:
            issues = ['compliance_check_needed']
        
        return {
            'root_cause': 'device_non_compliant',
            'affected_user': affected_user,
            'recommended_action': 'enforce_compliance',
            'automation_possible': True,
            'risk_level': 'medium',
            'requires_verification': False,
            'details': {
                'user': affected_user,
                'issues': issues,
                'action': 'Run compliance check and apply required patches',
                'steps': [
                    'Scan device for compliance',
                    'Install missing patches',
                    'Update antivirus definitions',
                    'Verify compliance status'
                ]
            }
        }
    
    async def _diagnose_access_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnose access permission requests"""
        affected_user = data.get('affected_user', data.get('requester_email'))
        description = data.get('description', '')
        
        # Extract requested resource (simple pattern matching)
        import re
        resource_patterns = [
            r'access\s+to\s+(\w+)',
            r'permission\s+for\s+(\w+)',
            r'(\w+)\s+folder',
            r'(\w+)\s+share'
        ]
        
        requested_resource = None
        for pattern in resource_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                requested_resource = match.group(1)
                break
        
        return {
            'root_cause': 'access_permission_needed',
            'affected_user': affected_user,
            'recommended_action': 'grant_access',
            'automation_possible': True,
            'risk_level': 'medium',
            'requires_verification': True,
            'requires_approval': True,  # Access requests typically need approval
            'verification_method': 'manager_approval',
            'details': {
                'user': affected_user,
                'resource': requested_resource or 'unspecified',
                'action': 'Verify authorization and grant access',
                'steps': [
                    'Verify user needs access',
                    'Check if user has appropriate role',
                    'Add user to appropriate group/resource',
                    'Verify access granted'
                ]
            }
        }
    
    async def _diagnose_generic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic diagnosis for uncategorized tickets"""
        return {
            'root_cause': 'requires_manual_review',
            'affected_user': data.get('affected_user', data.get('requester_email')),
            'recommended_action': 'manual_investigation',
            'automation_possible': False,
            'risk_level': 'unknown',
            'requires_verification': True,
            'details': {
                'action': 'Manual technician review required',
                'reason': 'Ticket does not match known automation patterns'
            }
        }


# Global instance
diagnosis_engine = DiagnosisEngine()
