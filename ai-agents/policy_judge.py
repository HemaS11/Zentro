
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class PolicyJudgeResult:
    agent: str = "Policy Judge"
    decision: str = "REVIEW"
    confidence: float = 0.0
    risk_score: int = 0
    matched_policy: str = "Not evaluated"
    notes: str = ""


class PolicyJudge:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model = self.config.get("model", "gemini-3.5-flash")

    def _as_float(self, value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _as_date(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d %b %Y"):
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        return None

    def evaluate(self, transaction: Dict[str, Any]) -> PolicyJudgeResult:
        mandate = transaction.get("mandate") or transaction.get("policy") or {}
        if not mandate:
            return PolicyJudgeResult(
                decision="REVIEW",
                confidence=0.65,
                risk_score=30,
                matched_policy="unknown",
                notes="Insufficient policy information provided. The spending mandate, category permissions, spending limits, and seller verification requirements are missing.",
            )

        amount = self._as_float(transaction.get("amount"))
        category = str(transaction.get("category") or "Unknown").lower()
        merchant = str(transaction.get("merchant") or transaction.get("vendor") or "Unknown").lower()
        monthly_limit = self._as_float(mandate.get("monthly_limit"))
        single_limit = self._as_float(mandate.get("single_purchase_limit"))
        approval_threshold = self._as_float(mandate.get("approval_threshold"))
        allowed_categories = [str(item).lower() for item in mandate.get("allowed_categories", [])]
        expiry = self._as_date(mandate.get("expiry_date"))
        verified_required = bool(mandate.get("verified_seller_only"))

        notes = []
        decision = "APPROVE"
        risk_score = 0
        confidence = 0.9

        if allowed_categories and category not in allowed_categories:
            decision = "BLOCK"
            risk_score = 85
            notes.append(f"Category '{transaction.get('category')}' is not permitted by the active mandate.")
        if monthly_limit is not None and amount is not None and amount > monthly_limit:
            decision = "BLOCK"
            risk_score = max(risk_score, 90)
            notes.append(f"Transaction amount exceeds the monthly limit of {monthly_limit}.")
        if single_limit is not None and amount is not None and amount > single_limit:
            decision = "ESCALATE"
            risk_score = max(risk_score, 70)
            notes.append(f"Single-purchase limit is exceeded at {amount} compared with {single_limit}.")
        if verified_required and ("verified" not in merchant and "trusted" not in merchant and transaction.get("seller_verified") is not True):
            decision = "ESCALATE"
            risk_score = max(risk_score, 65)
            notes.append("Seller verification is required but the transaction data does not confirm it.")
        if approval_threshold is not None and amount is not None and amount >= approval_threshold:
            decision = "ESCALATE"
            risk_score = max(risk_score, 60)
            notes.append(f"Approval threshold of {approval_threshold} is reached, requiring human review.")
        if expiry is not None and datetime.utcnow() > expiry:
            decision = "BLOCK"
            risk_score = max(risk_score, 80)
            notes.append("Mandate has expired.")

        if not notes:
            notes.append("All available mandate checks passed; the decision remains advisory and does not authorize a payment.")
        if decision == "APPROVE" and risk_score < 15:
            confidence = 0.94
        elif decision in {"ESCALATE", "REVIEW"}:
            confidence = 0.8
        else:
            confidence = 0.88

        return PolicyJudgeResult(
            decision=decision,
            confidence=max(0.0, min(1.0, confidence)),
            risk_score=max(0, min(100, risk_score)),
            matched_policy=str(mandate.get("name") or "Policy Controls"),
            notes=" ".join(notes),
        )
