from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request, Response


DOC_PATH_PREFIXES = ("/docs", "/redoc", "/openapi")


def _is_docs_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in DOC_PATH_PREFIXES)


async def security_headers_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)

    if _is_docs_path(request.url.path):
        headers = {
            # Swagger UI potřebuje načíst assety z CDN, proto povolíme jsdelivr a inline styly.
            "Content-Security-Policy": (
                "default-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "img-src 'self' data: https://cdn.jsdelivr.net; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' data: https://cdn.jsdelivr.net https://fonts.gstatic.com; "
                "object-src 'none'"
            ),
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            # COOP/COEP/CORP vynecháme, jinak by blokovaly načtení externích assetů pro swagger.
        }
    else:
        headers = {
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Resource-Policy": "same-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "img-src 'self' data:; "
                "script-src 'self'; "
                "style-src 'self'; "
                "object-src 'none'"
            ),
        }

    for k, v in headers.items():
        response.headers[k] = v

    return response
