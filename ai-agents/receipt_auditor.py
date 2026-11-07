
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ReceiptAuditorResult:
    agent: str = "Receipt Auditor"
    decision: str = "REVIEW"
    confidence: float = 0.0
    risk_score: int = 0
    matched_policy: str = "Not evaluated"
    notes: str = ""


class ReceiptAuditor:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model = self.config.get("model", "gemini-3.8-flash")

    def _to_float(self, value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def evaluate(self, transaction: Dict[str, Any]) -> ReceiptAuditorResult:
        receipt = transaction.get("receipt") or {}
        amount_expected = self._to_float(transaction.get("amount"))
        amount_receipt = self._to_float(receipt.get("amount") or receipt.get("total") or receipt.get("receipt_amount"))
        merchant = str(transaction.get("merchant") or transaction.get("vendor") or "").strip().lower()
        receipt_merchant = str(receipt.get("merchant") or receipt.get("vendor") or "").strip().lower()
        reference_expected = str(transaction.get("paymentReference") or transaction.get("reference") or "").strip()
        reference_receipt = str(receipt.get("reference") or receipt.get("payment_reference") or "").strip()
        notes = []
        risk_score = 0

        if amount_expected is not None and amount_receipt is not None and abs(amount_expected - amount_receipt) > 0.01:
            risk_score += 50
            notes.append("Receipt amount differs from the payment record amount.")
        if not receipt:
            risk_score += 25
            notes.append("Actual receipt or verified payment record is missing.")
        if merchant and receipt_merchant and merchant != receipt_merchant:
            risk_score += 30
            notes.append("Merchant name on the receipt does not match the transaction merchant.")
        if reference_expected and reference_receipt and reference_expected != reference_receipt:
            risk_score += 20
            notes.append("Receipt reference does not match the transaction reference.")
        if receipt.get("duplicate") or transaction.get("duplicate_receipt"):
            risk_score += 15
            notes.append("Duplicate receipt indicator is present.")

        if risk_score >= 70:
            decision = "BLOCK"
            confidence = 0.82
        elif risk_score >= 35:
            decision = "REVIEW"
            confidence = 0.7
        elif not receipt:
            decision = "REVIEW"
            confidence = 0.65
        else:
            decision = "APPROVE"
            confidence = 0.9

        if not notes:
            notes.append("Receipt data aligns with the transaction record and no material mismatch was found.")

        return ReceiptAuditorResult(
            decision=decision,
            confidence=max(0.0, min(1.0, confidence)),
            risk_score=max(0, min(100, risk_score)),
            matched_policy="Receipt Verification",
            notes=" ".join(notes),
        )
