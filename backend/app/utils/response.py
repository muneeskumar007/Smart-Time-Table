"""
Standard API response envelope.

Every successful response returned by this API has the shape:
    {"success": true, "message": "...", "data": {...}}

List endpoints additionally include a "meta" block with pagination info.
Error responses are produced separately by the exception handlers in
core/exceptions.py, which use the same {"success": false, ...} shape.
"""
from typing import Any


def success_response(data: Any = None, message: str = "Success", meta: dict | None = None) -> dict:
    body: dict[str, Any] = {"success": True, "message": message, "data": data}
    if meta is not None:
        body["meta"] = meta
    return body
