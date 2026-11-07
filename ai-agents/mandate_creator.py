
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from google import genai
except Exception:  # pragma: no cover
    genai = None


DEFAULT_MANDATE = {
    "allowed_categories": [],
    "monthly_limit": None,
    "single_purchase_limit": None,
    "verified_seller_only": None,
    "approval_threshold": None,
    "expiry_date": None,
    "additional_rules": [],
    "clarification_required": False,
    "clarification_question": None,
}


@dataclass
class MandateCreatorResult:
    agent: str = "Mandate Creator"
    decision: str = "REVIEW"
    confidence: float = 0.0
    risk_score: int = 0
    matched_policy: str = "Mandate Creation"
    notes: str = ""
    mandate: Optional[Dict[str, Any]] = None


class MandateCreator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = self.config.get("gemini_api_key", "")
        self.model = self.config.get("model", "gemini-3.8-flash")
        self.client = genai.Client(api_key=self.api_key) if self.api_key and genai else None

    def _extract_amount(self, text: str, *keywords: str) -> Optional[float]:
        pattern = re.compile(r"(?:\d+(?:,\d{3})*(?:\.\d+)?)")
        lower = text.lower()
        for keyword in keywords:
            if keyword in lower:
                match = re.search(rf"{re.escape(keyword)}[^\n\r]*?(\d+(?:,\d{3})*(?:\.\d+)?)", lower)
                if match:
                    value = match.group(1).replace(",", "")
                    return float(value)
        matches = pattern.findall(text)
        if not matches:
            return None
        value = matches[0].replace(",", "")
        return float(value)

    def _parse_mandate_text(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if not cleaned:
            return {**DEFAULT_MANDATE}

        lower_text = cleaned.lower()
        categories: List[str] = []
        category_keywords = {
            "technology": "Technology",
            "software": "Software",
            "travel": "Travel",
            "office": "Office",
            "wellness": "Wellness",
            "dining": "Dining",
            "shopping": "Shopping",
            "entertainment": "Entertainment",
            "education": "Education",
            "marketing": "Marketing",
            "cloud": "Technology",
            "hardware": "Technology",
            "laptop": "Technology",
        }
        for keyword, mapped in category_keywords.items():
            if keyword in lower_text and mapped not in categories:
                categories.append(mapped)

        monthly_limit = self._extract_amount(cleaned, "monthly", "per month", "month budget")
        single_limit = self._extract_amount(cleaned, "single purchase", "per purchase", "purchase limit", "any purchase")
        approval_threshold = self._extract_amount(cleaned, "requires human approval", "approval threshold", "approval if above", "approval above")
        expiry_date = None
        for match in re.finditer(r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{1,2} [A-Za-z]+ \d{4})", cleaned):
            candidate = match.group(1)
            try:
                datetime.strptime(candidate, "%Y-%m-%d")
                expiry_date = candidate
                break
            except ValueError:
                try:
                    datetime.strptime(candidate, "%d/%m/%Y")
                    expiry_date = candidate
                    break
                except ValueError:
                    try:
                        datetime.strptime(candidate, "%d %b %Y")
                        expiry_date = candidate
                        break
                    except ValueError:
                        continue

        verified_seller_only = None
        if "verified sellers only" in lower_text or "only verified sellers" in lower_text or "verified seller" in lower_text:
            verified_seller_only = True
        elif "allow unverified sellers" in lower_text or "unverified sellers allowed" in lower_text:
            verified_seller_only = False

        additional_rules = []
        for sentence in re.split(r"[.;\n]+", cleaned):
            stripped = sentence.strip()
            if not stripped:
                continue
            if any(token in lower_text for token in ["allow", "monthly", "single purchase", "verified", "approval", "human approval"]) and stripped.lower() not in {"allow", "allow monthly", "allow monthly technology spending", "technology spending"}:
                if not any(token in stripped.lower() for token in ["allow", "monthly", "single purchase", "verified", "approval", "human approval"]):
                    additional_rules.append(stripped)

        ambiguous = any(term in lower_text for term in ["reasonable", "as needed", "flexible", "whenever needed", "sufficient", "some expense"]) or "?" in cleaned

        mandate = {
            **DEFAULT_MANDATE,
            "allowed_categories": categories,
            "monthly_limit": monthly_limit,
            "single_purchase_limit": single_limit,
            "verified_seller_only": verified_seller_only,
            "approval_threshold": approval_threshold,
            "expiry_date": expiry_date,
            "additional_rules": additional_rules,
            "clarification_required": ambiguous or not cleaned,
        }
        if mandate["clarification_required"]:
            mandate["clarification_question"] = "Please confirm the exact monthly ceiling, single-purchase cap, and any category restrictions you want enforced."
        else:
            mandate["clarification_question"] = None

        return mandate

    def _validate_mandate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {**DEFAULT_MANDATE}
        for key in DEFAULT_MANDATE:
            if key in data:
                normalized[key] = data[key]
        if isinstance(normalized["additional_rules"], str):
            normalized["additional_rules"] = [normalized["additional_rules"]]
        if not isinstance(normalized["allowed_categories"], list):
            normalized["allowed_categories"] = []
        normalized["clarification_required"] = bool(normalized.get("clarification_required", False))
        normalized["clarification_question"] = normalized.get("clarification_question") or None
        return normalized

    def _run_model(self, mandate_text: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        prompt = f"""
You are Zentro's Mandate Creator agent.
Convert this mandate into valid JSON using this schema:
{json.dumps(DEFAULT_MANDATE, indent=2)}

Mandate text:
{mandate_text}

Rules:
- Use null for missing values.
- Use booleans for yes/no settings.
- Return ONLY JSON, no markdown.
- Never invent unsupported limits.
- When uncertain, set clarification_required to true and ask a clear question.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.2},
            )
            raw_text = getattr(response, "text", "")
            if not raw_text:
                return None
            text = raw_text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(text)
        except Exception:
            return None

    def evaluate(self, transaction: Dict[str, Any]) -> MandateCreatorResult:
        mandate_text = (
            transaction.get("mandate_text")
            or transaction.get("instruction")
            or transaction.get("mandate")
        )
        if not isinstance(mandate_text, str) or not mandate_text.strip():
            return MandateCreatorResult(
                decision="REVIEW",
                confidence=0.0,
                risk_score=0,
                matched_policy="Mandate Creation",
                notes="Please provide a natural-language spending mandate.",
                mandate={**DEFAULT_MANDATE},
            )

        parsed = self._parse_mandate_text(mandate_text)
        model_data = self._run_model(mandate_text)
        final_mandate = self._validate_mandate({**parsed, **(model_data or {})})
        requires_clarification = bool(final_mandate.get("clarification_required"))

        return MandateCreatorResult(
            decision="REVIEW" if requires_clarification else "APPROVE",
            confidence=0.92 if not requires_clarification else 0.74,
            risk_score=5 if requires_clarification else 0,
            matched_policy="Mandate Creation",
            notes=(
                "Mandate parsed and validated successfully."
                if not requires_clarification
                else final_mandate.get("clarification_question") or "Mandate needs clarification before enforcement."
            ),
            mandate=final_mandate,
        )
