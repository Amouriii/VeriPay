"""Authenticated role enforcement for the Business Portal boundary.

Expansion §1 item 6: portal endpoints previously described required roles via
``/access-policy`` but did not enforce identity. This module closes that gap
behind an injectable ``TokenAuthenticator`` protocol so the production
identity provider (OIDC introspection, JWT validation, etc.) can be wired in
without touching route code.

Enforcement model:
- Requests must carry ``Authorization: Bearer <token>``; anything else is 401.
- The authenticator resolves the token to a set of roles (and a subject).
- Endpoints declare required roles; a token holding none of them is 403.
- Fail-closed: an authenticator error or empty role set denies access.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class AuthError(Exception):
    """Raised when a request fails authentication or role authorization."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass(frozen=True)
class AuthIdentity:
    """Resolved caller identity for one request."""

    subject: str
    roles: frozenset[str]


class TokenAuthenticator(Protocol):
    """Resolve a bearer token to an identity. Raise AuthError to deny."""

    def authenticate(self, token: str) -> AuthIdentity: ...


class ConfigTokenAuthenticator:
    """Static-token authenticator for local development and tests.

    Tokens are configured via ``BUSINESS_AUTH_TOKENS`` as a comma-separated
    ``<token>:<role1|role2>`` map, e.g.::

        BUSINESS_AUTH_TOKENS="dev-admin:BUSINESS_ADMIN|MERCHANT_ADMIN,dev-merchant:MERCHANT_ADMIN"

    Production must replace this with a real identity provider (OIDC token
    introspection or signed-JWT validation) via ``TokenAuthenticator``.
    """

    def __init__(self, token_map: dict[str, frozenset[str]] | None = None) -> None:
        if token_map is not None:
            self._tokens = token_map
        else:
            self._tokens = _parse_token_map(os.getenv("BUSINESS_AUTH_TOKENS", ""))

    def authenticate(self, token: str) -> AuthIdentity:
        roles = self._tokens.get(token)
        if roles is None:
            raise AuthError(401, "Invalid or expired bearer token")
        return AuthIdentity(subject="config-token", roles=roles)


def _parse_token_map(raw: str) -> dict[str, frozenset[str]]:
    """Parse ``token:ROLE_A|ROLE_B,token2:ROLE_C`` into a lookup map."""
    result: dict[str, frozenset[str]] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        token, _, roles_part = entry.partition(":")
        token = token.strip()
        roles = frozenset(role.strip() for role in roles_part.split("|") if role.strip())
        if token and roles:
            result[token] = roles
    return result


def extract_bearer_token(authorization: str | None) -> str:
    """Extract the token from an ``Authorization: Bearer <token>`` header."""
    if not authorization:
        raise AuthError(401, "Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthError(401, "Authorization header must be 'Bearer <token>'")
    return token.strip()


def require_roles(
    authorization: str | None,
    authenticator: TokenAuthenticator,
    required_roles: set[str],
) -> AuthIdentity:
    """Authenticate the request and enforce at least one required role.

    Raises :class:`AuthError` (401 for auth failures, 403 for role mismatch).
    Fails closed when the identity carries no roles.
    """
    token = extract_bearer_token(authorization)
    identity = authenticator.authenticate(token)
    if not identity.roles or not (identity.roles & required_roles):
        raise AuthError(403, f"Requires one of roles: {sorted(required_roles)}")
    return identity


__all__ = [
    "AuthError",
    "AuthIdentity",
    "ConfigTokenAuthenticator",
    "TokenAuthenticator",
    "extract_bearer_token",
    "require_roles",
]
