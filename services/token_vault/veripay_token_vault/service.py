"""PCI-safe token vault domain logic.

The service stores token metadata only. PAN and dCVV secrets must remain in an
external vault provider and are never accepted or returned by these models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field
from veripay_common.enums import DcvvStatus, TokenStatus, TokenType


class TokenRecord(BaseModel):
    """Non-sensitive token metadata exposed by the vault."""

    model_config = ConfigDict(use_enum_values=True)

    token_id: str = Field(min_length=1)
    merchant_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    token_type: TokenType
    status: TokenStatus = TokenStatus.ACTIVE
    expires_at: datetime
    max_uses: int | None = Field(default=None, ge=1)
    uses: int = Field(default=0, ge=0)


class TokenCreateRequest(BaseModel):
    token_id: str = Field(min_length=1)
    merchant_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    token_type: TokenType = TokenType.SINGLE_USE
    expires_at: datetime
    max_uses: int | None = Field(default=None, ge=1)


class DcvvValidationRequest(BaseModel):
    token_id: str = Field(min_length=1)
    provided_dcvv: str = Field(min_length=3, max_length=3, pattern=r"^[0-9]{3}$")
    expected_dcvv: str = Field(min_length=3, max_length=3, pattern=r"^[0-9]{3}$")


class DcvvValidationResponse(BaseModel):
    token_id: str
    status: DcvvStatus


class TokenRepository(Protocol):
    def save(self, token: TokenRecord) -> TokenRecord: ...

    def get(self, token_id: str) -> TokenRecord | None: ...

    def list(self) -> list[TokenRecord]: ...


@dataclass
class InMemoryTokenRepository:
    tokens: dict[str, TokenRecord] = field(default_factory=dict)

    def save(self, token: TokenRecord) -> TokenRecord:
        self.tokens[token.token_id] = token
        return token

    def get(self, token_id: str) -> TokenRecord | None:
        return self.tokens.get(token_id)

    def list(self) -> list[TokenRecord]:
        return list(self.tokens.values())


def is_usable(token: TokenRecord, now: datetime | None = None) -> bool:
    """Check lifecycle state without exposing sensitive vault material."""
    current_time = now or datetime.now(UTC)
    return (
        token.status == TokenStatus.ACTIVE
        and token.expires_at > current_time
        and (token.max_uses is None or token.uses < token.max_uses)
    )


def consume(token: TokenRecord, now: datetime | None = None) -> TokenRecord:
    """Consume one use, rejecting expired, revoked, or exhausted tokens."""
    if not is_usable(token, now):
        raise ValueError("Token is not usable")
    token.uses += 1
    if token.max_uses is not None and token.uses >= token.max_uses:
        token.status = TokenStatus.EXHAUSTED
    return token


def validate_dcvv(
    request: DcvvValidationRequest,
    repository: TokenRepository,
    now: datetime | None = None,
) -> DcvvValidationResponse:
    """Validate dCVV against an external-provider result supplied by the caller."""
    token = repository.get(request.token_id)
    if token is None or not is_usable(token, now):
        return DcvvValidationResponse(token_id=request.token_id, status=DcvvStatus.EXPIRED)
    result = (
        DcvvStatus.MATCH if request.provided_dcvv == request.expected_dcvv else DcvvStatus.MISMATCH
    )
    return DcvvValidationResponse(token_id=request.token_id, status=result)
