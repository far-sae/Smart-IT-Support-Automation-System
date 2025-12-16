import msal
import aiohttp
from typing import Dict, Any, List, Optional
from app.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


class M365Integration:
    """Integration with Microsoft 365 / Azure AD via Microsoft Graph API"""
    
    def __init__(self):
        self.authority = settings.AZURE_AUTHORITY
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self.scope = [settings.AZURE_SCOPE]
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self._token = None
    
    async def _get_access_token(self) -> Optional[str]:
        """Get Microsoft Graph API access token"""
        if not self.client_id or not self.client_secret:
            logger.warning("Azure AD credentials not configured")
            return None
        
        try:
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret
            )
            
            result = app.acquire_token_for_client(scopes=self.scope)
            
            if "access_token" in result:
                self._token = result["access_token"]
                return self._token
            else:
                logger.error("Failed to acquire token", error=result.get("error_description"))
                return None
                
        except Exception as e:
            logger.error("Token acquisition failed", error=str(e))
            return None
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Graph API"""
        token = await self._get_access_token()
        if not token:
            return {'success': False, 'error': 'Authentication failed'}
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.graph_endpoint}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, json=data) as response:
                    if response.status in [200, 201, 204]:
                        if response.status == 204:
                            return {'success': True}
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(
                            "Graph API request failed",
                            status=response.status,
                            error=error_text
                        )
                        return {'success': False, 'error': error_text}
                        
        except Exception as e:
            logger.error("Graph API request exception", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def get_user_info(self, user_email: str) -> Dict[str, Any]:
        """Get user information from Azure AD"""
        result = await self._make_request('GET', f"/users/{user_email}")
        if result.get('success') is False:
            return {'error': result.get('error')}
        return result
    
    async def reset_password(self, user_email: str, new_password: str) -> Dict[str, Any]:
        """Reset user password in Azure AD"""
        data = {
            "passwordProfile": {
                "forceChangePasswordNextSignIn": True,
                "password": new_password
            }
        }
        
        result = await self._make_request('PATCH', f"/users/{user_email}", data)
        
        if result.get('success') or (not result.get('error')):
            return {'success': True, 'message': 'Password reset successfully'}
        return {'success': False, 'error': result.get('error')}
    
    async def unlock_account(self, user_email: str) -> Dict[str, Any]:
        """Unlock/enable user account in Azure AD"""
        data = {
            "accountEnabled": True
        }
        
        result = await self._make_request('PATCH', f"/users/{user_email}", data)
        
        if result.get('success') or (not result.get('error')):
            return {'success': True, 'message': 'Account unlocked successfully'}
        return {'success': False, 'error': result.get('error')}
    
    async def get_user_groups(self, user_email: str) -> List[str]:
        """Get user's group memberships"""
        result = await self._make_request('GET', f"/users/{user_email}/memberOf")
        
        if result.get('value'):
            return [group.get('displayName', '') for group in result['value']]
        return []
    
    async def add_user_to_group(self, user_email: str, group_name: str) -> Dict[str, Any]:
        """Add user to an Azure AD group"""
        # First, get the group ID
        groups_result = await self._make_request(
            'GET',
            f"/groups?$filter=displayName eq '{group_name}'"
        )
        
        if not groups_result.get('value'):
            return {'success': False, 'error': f'Group {group_name} not found'}
        
        group_id = groups_result['value'][0]['id']
        
        # Get user object ID
        user_result = await self.get_user_info(user_email)
        if user_result.get('error'):
            return {'success': False, 'error': user_result['error']}
        
        user_id = user_result['id']
        
        # Add user to group
        data = {
            "@odata.id": f"{self.graph_endpoint}/directoryObjects/{user_id}"
        }
        
        result = await self._make_request(
            'POST',
            f"/groups/{group_id}/members/$ref",
            data
        )
        
        if result.get('success'):
            return {'success': True, 'message': f'User added to group {group_name}'}
        return {'success': False, 'error': result.get('error')}
    
    async def check_user_license(self, user_email: str) -> Dict[str, Any]:
        """Check user's license assignments"""
        result = await self._make_request('GET', f"/users/{user_email}/licenseDetails")
        
        if result.get('value'):
            licenses = [lic.get('skuPartNumber', '') for lic in result['value']]
            return {'success': True, 'licenses': licenses}
        return {'success': False, 'licenses': []}
    
    async def revoke_user_sessions(self, user_email: str) -> Dict[str, Any]:
        """Revoke all user refresh tokens (force re-authentication)"""
        result = await self._make_request(
            'POST',
            f"/users/{user_email}/revokeSignInSessions"
        )
        
        if result.get('success') or result.get('value') is True:
            return {'success': True, 'message': 'User sessions revoked'}
        return {'success': False, 'error': result.get('error')}


# Global instance
m365_integration = M365Integration()
