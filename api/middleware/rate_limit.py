"""Rate limiting middleware."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from collections import defaultdict
import time
import redis
from utils.config import config
from utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware with Redis backend and in-memory fallback."""
    
    def __init__(self, app, max_requests: int = 100, window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI app
            max_requests: Maximum requests per window
            window: Time window in seconds
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
        
        # Initialize Redis client if enabled
        self.redis_client = None
        if config.enable_cache:
            try:
                self.redis_client = redis.Redis(
                    host=config.redis_host,
                    port=config.redis_port,
                    password=config.redis_password,
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info("RateLimitMiddleware: Using Redis backend")
            except Exception as e:
                logger.warning(f"RateLimitMiddleware: Redis unavailable, falling back to in-memory: {e}")
                self.redis_client = None
                
    async def dispatch(self, request: Request, call_next):
        """Check rate limit."""
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        if self.redis_client:
            try:
                # Sliding window rate limiting using Redis Sorted Set (ZSET)
                key = f"rate_limit:{client_ip}"
                pipe = self.redis_client.pipeline()
                # Clear expired timestamps
                pipe.zremrangebyscore(key, 0, now - self.window)
                # Count current requests
                pipe.zcard(key)
                # Add current request
                pipe.zadd(key, {str(now): now})
                # Refresh expire TTL
                pipe.expire(key, self.window)
                
                # Execute pipeline commands
                _, request_count, _, _ = pipe.execute()
                
                if request_count > self.max_requests:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"}
                    )
            except Exception as e:
                logger.error(f"Redis rate limiting error: {e}, using in-memory fallback")
                if self._in_memory_limit(client_ip, now):
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"}
                    )
        else:
            if self._in_memory_limit(client_ip, now):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"}
                )
                
        # Process request
        response = await call_next(request)
        return response

    def _in_memory_limit(self, client_ip: str, now: float) -> bool:
        """Fallback in-memory sliding window rate limiter."""
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return True
        
        # Add current request
        self.requests[client_ip].append(now)
        return False