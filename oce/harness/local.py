"""Deterministic in-process harness (B6-I2, section C1.S4).

``up(profile)`` returns a typed endpoint set for a declared profile. It opens no socket, resolves
no DNS name, reads no environment variable and starts no process, so a fresh machine can run the
whole profile with nothing installed beyond the standard library. Profiles, services and the
permitted import set are frozen data; anything else is refused by name.
"""
from __future__ import annotations

from ..templates.refusals import refuse

SERVICES = {
    "app": {"transport": "in-process", "address": "local://app"},
    "db": {"transport": "in-process", "address": "local://db"},
    "evidence": {"transport": "in-process", "address": "local://evidence"},
    "queue": {"transport": "in-process", "address": "local://queue"},
}

PROFILES = {
    "local": ("app", "db", "queue", "evidence"),
    "minimal": ("app",),
}

PERMITTED_IMPORTS = ("hashlib", "json", "pathlib", "typing")

NETWORK_MODULES = ("aiohttp", "ftplib", "http", "httpx", "requests", "socket", "ssl",
                   "telnetlib", "urllib")


def profiles() -> dict:
    return {name: sorted(services) for name, services in sorted(PROFILES.items())}


def up(profile: str = "local", *, services=None, imports=()) -> dict:
    """Return the typed endpoint set for a profile, or refuse with a named code."""
    if profile not in PROFILES:
        refuse("REFUSED_UNKNOWN_PROFILE", profile)
    selected = tuple(PROFILES[profile] if services is None else services)
    if not selected:
        refuse("REFUSED_MISSING_SERVICE", "empty service selection")
    for service in selected:
        if service not in SERVICES or service not in PROFILES[profile]:
            refuse("REFUSED_MISSING_SERVICE", service)
    for module in imports:
        root = str(module).split(".")[0]
        if root in NETWORK_MODULES:
            refuse("REFUSED_NETWORK", module)
        if root not in PERMITTED_IMPORTS:
            refuse("REFUSED_INVALID_MANIFEST", f"undeclared import: {module}")
    endpoints = [{"service": service, **SERVICES[service]} for service in sorted(selected)]
    return {
        "profile": profile,
        "transport": "in-process",
        "network": False,
        "services": sorted(selected),
        "endpoints": endpoints,
    }


__all__ = ["NETWORK_MODULES", "PERMITTED_IMPORTS", "PROFILES", "SERVICES", "profiles", "up"]
