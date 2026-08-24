"""Canonical enums shared across services (mirror proto/veripay).

Single source of truth for string values flowing between services. Proto
definitions remain authoritative for the wire format; these enums are the
ergonomic Python mirror used inside services.
"""

from __future__ import annotations

from enum import StrEnum


class Mti(StrEnum):
    AUTHORIZATION_REQUEST = "0100"
    AUTHORIZATION_RESPONSE = "0110"
    AUTHORIZATION_REVERSAL = "0400"


class Channel(StrEnum):
    CARD_PRESENT = "CARD_PRESENT"
    CARD_NOT_PRESENT = "CARD_NOT_PRESENT"


class TokenType(StrEnum):
    SINGLE_USE = "SINGLE_USE"
    MERCHANT_LOCKED = "MERCHANT_LOCKED"
    SUBSCRIPTION = "SUBSCRIPTION"
    DYNAMIC_CVV = "DYNAMIC_CVV"


class DcvvStatus(StrEnum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    EXPIRED = "EXPIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TokenStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXHAUSTED = "EXHAUSTED"
    REVOKED = "REVOKED"


class DecisionAction(StrEnum):
    ALLOW = "ALLOW"
    MONITOR = "MONITOR"
    CHALLENGE = "CHALLENGE"
    REVIEW = "REVIEW"
    DECLINE = "DECLINE"
    REVERSE = "REVERSE"


class RiskBand(StrEnum):
    APPROVE = "APPROVE"
    VERIFY = "VERIFY"
    BLOCK = "BLOCK"


class GpvOutcome(StrEnum):
    MATCHED = "MATCHED"
    LIKELY_MATCH = "LIKELY_MATCH"
    MISMATCHED = "MISMATCHED"


class DevicePlatform(StrEnum):
    IOS = "ios"
    ANDROID = "android"


class DeviceTrustState(StrEnum):
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"
    UNKNOWN = "UNKNOWN"
