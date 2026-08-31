from datetime import UTC, datetime

from veripay_analyst_api.clients import PipelineClient
from veripay_analyst_api.models import ScoreRequest, TransactionInput
from veripay_analyst_api.profiles import ProfileStore
from veripay_analyst_api.service import AnalystOrchestrator

_BASE = datetime(2026, 8, 10, tzinfo=UTC)


def _input(cc_num: int) -> TransactionInput:
    return TransactionInput(
        transaction_id=f"tx_{cc_num}",
        cc_num=cc_num,
        amount=100.0,
        merchant="m_amazon",
        category="ecommerce",
        timestamp=_BASE,
    )


def test_score_exposes_model_versions_and_fallbacks(fake_client: PipelineClient) -> None:
    response = AnalystOrchestrator(fake_client, ProfileStore()).score(
        ScoreRequest(transaction=_input(cc_num=101))
    )
    assert response.model_versions == {"supervised": "v1", "anomaly": "v1"}
    assert response.model_fallbacks == []


def test_score_records_unavailable_model_fallback(fake_client: PipelineClient) -> None:
    fake_client.supervised_score = lambda transaction_id, features: {  # type: ignore[method-assign]
        "fraud_probability": 0.2,
        "model_available": False,
        "fallback": True,
        "model_version": "fallback",
    }
    response = AnalystOrchestrator(fake_client, ProfileStore()).score(
        ScoreRequest(transaction=_input(cc_num=102))
    )
    assert response.model_available is False
    assert response.model_fallbacks == ["supervised"]