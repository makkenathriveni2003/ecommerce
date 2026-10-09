from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """
    High-performance pure ASGI middleware that adds OWASP security headers
    without breaking Content-Length, streaming responses, or GZip threshold detection.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                # Prevent MIME-sniffing
                headers["X-Content-Type-Options"] = "nosniff"
                # Prevent clickjacking
                headers["X-Frame-Options"] = "DENY"
                # Cross-site scripting filter
                headers["X-XSS-Protection"] = "1; mode=block"
                # Controlled referrer policy
                headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                # Restrict browser features
                headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
                # Content Security Policy (permits Swagger UI and ReDoc CDNs for documentation routes)
                path = scope.get("path", "")
                if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
                    headers["Content-Security-Policy"] = (
                        "default-src 'self' https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
                        "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
                        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                        "worker-src 'self' blob:; "
                        "connect-src 'self' http: https:;"
                    )
                else:
                    headers["Content-Security-Policy"] = (
                        "default-src 'self'; "
                        "img-src 'self' data: https:; "
                        "style-src 'self' 'unsafe-inline'; "
                        "script-src 'self' 'unsafe-inline'; "
                        "connect-src 'self' ws: wss: http: https:; "
                        "frame-ancestors 'none';"
                    )

            await send(message)

        await self.app(scope, receive, send_with_headers)
