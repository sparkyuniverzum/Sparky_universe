from __future__ import annotations

import json
from typing import Any, Dict


class ValidationNormalizeMiddleware:
    """Normalize FastAPI 422 validation responses into 400 with a short error body."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        normalized = False

        async def send_wrapper(message: Dict[str, Any]) -> None:
            nonlocal normalized
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                if status_code == 422:
                    normalized = True
                    headers = list(message.get("headers", []))
                    payload = json.dumps({"error": "Invalid input."}).encode("utf-8")
                    filtered = [
                        (key, value)
                        for key, value in headers
                        if key.lower() not in {b"content-length"}
                    ]
                    filtered.append((b"content-type", b"application/json"))
                    await send(
                        {
                            "type": "http.response.start",
                            "status": 400,
                            "headers": filtered,
                        }
                    )
                    await send({"type": "http.response.body", "body": payload})
                    return
                await send(message)
                return
            if message["type"] == "http.response.body":
                if normalized:
                    return
                await send(message)
                return

        await self.app(scope, receive, send_wrapper)
