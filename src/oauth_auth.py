"""OAuth authentication module for the MCP server."""

import logging
from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from itsdangerous import URLSafeTimedSerializer

from config import get_settings

logger = logging.getLogger(__name__)

# Global OAuth client
_oauth_client: Optional[OAuth] = None


def init_oauth() -> Optional[OAuth]:
    """
    Initialize OAuth client with configured settings.
    
    Returns:
        OAuth client if enabled and configured, None otherwise
    """
    global _oauth_client
    
    settings = get_settings()
    
    if not settings.oauth_enabled:
        logger.info("OAuth is disabled")
        return None
    
    if not all([
        settings.oauth_client_id,
        settings.oauth_client_secret,
        settings.oauth_authorize_url,
        settings.oauth_token_url
    ]):
        logger.error("OAuth is enabled but not properly configured")
        return None
    
    try:
        _oauth_client = OAuth()
        _oauth_client.register(
            name='pcmcp',
            client_id=settings.oauth_client_id,
            client_secret=settings.oauth_client_secret,
            authorize_url=settings.oauth_authorize_url,
            access_token_url=settings.oauth_token_url,
            userinfo_endpoint=settings.oauth_userinfo_url,
            client_kwargs={'scope': 'openid profile email'},
        )
        logger.info("OAuth client initialized successfully")
        return _oauth_client
    except Exception as e:
        logger.error(f"Failed to initialize OAuth client: {e}")
        return None


def get_oauth_client() -> Optional[OAuth]:
    """Get the OAuth client instance."""
    return _oauth_client


def is_authenticated(request: Request) -> bool:
    """
    Check if the current request is authenticated.
    
    Args:
        request: Starlette request object
    
    Returns:
        True if authenticated, False otherwise
    """
    settings = get_settings()
    
    # If OAuth is disabled, consider all requests authenticated
    if not settings.oauth_enabled:
        return True
    
    # Check if user is in session
    return request.session.get('user') is not None


def require_auth(func):
    """
    Decorator to require authentication for a route.
    
    Usage:
        @require_auth
        async def my_route(request):
            ...
    """
    async def wrapper(request: Request):
        if not is_authenticated(request):
            return JSONResponse(
                {"error": "Authentication required"},
                status_code=401
            )
        return await func(request)
    
    return wrapper


async def login(request: Request):
    """OAuth login route - redirects to OAuth provider."""
    settings = get_settings()
    oauth = get_oauth_client()
    
    if not settings.oauth_enabled or not oauth:
        return JSONResponse(
            {"error": "OAuth is not enabled or configured"},
            status_code=400
        )
    
    redirect_uri = settings.oauth_redirect_uri
    return await oauth.pcmcp.authorize_redirect(request, redirect_uri)


async def auth_callback(request: Request):
    """OAuth callback route - handles the OAuth provider's response."""
    settings = get_settings()
    oauth = get_oauth_client()
    
    if not settings.oauth_enabled or not oauth:
        return JSONResponse(
            {"error": "OAuth is not enabled or configured"},
            status_code=400
        )
    
    try:
        # Get the access token
        token = await oauth.pcmcp.authorize_access_token(request)
        
        # Get user info if userinfo endpoint is configured
        user = None
        if settings.oauth_userinfo_url:
            user = token.get('userinfo')
            if not user:
                # Fetch userinfo if not included in token
                user = await oauth.pcmcp.userinfo(token=token)
        
        # Store user in session
        request.session['user'] = dict(user) if user else {'authenticated': True}
        request.session['token'] = token
        
        logger.info(f"User authenticated: {user.get('email', 'unknown') if user else 'unknown'}")
        
        # Redirect to home page
        return RedirectResponse(url='/')
    
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return JSONResponse(
            {"error": f"Authentication failed: {str(e)}"},
            status_code=400
        )


async def logout(request: Request):
    """Logout route - clears the session."""
    request.session.clear()
    return RedirectResponse(url='/')


async def user_info(request: Request):
    """Get current user information."""
    if not is_authenticated(request):
        return JSONResponse(
            {"error": "Not authenticated"},
            status_code=401
        )
    
    user = request.session.get('user', {})
    return JSONResponse(user)
