"""Authentication middleware."""
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from utils.config import config
from utils.logger import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT authentication middleware."""
    
    # Public endpoints that don't require authentication
    PUBLIC_ENDPOINTS = [
        '/docs',
        '/redoc',
        '/openapi.json',
        '/health',
        '/',
        '/api/auth/login',
        '/api/auth/register'
    ]
    
    async def dispatch(self, request: Request, call_next):
        """Check authentication for protected endpoints."""
        
        # Skip authentication for public endpoints
        if any(request.url.path.startswith(endpoint) for endpoint in self.PUBLIC_ENDPOINTS):
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Authorization header missing"
            )
        
        try:
            # Extract token
            scheme, token = auth_header.split()
            
            if scheme.lower() != 'bearer':
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication scheme"
                )
            
            # Verify token
            payload = jwt.decode(
                token,
                config.api_secret_key,
                algorithms=[config.jwt_algorithm]
            )
            
            # Add user info to request state
            request.state.user = payload.get('sub')
            
            logger.debug(f"Authenticated user: {request.state.user}")
            
        except ValueError:
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format"
            )
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Authentication failed"
            )
        
        # Process request
        response = await call_next(request)
        return response


def get_current_user(request: Request) -> str:
    """Get current authenticated user from request."""
    if not hasattr(request.state, 'user'):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.state.user