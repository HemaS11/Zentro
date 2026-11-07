
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RiskAgentResult:
    agent: str = "Risk Detection"
    decision: str = "REVIEW"
    confidence: float = 0.0
    risk_score: int = 0
    matched_policy: str = "Not evaluated"
    notes: str = ""


class RiskAgent:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model = self.config.get("model", "gemini-3.8-flash")

    def _to_float(self, value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def evaluate(self, transaction: Dict[str, Any]) -> RiskAgentResult:
        amount = self._to_float(transaction.get("amount")) or 0.0
        merchant = str(transaction.get("merchant") or transaction.get("vendor") or "Unknown").lower()
        status = str(transaction.get("status") or "unknown").lower()
        payment_reference = str(transaction.get("paymentReference") or transaction.get("reference") or "")
        history = transaction.get("history") or transaction.get("previous_transactions") or []
        score = 0
        indicators = []

        if amount >= 75000:
            score += 25
            indicators.append("Very high transaction value compared with the typical spend patterns.")
        if amount >= 150000:
            score += 15
            indicators.append("Extreme transaction amount triggers enhanced scrutiny.")
        if any(token in merchant for token in ["unknown", "suspicious", "generic", "test"]):
            score += 20
            indicators.append("Merchant information is weak or has suspicious naming patterns.")
        if payment_reference and any(entry.get("paymentReference") == payment_reference for entry in history):
            score += 20
            indicators.append("Duplicate payment reference appears in recent history.")
        if status in {"pending", "escalated"}:
            score += 10
            indicators.append("Transaction is already awaiting manual review.")
        if transaction.get("mandate") and transaction.get("mandate").get("verified_seller_only") and not transaction.get("seller_verified"):
            score += 15
            indicators.append("Verified seller is required but the seller status is not confirmed.")
        if not transaction.get("merchant") and not transaction.get("vendor"):
            score += 10
            indicators.append("Missing merchant data limits validation confidence.")

        score = max(0, min(100, score))
        if score >= 80:
            decision = "BLOCK"
        elif score >= 60:
            decision = "ESCALATE"
        elif score >= 30:
            decision = "REVIEW"
        else:
            decision = "APPROVE"

        confidence = 0.65 if score >= 60 else 0.77 if score >= 30 else 0.9
        return RiskAgentResult(
            decision=decision,
            confidence=confidence,
            risk_score=score,
            matched_policy="Risk Assessment",
            notes=" ".join(indicators) if indicators else "No material risk indicators were identified from the available transaction data.",
        )
