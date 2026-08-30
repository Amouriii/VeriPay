"""Tests for veripay_common.privacy — PII redaction boundary."""

from veripay_common.privacy import DeterministicPiiRedactor


def test_sensitive_keys_are_tokenized():
    redactor = DeterministicPiiRedactor()
    result = redactor.redact(
        {
            "pan": "4111111111111111",
            "cvv": "123",
            "amount": 99.5,
        }
    )
    assert result.payload["pan"].startswith("tok_")
    assert result.payload["cvv"].startswith("tok_")
    # Non-sensitive values pass through untouched
    assert result.payload["amount"] == 99.5
    assert set(result.redacted_fields) == {"pan", "cvv"}


def test_tokenization_is_deterministic():
    redactor = DeterministicPiiRedactor()
    a = redactor.redact({"card_number": "4111-1111-1111-1111"})
    b = redactor.redact({"card_number": "4111-1111-1111-1111"})
    assert a.payload["card_number"] == b.payload["card_number"]


def test_different_values_get_different_tokens():
    redactor = DeterministicPiiRedactor()
    result = redactor.redact({"pan": "4111111111111111", "name": "4111111111111112"})
    assert result.payload["pan"] != result.payload["name"]


def test_nested_structures_are_walked():
    redactor = DeterministicPiiRedactor()
    result = redactor.redact(
        {
            "transaction": {
                "amount": 50,
                "card": {"pan": "4111111111111111"},
            },
            "devices": [{"device_id": "abc"}, {"device_id": "def"}],
        }
    )
    assert result.payload["transaction"]["card"]["pan"].startswith("tok_")
    assert result.payload["transaction"]["amount"] == 50
    for item in result.payload["devices"]:
        assert item["device_id"].startswith("tok_")
    assert "transaction.card.pan" in result.redacted_fields
    assert "devices[0].device_id" in result.redacted_fields


def test_namespaced_namespaces_change_tokens():
    a = DeterministicPiiRedactor(namespace="ns1").redact({"pan": "X"}).payload["pan"]
    b = DeterministicPiiRedactor(namespace="ns2").redact({"pan": "X"}).payload["pan"]
    assert a != b


def test_no_sensitive_key_patterns_missed():
    redactor = DeterministicPiiRedactor()
    keys = [
        "pan",
        "primary_account",
        "card_number",
        "cvv",
        "dcvv",
        "first_name",
        "billing_address",
        "national_id",
        "ssn",
        "ip",
        "payment_instrument",
        "credential",
        "secret",
        "token",
    ]
    payload = {key: "value-" + key for key in keys}
    result = redactor.redact(payload)
    for key in keys:
        assert result.payload[key].startswith("tok_"), f"{key} was not tokenized"
    assert len(result.redacted_fields) == len(keys)


def test_empty_payload():
    redactor = DeterministicPiiRedactor()
    result = redactor.redact({})
    assert result.payload == {}
    assert result.redacted_fields == []
    assert result.tokenization_version == "deterministic-v1"
