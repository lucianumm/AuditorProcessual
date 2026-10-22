"""Typed registry of official portals: which source kind lives where and how it can be reached."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

REFERENCES = Path(__file__).resolve().parents[1] / "references"


@lru_cache(maxsize=1)
def load_registry() -> dict:
    return json.loads((REFERENCES / "official_source_registry.json").read_text(encoding="utf-8"))


def _host(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def portal_for(url: str) -> dict | None:
    """Most specific portal for an official URL (host plus optional path prefix)."""
    host, path = _host(url), urlsplit(url).path if isinstance(url, str) else ""
    best = None
    for portal in load_registry()["portals"]:
        hosts = portal.get("hosts", [])
        if portal.get("hosts_pattern", "").startswith("trt") and host.startswith(("trt", "www.trt")) and host.endswith(".jus.br"):
            matched = True
        else:
            matched = host in hosts
        if matched and portal.get("path_prefix") and not path.startswith(portal["path_prefix"]):
            matched = False
        if matched and (best is None or len(portal.get("path_prefix", "")) > len(best.get("path_prefix", ""))):
            best = portal
    return best


def access_tier(url: str) -> str:
    portal = portal_for(url)
    return portal["access_tier"] if portal else "unknown"


def routes(kind: str) -> list[dict]:
    """Portals to consult for one source kind, in preference order."""
    registry = load_registry()
    by_id = {p["id"]: p for p in registry["portals"]}
    return [by_id[i] for i in registry["kind_routes"].get(kind, registry["kind_routes"]["other"]) if i in by_id]
