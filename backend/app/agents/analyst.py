from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.config import Settings


class AnalystProposal(BaseModel):
    thesis: str = Field(min_length=12)
    evidence: list[str] = Field(min_length=2, max_length=6)
    invalidation_condition: str = Field(min_length=8)
    expected_holding_period: str = Field(min_length=3)
    confidence_score: float = Field(ge=0, le=1)


class CriticResult(BaseModel):
    passed: bool
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AgentReview(BaseModel):
    analyst: AnalystProposal
    critic: CriticResult
    source: str


def analyze_and_critique(
    proposal: dict[str, Any],
    market_candidate: dict[str, Any] | None,
    settings: Settings,
) -> AgentReview:
    if settings.demo_mode or not settings.has_agent_credentials:
        analyst = _deterministic_analyst(proposal, market_candidate)
        return AgentReview(analyst=analyst, critic=critique(proposal, market_candidate, analyst), source="deterministic")

    try:
        analyst = _model_analyst(proposal, market_candidate, settings)
    except (httpx.HTTPError, ValidationError, ValueError, KeyError, TypeError):
        analyst = _deterministic_analyst(proposal, market_candidate)
        return AgentReview(analyst=analyst, critic=critique(proposal, market_candidate, analyst), source="fallback")

    return AgentReview(analyst=analyst, critic=critique(proposal, market_candidate, analyst), source=settings.agent_model)


def critique(
    proposal: dict[str, Any],
    market_candidate: dict[str, Any] | None,
    analyst: AnalystProposal,
) -> CriticResult:
    blocking_reasons: list[str] = []
    warnings: list[str] = []
    direction = proposal.get("direction")
    strategy_type = proposal.get("strategy_type", "")
    reasons = market_candidate.get("reason_codes", []) if market_candidate else []

    if direction not in {"bullish", "bearish"}:
        blocking_reasons.append("missing_or_invalid_direction")
    if not proposal.get("legs"):
        blocking_reasons.append("missing_option_legs")
    if direction == "bullish" and strategy_type not in {"bull_call_debit_spread", "long_call"}:
        blocking_reasons.append("strategy_does_not_match_bullish_signal")
    if direction == "bearish" and strategy_type not in {"bear_put_debit_spread", "long_put"}:
        blocking_reasons.append("strategy_does_not_match_bearish_signal")
    if analyst.confidence_score < 0.35:
        blocking_reasons.append("analyst_confidence_too_low")
    if len(analyst.evidence) < 2:
        blocking_reasons.append("insufficient_evidence")
    if market_candidate and market_candidate.get("direction") not in {direction, None}:
        blocking_reasons.append("signal_direction_contradicts_proposal")
    if market_candidate and not reasons:
        warnings.append("market_candidate_has_no_reason_codes")
    if "weak_directional_edge" in reasons:
        warnings.append("scanner_flagged_weak_directional_edge")

    return CriticResult(
        passed=not blocking_reasons,
        blocking_reasons=blocking_reasons,
        warnings=warnings,
    )


def _deterministic_analyst(
    proposal: dict[str, Any],
    market_candidate: dict[str, Any] | None,
) -> AnalystProposal:
    symbol = proposal.get("underlying_symbol", "the underlying")
    direction = proposal.get("direction", "directional")
    strategy = proposal.get("strategy_type", "defined-risk option structure")
    reasons = market_candidate.get("reason_codes", []) if market_candidate else []
    feature_summary = _feature_summary(market_candidate or {})
    evidence = [
        f"Scanner direction is {direction} for {symbol}.",
        f"Selected structure is {strategy} with max loss capped at {proposal.get('max_loss')}.",
    ]
    if reasons:
        evidence.append(f"Reason codes: {', '.join(reasons[:3])}.")
    if feature_summary:
        evidence.append(feature_summary)

    return AnalystProposal(
        thesis=f"{symbol} has enough structured {direction} evidence to justify a small defined-risk paper trade.",
        evidence=evidence[:6],
        invalidation_condition="Reject or exit if the scanner direction flips, option quotes stale, or risk limits fail.",
        expected_holding_period="1 to 5 trading days",
        confidence_score=0.62 if reasons else 0.45,
    )


def _model_analyst(
    proposal: dict[str, Any],
    market_candidate: dict[str, Any] | None,
    settings: Settings,
) -> AnalystProposal:
    url = settings.agent_base_url.rstrip("/") + "/chat/completions"
    messages = [
        {
            "role": "system",
            "content": (
                "You are a cautious options analyst. Return strict JSON only with keys "
                "thesis, evidence, invalidation_condition, expected_holding_period, confidence_score. "
                "Do not include executable order payloads."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {"proposal": proposal, "market_candidate": market_candidate},
                sort_keys=True,
                default=str,
            ),
        },
    ]
    response = httpx.post(
        url,
        headers={"Authorization": f"Bearer {settings.agent_api_key}"},
        json={"model": settings.agent_model, "messages": messages, "temperature": 0.2},
        timeout=20,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return AnalystProposal.model_validate_json(content)


def _feature_summary(candidate: dict[str, Any]) -> str | None:
    features = candidate.get("features") or {}
    if not features:
        return None
    return (
        "Features include "
        f"1-day return {features.get('one_day_return_pct')}%, "
        f"5-day return {features.get('five_day_return_pct')}%, "
        f"volume ratio {features.get('volume_ratio')}, "
        f"and quote freshness {features.get('quote_fresh')}."
    )
