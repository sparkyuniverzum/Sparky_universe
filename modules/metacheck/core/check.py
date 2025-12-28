from __future__ import annotations

from html.parser import HTMLParser
from typing import Any, Dict, List, Tuple

TITLE_MIN = 30
TITLE_MAX = 60
DESC_MIN = 70
DESC_MAX = 160

OG_REQUIRED = ["og:title", "og:description", "og:image", "og:url"]
TW_REQUIRED = ["twitter:card", "twitter:title", "twitter:description", "twitter:image"]


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_text: List[str] = []
        self.title_count = 0
        self._in_title = False
        self.meta_name: Dict[str, List[str]] = {}
        self.meta_property: Dict[str, List[str]] = {}
        self.canonicals: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = True
            self.title_count += 1
        if tag == "meta":
            self._handle_meta(attrs)
        if tag == "link":
            self._handle_link(attrs)

    def handle_startendtag(
        self,
        tag: str,
        attrs: List[tuple[str, str | None]],
    ) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_text.append(data)

    def _handle_meta(self, attrs: List[tuple[str, str | None]]) -> None:
        data = {key.lower(): value for key, value in attrs if key}
        name = (data.get("name") or "").strip().lower()
        prop = (data.get("property") or "").strip().lower()
        content = (data.get("content") or "").strip()
        if name:
            self.meta_name.setdefault(name, []).append(content)
        if prop:
            self.meta_property.setdefault(prop, []).append(content)

    def _handle_link(self, attrs: List[tuple[str, str | None]]) -> None:
        data = {key.lower(): value for key, value in attrs if key}
        rel = (data.get("rel") or "").strip().lower()
        href = (data.get("href") or "").strip()
        if "canonical" in rel and href:
            self.canonicals.append(href)


def _first(values: List[str]) -> str | None:
    for value in values:
        if value and value.strip():
            return value.strip()
    return None


def _length(value: str | None) -> int:
    return len(value) if value else 0


def audit_html(html: Any) -> Tuple[Dict[str, Any] | None, str | None]:
    if html is None:
        return None, "HTML input is required."
    raw = str(html).strip()
    if not raw:
        return None, "HTML input is required."

    parser = _MetaParser()
    parser.feed(raw)
    parser.close()

    title_value = "".join(parser.title_text).strip() or None
    title_length = _length(title_value)
    desc_values = parser.meta_name.get("description", [])
    desc_value = _first(desc_values)
    desc_length = _length(desc_value)

    canonical_value = _first(parser.canonicals)
    robots_value = _first(parser.meta_name.get("robots", []))

    og_present = {
        key: _first(parser.meta_property.get(key, [])) for key in OG_REQUIRED
    }
    og_missing = [key for key, value in og_present.items() if not value]

    tw_present = {
        key: _first(parser.meta_name.get(key, [])) for key in TW_REQUIRED
    }
    tw_missing = [key for key, value in tw_present.items() if not value]

    issues: List[str] = []
    warnings: List[str] = []

    if not title_value:
        issues.append("Missing <title> tag.")
    else:
        if title_length < TITLE_MIN:
            warnings.append("Title is shorter than recommended.")
        if title_length > TITLE_MAX:
            warnings.append("Title is longer than recommended.")
        if parser.title_count > 1:
            warnings.append("Multiple <title> tags found.")

    if not desc_value:
        issues.append("Missing meta description.")
    else:
        if desc_length < DESC_MIN:
            warnings.append("Description is shorter than recommended.")
        if desc_length > DESC_MAX:
            warnings.append("Description is longer than recommended.")
        if len(desc_values) > 1:
            warnings.append("Multiple meta descriptions found.")

    if not canonical_value:
        warnings.append("Missing canonical link tag.")
    if len(parser.canonicals) > 1:
        warnings.append("Multiple canonical links found.")

    if og_missing:
        warnings.append("Missing Open Graph tags: " + ", ".join(og_missing))
    if tw_missing:
        warnings.append("Missing Twitter card tags: " + ", ".join(tw_missing))

    return {
        "title": {
            "value": title_value,
            "length": title_length,
            "count": parser.title_count,
        },
        "description": {
            "value": desc_value,
            "length": desc_length,
            "count": len(desc_values),
        },
        "canonical": {
            "value": canonical_value,
            "count": len(parser.canonicals),
        },
        "robots": {
            "value": robots_value,
        },
        "open_graph": {
            "present": og_present,
            "missing": og_missing,
        },
        "twitter": {
            "present": tw_present,
            "missing": tw_missing,
        },
        "issues": issues,
        "warnings": warnings,
    }, None
