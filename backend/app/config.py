from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Smart IT Support Automation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str
    DATABASE_ECHO: bool = False
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Microsoft 365 / Azure AD
    AZURE_CLIENT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""
    AZURE_TENANT_ID: str = ""
    AZURE_AUTHORITY: str = ""
    AZURE_SCOPE: str = "https://graph.microsoft.com/.default"
    
    # Email
    EMAIL_IMAP_SERVER: str = "outlook.office365.com"
    EMAIL_IMAP_PORT: int = 993
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_SMTP_SERVER: str = "smtp.office365.com"
    EMAIL_SMTP_PORT: int = 587
    
    # Slack
    SLACK_WEBHOOK_URL: str = ""
    SLACK_BOT_TOKEN: str = ""
    
    # Teams
    TEAMS_WEBHOOK_URL: str = ""
    
    # VPN
    VPN_MANAGEMENT_API: str = ""
    VPN_API_KEY: str = ""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # PowerShell
    POWERSHELL_PATH: str = "/usr/local/bin/pwsh"
    ENABLE_POWERSHELL_AUTOMATION: bool = True
    
    # Auto-Resolution
    AUTO_RESOLVE_ENABLED: bool = True
    AUTO_RESOLVE_THRESHOLD: float = 0.85
    REQUIRE_APPROVAL_FOR_CRITICAL: bool = True
    
    # Automation Limits
    MAX_PASSWORD_RESET_ATTEMPTS: int = 3
    MAX_AUTOMATION_RETRIES: int = 2
    AUTOMATION_TIMEOUT_SECONDS: int = 300
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
