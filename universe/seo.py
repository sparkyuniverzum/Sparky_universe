from __future__ import annotations

import json
import os
from typing import Any, Dict


def _flag(name: str, default: str = "off") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def seo_enabled() -> bool:
    return _flag("SPARKY_SEO", "off")


def _base_url(request: Any) -> str:
    env = os.getenv("SPARKY_SEO_BASE_URL", "").strip()
    if env:
        return env.rstrip("/")
    return str(request.base_url).rstrip("/")


def _join_url(base: str, path: str) -> str:
    if not path:
        return base
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def _page_json_ld(request: Any, name: str, description: str, page_type: str) -> str:
    base = _base_url(request)
    path = getattr(request.url, "path", "/")
    url = _join_url(base, path)
    payload: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": page_type,
        "name": name,
        "url": url,
    }
    if description:
        payload["description"] = description
    return json.dumps(payload, ensure_ascii=True)


def seo_site_json_ld(request: Any, name: str, description: str = "") -> str:
    return _page_json_ld(request, name, description, "WebSite")


def seo_collection_json_ld(request: Any, name: str, description: str = "") -> str:
    return _page_json_ld(request, name, description, "CollectionPage")


def seo_module_json_ld(request: Any, name: str, description: str = "") -> str:
    base = _base_url(request)
    path = getattr(request.url, "path", "/")
    url = _join_url(base, path)
    payload: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": name,
        "url": url,
        "operatingSystem": "Any",
    }
    if description:
        payload["description"] = description
    return json.dumps(payload, ensure_ascii=True)


def sitemap_xml(urls: list[str]) -> str:
    seen: set[str] = set()
    items: list[str] = []
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        escaped = (
            url.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\"", "&quot;")
            .replace("'", "&apos;")
        )
        items.append(f"  <url><loc>{escaped}</loc></url>")
    body = "\n".join(items)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
        f"{body}\n"
        "</urlset>\n"
    )
