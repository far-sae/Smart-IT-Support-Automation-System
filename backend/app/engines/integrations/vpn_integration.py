import aiohttp
from typing import Dict, Any
from app.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


class VPNIntegration:
    """Integration with VPN management system"""
    
    def __init__(self):
        self.api_url = settings.VPN_MANAGEMENT_API
        self.api_key = settings.VPN_API_KEY
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None
    ) -> Dict[str, Any]:
        """Make request to VPN API"""
        if not self.api_url or not self.api_key:
            logger.warning("VPN API not configured, using mock mode")
            return await self._mock_vpn_operation(endpoint, data)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.api_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, json=data) as response:
                    if response.status in [200, 201, 204]:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error("VPN API request failed", status=response.status, error=error_text)
                        return {'success': False, 'error': error_text}
                        
        except Exception as e:
            logger.error("VPN API request exception", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def get_user_vpn_status(self, user_email: str) -> Dict[str, Any]:
        """Get VPN status for user"""
        result = await self._make_request('GET', f"/users/{user_email}/vpn-status")
        return result
    
    async def reset_vpn_profile(self, user_email: str) -> Dict[str, Any]:
        """Reset VPN profile/credentials for user"""
        data = {'action': 'reset_profile'}
        result = await self._make_request('POST', f"/users/{user_email}/reset", data)
        return result
    
    async def renew_vpn_certificate(self, user_email: str) -> Dict[str, Any]:
        """Renew VPN certificate for user"""
        data = {'action': 'renew_certificate'}
        result = await self._make_request('POST', f"/users/{user_email}/certificate", data)
        return result
    
    async def run_diagnostics(self, user_email: str) -> Dict[str, Any]:
        """Run VPN diagnostics for user"""
        result = await self._make_request('GET', f"/users/{user_email}/diagnostics")
        return result
    
    async def disconnect_user(self, user_email: str) -> Dict[str, Any]:
        """Disconnect user's VPN session"""
        data = {'action': 'disconnect'}
        result = await self._make_request('POST', f"/users/{user_email}/session", data)
        return result
    
    async def _mock_vpn_operation(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Mock VPN operations for testing when API is not configured"""
        import asyncio
        await asyncio.sleep(0.5)  # Simulate API delay
        
        if 'vpn-status' in endpoint:
            return {
                'success': True,
                'connected': False,
                'last_connection': '2024-12-10T10:30:00Z',
                'certificate_expiry': '2025-06-15T00:00:00Z'
            }
        elif 'reset' in endpoint:
            return {
                'success': True,
                'message': 'VPN profile reset successfully',
                'new_credentials': 'sent_via_email'
            }
        elif 'certificate' in endpoint:
            return {
                'success': True,
                'message': 'Certificate renewed successfully',
                'expiry': '2026-01-01T00:00:00Z'
            }
        elif 'diagnostics' in endpoint:
            return {
                'success': True,
                'diagnostics': {
                    'client_version': '2.5.1',
                    'server_reachable': True,
                    'authentication_valid': True,
                    'certificate_valid': True,
                    'network_latency_ms': 45,
                    'issues_found': []
                }
            }
        elif 'session' in endpoint:
            return {
                'success': True,
                'message': 'User disconnected successfully'
            }
        
        return {'success': True, 'message': 'Mock operation completed'}
