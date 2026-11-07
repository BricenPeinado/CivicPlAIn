"""Small local-demo transport guard, not authentication or production DoS protection."""
import asyncio
from starlette.responses import JSONResponse

MAX_BODY_BYTES = 1_048_576


class RequestLimits:
    def __init__(self, app, allowed_origins):
        self.app, self.allowed_origins = app, set(allowed_origins)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)

        async def reject(status, code, message):
            response = JSONResponse(status_code=status, content={'error': {
                'code': code, 'message': message, 'field_errors': [],
                'request_id': scope.get('state', {}).get('request_id', 'unavailable')}})
            await response(scope, receive, send)

        headers = dict(scope.get('headers', []))
        origin = headers.get(b'origin')
        if scope['method'] in {'POST', 'PATCH', 'DELETE'} and origin is not None:
            if origin.decode('latin-1') not in self.allowed_origins:
                return await reject(403, 'ORIGIN_NOT_ALLOWED', 'Mutation origin is not allowed')
        length = headers.get(b'content-length')
        if length is not None:
            try:
                if int(length) < 0:
                    raise ValueError
                if int(length) > MAX_BODY_BYTES:
                    return await reject(413, 'REQUEST_TOO_LARGE', 'Request body exceeds the 1 MiB limit')
            except ValueError:
                return await reject(400, 'INVALID_CONTENT_LENGTH', 'Invalid request length')
        # Enforce the limit even without Content-Length (chunked bodies).
        chunks, total = [], 0
        async def read_body():
            nonlocal total
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return False
                chunk = message.get('body', b'')
                total += len(chunk)
                if total > MAX_BODY_BYTES:
                    return False
                chunks.append(chunk)
                if not message.get('more_body', False):
                    return True
        try:
            complete = await asyncio.wait_for(read_body(), timeout=10)
        except asyncio.TimeoutError:
            return await reject(408, 'REQUEST_TIMEOUT', 'Request body took too long to arrive')
        if not complete:
            if total > MAX_BODY_BYTES:
                await reject(413, 'REQUEST_TOO_LARGE', 'Request body exceeds the 1 MiB limit')
            return
        body = b''.join(chunks)
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return await receive()
        await self.app(scope, replay, send)
