import logging
import uuid
from time import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("lumen")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # Attach request_id to request state so other parts of the app can use it
        request.state.request_id = request_id
        
        start = time()
        try:
            response = await call_next(request)
            elapsed = round((time() - start) * 1000, 2)
            logger.info(
                f"req_id={request_id} method={request.method} path={request.url.path} "
                f"status={response.status_code} elapsed={elapsed}ms"
            )
            return response
        except Exception as e:
            elapsed = round((time() - start) * 1000, 2)
            logger.error(
                f"req_id={request_id} method={request.method} path={request.url.path} "
                f"status=500 elapsed={elapsed}ms error={str(e)}"
            )
            raise
