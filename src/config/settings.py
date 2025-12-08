"""Settings and configuration management."""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache


class Settings:
    """
    Centralized configuration for the MCP server.
    
    All settings are loaded from environment variables with sensible defaults.
    This class provides a single source of truth for all configuration.
    """
    
    def __init__(self):
        # Workspace configuration
        self.workspace_dir: Path = Path(os.getenv("WORKSPACE_DIR", "./workspace")).resolve()
        
        # External tool binaries
        self.openscad_bin: str = os.getenv("OPENSCAD_BIN", "openscad")
        self.slicer_bin: str = os.getenv("SLICER_BIN", "")
        
        # OctoPrint configuration
        self.octoprint_url: str = os.getenv("OCTOPRINT_URL", "http://localhost:5000")
        self.octoprint_api_key: str = os.getenv("OCTOPRINT_API_KEY", "")
        
        # MCP transport configuration
        valid_transports = ["stdio", "sse", "streamable-http"]
        transport_env = os.getenv("MCP_TRANSPORT", "stdio")
        self.mcp_transport: str = transport_env if transport_env in valid_transports else "stdio"
        
        # Performance tuning
        self.max_output_length: int = int(os.getenv("MAX_OUTPUT_LENGTH", "10000"))
        self.command_timeout: int = int(os.getenv("COMMAND_TIMEOUT", "120"))
        self.slice_timeout: int = int(os.getenv("SLICE_TIMEOUT", "300"))
        
        # Web server configuration
        self.web_host: str = os.getenv("WEB_HOST", "127.0.0.1")
        self.web_port: int = int(os.getenv("WEB_PORT", "8080"))
        
        # OAuth configuration
        self.oauth_enabled: bool = os.getenv("OAUTH_ENABLED", "false").lower() in ("true", "1", "yes")
        self.oauth_client_id: str = os.getenv("OAUTH_CLIENT_ID", "")
        self.oauth_client_secret: str = os.getenv("OAUTH_CLIENT_SECRET", "")
        self.oauth_authorize_url: str = os.getenv("OAUTH_AUTHORIZE_URL", "")
        self.oauth_token_url: str = os.getenv("OAUTH_TOKEN_URL", "")
        self.oauth_userinfo_url: str = os.getenv("OAUTH_USERINFO_URL", "")
        self.oauth_redirect_uri: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8080/auth/callback")
        self.oauth_secret_key: str = os.getenv("OAUTH_SECRET_KEY", "change-me-in-production")
        
        # Logging configuration
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        
    def validate(self) -> list[str]:
        """
        Validate configuration and return list of warnings/errors.
        
        Returns:
            List of validation messages (empty if all valid)
        """
        messages = []
        
        # Check if workspace can be created
        try:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messages.append(f"Cannot create workspace directory: {e}")
        
        # Warn about missing optional configurations
        if not self.openscad_bin:
            messages.append("OPENSCAD_BIN not configured - CAD features will not work")
        
        if not self.slicer_bin:
            messages.append("SLICER_BIN not configured - slicing features will not work")
        
        if not self.octoprint_api_key:
            messages.append("OCTOPRINT_API_KEY not configured - printer features will not work")
        
        # Validate OAuth configuration if enabled
        if self.oauth_enabled:
            if not self.oauth_client_id:
                messages.append("OAUTH_CLIENT_ID is required when OAuth is enabled")
            if not self.oauth_client_secret:
                messages.append("OAUTH_CLIENT_SECRET is required when OAuth is enabled")
            if not self.oauth_authorize_url:
                messages.append("OAUTH_AUTHORIZE_URL is required when OAuth is enabled")
            if not self.oauth_token_url:
                messages.append("OAUTH_TOKEN_URL is required when OAuth is enabled")
            # Check for common insecure default secret keys
            insecure_defaults = [
                "change-me-in-production",
                "CHANGE-THIS-TO-A-RANDOM-SECRET-KEY-BEFORE-ENABLING-OAUTH"
            ]
            if self.oauth_secret_key in insecure_defaults:
                messages.append("WARNING: OAUTH_SECRET_KEY must be changed from default for security!")
        
        return messages
    
    @property
    def models_dir(self) -> Path:
        """Get the models directory within the workspace."""
        return self.workspace_dir / "models"
    
    def ensure_workspace(self) -> None:
        """Ensure workspace and models directories exist."""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures we only create one Settings instance
    and reuse it throughout the application, improving efficiency.
    
    Returns:
        Settings instance
    """
    return Settings()
