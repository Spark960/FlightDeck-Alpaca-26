from app.agents.analyst import AnalystProposal, analyze_and_critique, critique
from app.config import Settings


def _proposal(**overrides) -> dict:
    base = {
        "underlying_symbol": "SPY",
        "direction": "bullish",
        "strategy_type": "bull_call_debit_spread",
        "max_loss": 255.0,
        "legs": [{"side": "buy"}, {"side": "sell"}],
    }
    base.update(overrides)
    return base


def _market_candidate(**overrides) -> dict:
    base = {
        "symbol": "SPY",
        "direction": "bullish",
        "reason_codes": ["positive_intraday_momentum", "liquid_recent_volume"],
    }
    base.update(overrides)
    return base


def test_analyst_generates_structured_review_in_demo_mode():
    settings = Settings(demo_mode=True, agent_api_key=None)
    review = analyze_and_critique(_proposal(), _market_candidate(), settings)
    assert review.source == "deterministic"
    assert len(review.analyst.evidence) >= 2
    assert 0 <= review.analyst.confidence_score <= 1


def test_critic_passes_aligned_proposal():
    analyst = AnalystProposal(
        thesis="SPY shows bullish momentum with defined-risk spread structure.",
        evidence=["Scanner direction is bullish.", "Spread caps max loss at 255."],
        invalidation_condition="Exit if direction flips or quotes stale.",
        expected_holding_period="1 to 5 trading days",
        confidence_score=0.7,
    )
    result = critique(_proposal(), _market_candidate(), analyst)
    assert result.passed is True
    assert result.blocking_reasons == []


def test_critic_rejects_weak_proposal():
    analyst = AnalystProposal(
        thesis="Weak thesis without enough support for this trade.",
        evidence=["Only one meaningful point.", "Another thin point."],
        invalidation_condition="Unknown invalidation path.",
        expected_holding_period="1 day",
        confidence_score=0.2,
    )
    result = critique(
        _proposal(direction="bearish", strategy_type="bull_call_debit_spread"),
        _market_candidate(direction="bullish"),
        analyst,
    )
    assert result.passed is False
    assert "strategy_does_not_match_bearish_signal" in result.blocking_reasons
    assert "analyst_confidence_too_low" in result.blocking_reasons
