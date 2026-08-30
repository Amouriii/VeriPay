"""Merchant-specific policy rules and evaluation. Expansion §1 Dev4, §2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field


class MerchantLockRule(BaseModel):
    lock_id: str = Field(default_factory=lambda: f"lock_{uuid4().hex}", min_length=1)
    merchant_id: str = Field(min_length=1)
    allowed_mccs: str | None = None
    max_spend_per_txn_minor: int | None = Field(default=None, ge=0)
    daily_spend_limit_minor: int | None = Field(default=None, ge=0)
    velocity_limit_5m: int | None = Field(default=None, ge=1)
    enforce_merchant_lock: bool = True


class PolicyEvaluationRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    merchant_id: str = Field(min_length=1)
    mcc: str = Field(min_length=1)
    amount_minor: int = Field(ge=0)
    daily_spend_minor: int = Field(default=0, ge=0)
    velocity_count_5m: int = Field(default=0, ge=0)


class PolicyFinding(BaseModel):
    code: str
    triggered: bool
    reason: str


class PolicyEvaluationResponse(BaseModel):
    transaction_id: str
    merchant_id: str
    allowed: bool
    rule_id: str | None = None
    findings: list[PolicyFinding]


class MerchantPolicyRepository(Protocol):
    def save(self, rule: MerchantLockRule) -> MerchantLockRule: ...

    def list(self) -> list[MerchantLockRule]: ...

    def get(self, lock_id: str) -> MerchantLockRule | None: ...

    def delete(self, lock_id: str) -> bool: ...


@dataclass
class InMemoryMerchantPolicyRepository:
    rules: dict[str, MerchantLockRule] = field(default_factory=dict)

    def save(self, rule: MerchantLockRule) -> MerchantLockRule:
        self.rules[rule.lock_id] = rule
        return rule

    def list(self) -> list[MerchantLockRule]:
        return list(self.rules.values())

    def get(self, lock_id: str) -> MerchantLockRule | None:
        return self.rules.get(lock_id)

    def delete(self, lock_id: str) -> bool:
        return self.rules.pop(lock_id, None) is not None


def _select_rule(repository: MerchantPolicyRepository, merchant_id: str) -> MerchantLockRule | None:
    rules = [rule for rule in repository.list() if rule.merchant_id == merchant_id]
    if not rules:
        return None
    return sorted(rules, key=lambda rule: rule.lock_id)[-1]


def evaluate_policy(
    request: PolicyEvaluationRequest, repository: MerchantPolicyRepository
) -> PolicyEvaluationResponse:
    rule = _select_rule(repository, request.merchant_id)
    if rule is None:
        return PolicyEvaluationResponse(
            transaction_id=request.transaction_id,
            merchant_id=request.merchant_id,
            allowed=True,
            findings=[
                PolicyFinding(
                    code="NO_POLICY", triggered=False, reason="No merchant policy configured"
                )
            ],
        )
    if not rule.enforce_merchant_lock:
        return PolicyEvaluationResponse(
            transaction_id=request.transaction_id,
            merchant_id=request.merchant_id,
            allowed=True,
            rule_id=rule.lock_id,
            findings=[
                PolicyFinding(
                    code="POLICY_DISABLED", triggered=False, reason="Merchant policy is disabled"
                )
            ],
        )

    allowed_mccs = {
        value.strip() for value in (rule.allowed_mccs or "").split(",") if value.strip()
    }
    findings = [
        PolicyFinding(
            code="MCC_RESTRICTED",
            triggered=bool(allowed_mccs) and request.mcc not in allowed_mccs,
            reason=(
                "MCC is not allowed"
                if allowed_mccs and request.mcc not in allowed_mccs
                else "MCC allowed"
            ),
        ),
        PolicyFinding(
            code="TRANSACTION_LIMIT",
            triggered=(
                rule.max_spend_per_txn_minor is not None
                and request.amount_minor > rule.max_spend_per_txn_minor
            ),
            reason=(
                "Transaction limit exceeded"
                if rule.max_spend_per_txn_minor is not None
                and request.amount_minor > rule.max_spend_per_txn_minor
                else "Transaction limit not exceeded"
            ),
        ),
        PolicyFinding(
            code="DAILY_LIMIT",
            triggered=(
                rule.daily_spend_limit_minor is not None
                and request.daily_spend_minor + request.amount_minor > rule.daily_spend_limit_minor
            ),
            reason=(
                "Daily spend limit exceeded"
                if rule.daily_spend_limit_minor is not None
                and request.daily_spend_minor + request.amount_minor > rule.daily_spend_limit_minor
                else "Daily spend limit not exceeded"
            ),
        ),
        PolicyFinding(
            code="VELOCITY_LIMIT",
            triggered=(
                rule.velocity_limit_5m is not None
                and request.velocity_count_5m > rule.velocity_limit_5m
            ),
            reason=(
                "Five-minute merchant velocity limit exceeded"
                if rule.velocity_limit_5m is not None
                and request.velocity_count_5m > rule.velocity_limit_5m
                else "Merchant velocity limit not exceeded"
            ),
        ),
    ]
    return PolicyEvaluationResponse(
        transaction_id=request.transaction_id,
        merchant_id=request.merchant_id,
        allowed=not any(finding.triggered for finding in findings),
        rule_id=rule.lock_id,
        findings=findings,
    )
