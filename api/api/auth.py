"""
EDDA API - Auth stub (NFR-009/010 extension point).
In dev: no auth or optional API key via X-API-Key header.
Replace with SAML 2.0 / LDAP middleware and RBAC (read, write, admin) for production.
"""
from __future__ import annotations

import os
from typing import Annotated

from fastapi import Header, HTTPException, status

# Set EDDA_API_KEY in env to require X-API-Key on protected routes. Leave unset for no auth (dev).
REQUIRE_API_KEY = bool(os.environ.get("EDDA_API_KEY"))


async def verify_api_key(x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None) -> str | None:
    """
    Dependency: if EDDA_API_KEY is set, require X-API-Key header to match.
    Use on routes that should be protected. When REQUIRE_API_KEY is false, always passes.
    """
    if not REQUIRE_API_KEY:
        return None
    expected = os.environ.get("EDDA_API_KEY", "")
    if not expected:
        return None
    if x_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return x_api_key
