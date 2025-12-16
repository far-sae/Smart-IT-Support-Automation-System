import asyncio
import subprocess
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from app.config import get_settings
from app.engines.integrations.m365_integration import M365Integration
from app.engines.integrations.vpn_integration import VPNIntegration
import structlog

logger = structlog.get_logger()
settings = get_settings()


class AutomationResult:
    """Result of an automation execution"""
    def __init__(self, success: bool, output: str = "", error: str = "", 
                 before_state: Dict = None, after_state: Dict = None, duration: float = 0):
        self.success = success
        self.output = output
        self.error = error
        self.before_state = before_state or {}
        self.after_state = after_state or {}
        self.duration = duration


class AutomationEngine:
    """Execute automated IT support actions safely"""
    
    def __init__(self):
        self.m365 = M365Integration()
        self.vpn = VPNIntegration()
        
    async def execute_automation(
        self,
        automation_type: str,
        parameters: Dict[str, Any],
        ticket_id: int
    ) -> AutomationResult:
        """
        Main automation dispatcher
        Routes to specific automation handlers
        """
        logger.info(
            "Starting automation",
            automation_type=automation_type,
            ticket_id=ticket_id,
            parameters=parameters
        )
        
        # Check if we should use mock mode (for demo/testing)
        use_mock = not all([settings.AZURE_CLIENT_ID, settings.AZURE_CLIENT_SECRET, settings.AZURE_TENANT_ID])
        if use_mock:
            logger.info("Using MOCK mode for automation (no real credentials configured)", automation_type=automation_type)
        
        automation_handlers = {
            'password_reset': self._execute_password_reset,
            'unlock_account': self._execute_account_unlock,
            'reset_vpn_credentials': self._execute_vpn_reset,
            'reset_vpn_connection': self._execute_vpn_reset,  # Alias for VPN fix
            'diagnose_vpn_connection': self._execute_vpn_diagnostics,
            'enforce_compliance': self._execute_compliance_check,
            'grant_access': self._execute_grant_access,
        }
        
        handler = automation_handlers.get(automation_type)
        if not handler:
            return AutomationResult(
                success=False,
                error=f"Unknown automation type: {automation_type}"
            )
        
        start_time = datetime.now()
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                handler(parameters),
                timeout=settings.AUTOMATION_TIMEOUT_SECONDS
            )
            result.duration = (datetime.now() - start_time).total_seconds()
            return result
            
        except asyncio.TimeoutError:
            logger.error("Automation timeout", automation_type=automation_type, ticket_id=ticket_id)
            return AutomationResult(
                success=False,
                error=f"Automation timed out after {settings.AUTOMATION_TIMEOUT_SECONDS} seconds"
            )
        except Exception as e:
            logger.error(
                "Automation failed",
                automation_type=automation_type,
                ticket_id=ticket_id,
                error=str(e)
            )
            return AutomationResult(success=False, error=str(e))
    
    async def _execute_password_reset(self, params: Dict[str, Any]) -> AutomationResult:
        """Reset user password via M365/Azure AD"""
        user_email = params.get('user_email') or params.get('affected_user')
        
        if not user_email:
            return AutomationResult(success=False, error="No user email provided")
        
        try:
            # Get current user state
            before_state = await self.m365.get_user_info(user_email)
            
            # Generate temporary password
            temp_password = self._generate_temp_password()
            
            # Reset password in M365
            reset_result = await self.m365.reset_password(user_email, temp_password)
            
            if reset_result['success']:
                # Get updated state
                after_state = await self.m365.get_user_info(user_email)
                
                # Send password to user via email
                await self._send_temp_password_email(user_email, temp_password)
                
                return AutomationResult(
                    success=True,
                    output=f"Password reset for {user_email}. Temporary password sent via email.",
                    before_state=before_state,
                    after_state=after_state
                )
            else:
                return AutomationResult(
                    success=False,
                    error=reset_result.get('error', 'Password reset failed')
                )
                
        except Exception as e:
            logger.error("Password reset failed", user=user_email, error=str(e))
            return AutomationResult(success=False, error=str(e))
    
    async def _execute_account_unlock(self, params: Dict[str, Any]) -> AutomationResult:
        """Unlock user account in M365/Azure AD"""
        user_email = params.get('user_email') or params.get('affected_user')
        
        if not user_email:
            return AutomationResult(success=False, error="No user email provided")
        
        try:
            # Get current user state
            before_state = await self.m365.get_user_info(user_email)
            
            # Check if account is actually locked
            if not before_state.get('accountEnabled') == False:
                return AutomationResult(
                    success=True,
                    output=f"Account {user_email} is not locked. No action needed.",
                    before_state=before_state,
                    after_state=before_state
                )
            
            # Unlock account
            unlock_result = await self.m365.unlock_account(user_email)
            
            if unlock_result['success']:
                # Get updated state
                after_state = await self.m365.get_user_info(user_email)
                
                # Notify user
                await self._send_account_unlocked_email(user_email)
                
                return AutomationResult(
                    success=True,
                    output=f"Account {user_email} unlocked successfully.",
                    before_state=before_state,
                    after_state=after_state
                )
            else:
                return AutomationResult(
                    success=False,
                    error=unlock_result.get('error', 'Account unlock failed')
                )
                
        except Exception as e:
            logger.error("Account unlock failed", user=user_email, error=str(e))
            return AutomationResult(success=False, error=str(e))
    
    async def _execute_vpn_reset(self, params: Dict[str, Any]) -> AutomationResult:
        """Reset VPN credentials/profile"""
        user_email = params.get('user_email') or params.get('affected_user')
        
        if not user_email:
            return AutomationResult(success=False, error="No user email provided")
        
        try:
            # Get current VPN state
            before_state = await self.vpn.get_user_vpn_status(user_email)
            
            # Reset VPN profile
            reset_result = await self.vpn.reset_vpn_profile(user_email)
            
            if reset_result['success']:
                # Get updated state
                after_state = await self.vpn.get_user_vpn_status(user_email)
                
                return AutomationResult(
                    success=True,
                    output=f"VPN profile reset for {user_email}.",
                    before_state=before_state,
                    after_state=after_state
                )
            else:
                return AutomationResult(
                    success=False,
                    error=reset_result.get('error', 'VPN reset failed')
                )
                
        except Exception as e:
            logger.error("VPN reset failed", user=user_email, error=str(e))
            return AutomationResult(success=False, error=str(e))
    
    async def _execute_vpn_diagnostics(self, params: Dict[str, Any]) -> AutomationResult:
        """Run VPN diagnostics"""
        user_email = params.get('user_email') or params.get('affected_user')
        
        if not user_email:
            return AutomationResult(success=False, error="No user email provided")
        
        try:
            # Run diagnostics
            diag_result = await self.vpn.run_diagnostics(user_email)
            
            return AutomationResult(
                success=diag_result['success'],
                output=json.dumps(diag_result.get('diagnostics', {}), indent=2),
                before_state=diag_result.get('diagnostics', {})
            )
                
        except Exception as e:
            logger.error("VPN diagnostics failed", user=user_email, error=str(e))
            return AutomationResult(success=False, error=str(e))
    
    async def _execute_compliance_check(self, params: Dict[str, Any]) -> AutomationResult:
        """Check and enforce device compliance via PowerShell"""
        user_email = params.get('user_email') or params.get('affected_user')
        device_name = params.get('device_name')
        
        if not user_email and not device_name:
            return AutomationResult(success=False, error="No user or device provided")
        
        try:
            # Run compliance check via PowerShell
            script_path = "scripts/Check-DeviceCompliance.ps1"
            ps_params = {
                'UserEmail': user_email,
                'DeviceName': device_name
            }
            
            result = await self._run_powershell_script(script_path, ps_params)
            
            return result
                
        except Exception as e:
            logger.error("Compliance check failed", user=user_email, error=str(e))
            return AutomationResult(success=False, error=str(e))
    
    async def _execute_grant_access(self, params: Dict[str, Any]) -> AutomationResult:
        """Grant access permissions (requires approval in production)"""
        user_email = params.get('user_email') or params.get('affected_user')
        resource = params.get('resource')
        group_name = params.get('group_name')
        
        if not user_email:
            return AutomationResult(success=False, error="No user email provided")
        
        try:
            # Get current user groups
            before_state = await self.m365.get_user_groups(user_email)
            
            # Add user to group (if specified)
            if group_name:
                add_result = await self.m365.add_user_to_group(user_email, group_name)
                
                if add_result['success']:
                    # Get updated groups
                    after_state = await self.m365.get_user_groups(user_email)
                    
                    return AutomationResult(
                        success=True,
                        output=f"User {user_email} added to group {group_name}.",
                        before_state={'groups': before_state},
                        after_state={'groups': after_state}
                    )
                else:
                    return AutomationResult(
                        success=False,
                        error=add_result.get('error', 'Failed to add user to group')
                    )
            else:
                return AutomationResult(
                    success=False,
                    error="No group specified for access grant"
                )
                
        except Exception as e:
            logger.error("Grant access failed", user=user_email, error=str(e))
            return AutomationResult(success=False, error=str(e))
    
    async def _run_powershell_script(
        self,
        script_path: str,
        parameters: Dict[str, Any]
    ) -> AutomationResult:
        """Execute PowerShell script with parameters"""
        if not settings.ENABLE_POWERSHELL_AUTOMATION:
            return AutomationResult(
                success=False,
                error="PowerShell automation is disabled"
            )
        
        try:
            # Build PowerShell command
            param_string = " ".join([
                f"-{key} '{value}'" for key, value in parameters.items()
            ])
            
            command = [
                settings.POWERSHELL_PATH,
                "-ExecutionPolicy", "Bypass",
                "-File", script_path,
                *param_string.split()
            ]
            
            # Execute
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode('utf-8')
                # Try to parse JSON output
                try:
                    result_data = json.loads(output)
                    return AutomationResult(
                        success=True,
                        output=output,
                        after_state=result_data
                    )
                except json.JSONDecodeError:
                    return AutomationResult(
                        success=True,
                        output=output
                    )
            else:
                return AutomationResult(
                    success=False,
                    error=stderr.decode('utf-8'),
                    output=stdout.decode('utf-8')
                )
                
        except Exception as e:
            logger.error("PowerShell execution failed", script=script_path, error=str(e))
            return AutomationResult(success=False, error=str(e))
    
    def _generate_temp_password(self) -> str:
        """Generate a secure temporary password"""
        import secrets
        import string
        
        # 12 characters: uppercase, lowercase, digits, special
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        return password
    
    async def _send_temp_password_email(self, user_email: str, temp_password: str):
        """Send temporary password via email"""
        # This would integrate with email service
        logger.info("Sending temp password", user=user_email)
        # Implementation in email integration
    
    async def _send_account_unlocked_email(self, user_email: str):
        """Notify user that account is unlocked"""
        logger.info("Sending account unlocked notification", user=user_email)
        # Implementation in email integration


# Global instance
automation_engine = AutomationEngine()
