# OAuth Configuration Guide

This guide explains how to configure OAuth authentication for the CadSlicerPrinter MCP Server.

## Overview

OAuth authentication provides secure access control to the MCP server's web interface and API endpoints. When enabled, users must authenticate through an OAuth provider before accessing the server.

## Features

- **Secure Authentication**: Industry-standard OAuth 2.0 protocol
- **Session Management**: Persistent sessions with secure cookies
- **Protected Endpoints**: All API endpoints require authentication when OAuth is enabled
- **Flexible Configuration**: Works with any OAuth 2.0 provider (Google, GitHub, Auth0, etc.)

## Configuration

### Environment Variables

The following environment variables control OAuth behavior:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OAUTH_ENABLED` | Enable/disable OAuth authentication | No | `false` |
| `OAUTH_CLIENT_ID` | OAuth client ID from your provider | Yes* | - |
| `OAUTH_CLIENT_SECRET` | OAuth client secret from your provider | Yes* | - |
| `OAUTH_AUTHORIZE_URL` | OAuth authorization endpoint URL | Yes* | - |
| `OAUTH_TOKEN_URL` | OAuth token endpoint URL | Yes* | - |
| `OAUTH_USERINFO_URL` | OAuth userinfo endpoint URL | No | - |
| `OAUTH_REDIRECT_URI` | Redirect URI after OAuth callback | No | `http://localhost:8080/auth/callback` |
| `OAUTH_SECRET_KEY` | Secret key for session encryption | No | `change-me-in-production` |

\* Required when `OAUTH_ENABLED=true`

### Setting up OAuth Providers

#### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8080/auth/callback`
5. Note your Client ID and Client Secret

Configuration:
```bash
export OAUTH_ENABLED=true
export OAUTH_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
export OAUTH_CLIENT_SECRET="your-google-client-secret"
export OAUTH_AUTHORIZE_URL="https://accounts.google.com/o/oauth2/v2/auth"
export OAUTH_TOKEN_URL="https://oauth2.googleapis.com/token"
export OAUTH_USERINFO_URL="https://www.googleapis.com/oauth2/v1/userinfo"
export OAUTH_SECRET_KEY="your-random-secret-key-here"
```

#### GitHub OAuth

1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Click "New OAuth App"
3. Fill in the details:
   - Authorization callback URL: `http://localhost:8080/auth/callback`
4. Note your Client ID and Client Secret

Configuration:
```bash
export OAUTH_ENABLED=true
export OAUTH_CLIENT_ID="your-github-client-id"
export OAUTH_CLIENT_SECRET="your-github-client-secret"
export OAUTH_AUTHORIZE_URL="https://github.com/login/oauth/authorize"
export OAUTH_TOKEN_URL="https://github.com/login/oauth/access_token"
export OAUTH_USERINFO_URL="https://api.github.com/user"
export OAUTH_SECRET_KEY="your-random-secret-key-here"
```

#### Auth0

1. Create an Auth0 account and application
2. Configure application settings:
   - Application Type: Regular Web Application
   - Allowed Callback URLs: `http://localhost:8080/auth/callback`
3. Note your Client ID, Client Secret, and Domain

Configuration:
```bash
export OAUTH_ENABLED=true
export OAUTH_CLIENT_ID="your-auth0-client-id"
export OAUTH_CLIENT_SECRET="your-auth0-client-secret"
export OAUTH_AUTHORIZE_URL="https://your-domain.auth0.com/authorize"
export OAUTH_TOKEN_URL="https://your-domain.auth0.com/oauth/token"
export OAUTH_USERINFO_URL="https://your-domain.auth0.com/userinfo"
export OAUTH_SECRET_KEY="your-random-secret-key-here"
```

### Systemd Service Configuration

To enable OAuth in the systemd service:

1. Edit the service file:
   ```bash
   sudo nano /etc/systemd/system/cadslicerprinter@.service
   ```

2. Update the OAuth environment variables:
   ```ini
   Environment="OAUTH_ENABLED=true"
   Environment="OAUTH_CLIENT_ID=your-client-id"
   Environment="OAUTH_CLIENT_SECRET=your-client-secret"
   Environment="OAUTH_AUTHORIZE_URL=https://..."
   Environment="OAUTH_TOKEN_URL=https://..."
   Environment="OAUTH_USERINFO_URL=https://..."
   Environment="OAUTH_SECRET_KEY=your-random-secret-key"
   ```

3. Reload systemd and restart the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart cadslicerprinter@$USER.service
   ```

## OAuth Endpoints

When OAuth is enabled, the following authentication endpoints are available:

- `GET /auth/login` - Initiates OAuth login flow
- `GET /auth/callback` - OAuth provider callback endpoint
- `GET /auth/logout` - Logs out the current user
- `GET /auth/user` - Returns current user information

## Protected Endpoints

When OAuth is enabled, all API endpoints require authentication:

- `/api/cad/*` - CAD operations
- `/api/slicer/*` - Slicing operations
- `/api/printer/*` - Printer operations
- `/api/workspace/*` - Workspace operations

The health check endpoint `/api/health` is always public.

## Security Considerations

1. **Secret Key**: Always change `OAUTH_SECRET_KEY` from the default value in production
2. **HTTPS**: Use HTTPS in production environments (configure your reverse proxy)
3. **Redirect URI**: Ensure the redirect URI matches your OAuth provider configuration exactly
4. **Client Secret**: Keep your OAuth client secret secure and never commit it to version control
5. **Network Access**: By default, the server binds to `127.0.0.1` (localhost only). Change `--host` to `0.0.0.0` only if needed for network access

## Testing OAuth

1. Start the server with OAuth enabled:
   ```bash
   python server.py --web
   ```

2. Visit `http://localhost:8080` in your browser

3. You should be redirected to the OAuth provider login page

4. After successful authentication, you'll be redirected back to the application

5. Check authentication status at `http://localhost:8080/auth/user`

## Troubleshooting

### "OAuth is not enabled or configured" error

- Ensure `OAUTH_ENABLED=true` is set
- Verify all required OAuth environment variables are configured
- Check server logs for configuration validation errors

### Authentication loop or redirect issues

- Verify `OAUTH_REDIRECT_URI` matches the callback URL in your OAuth provider
- Ensure the redirect URI is registered in your OAuth provider's configuration
- Check that cookies are enabled in your browser

### Session not persisting

- Verify `OAUTH_SECRET_KEY` is set and consistent across restarts
- Check that `SessionMiddleware` is properly initialized
- Ensure cookies are not blocked by browser settings

## Disabling OAuth

To disable OAuth authentication:

1. Set `OAUTH_ENABLED=false` in your environment or service file
2. Restart the service

With OAuth disabled, all API endpoints are publicly accessible (recommended only for localhost development).
