import time
import threading
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class SecurityMiddleware(BaseHTTPMiddleware):
    # Per-process limiter; configure a shared gateway limiter for multiple workers.
    def __init__(self, app):
        super().__init__(app)
        self.events = defaultdict(deque)
        self.lock = threading.Lock()

    async def dispatch(self, request, call_next):
        if request.url.path.startswith('/api/v1/auth/') and request.method == 'POST':
            key = request.client.host if request.client else 'unknown'
            timestamp = time.monotonic()
            with self.lock:
                for stale in [k for k, v in self.events.items() if not v or v[-1] < timestamp - 60]:
                    del self.events[stale]
                queue = self.events[key]
                while queue and queue[0] < timestamp - 60:
                    queue.popleft()
                if len(queue) >= 30:
                    return JSONResponse({'detail': 'Too many authentication requests'}, 429, headers={'Retry-After': '60'})
                queue.append(timestamp)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Cache-Control'] = 'no-store'
        return response
