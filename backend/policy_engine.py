import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from config import get_agent_config
except Exception:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai-agents"))
    from config import get_agent_config

SAFE_RULE_KEYS = {
    "max_transaction_amount",
    "allowed_categories",
    "blocked_categories",
    "allowed_days",
    "require_approval_above",
    "currency",
    "merchant_verification_required",
    "require_user_confirmation",
    "require_user_confirmation_for",
    "unknown_merchant_blocked",
    "expires_on",
    "seller_restrictions",
    "allow_unknown_merchants",
}

CATEGORY_ALIASES = {
    "electronics": "electronics",
    "tech": "electronics",
    "technology": "electronics",
    "food": "food",
    "restaurant": "food",
    "grocery": "food",
    "travel": "travel",
    "flight": "travel",
    "hotel": "travel",
    "furniture": "furniture",
    "office": "furniture",
    "software": "software",
    "subscription": "software",
    "medicine": "healthcare",
    "healthcare": "healthcare",
    "medical": "healthcare",
    "clothing": "clothing",
    "fashion": "clothing",
    "jewelry": "jewelry",
    "luxury": "jewelry",
    "books": "books",
    "education": "education",
}

VALID_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class PolicyValidationError(ValueError):
    """Raised when a mandate or purchase payload violates the policy schema."""


class MandateParsingError(PolicyValidationError):
    """Raised when live Gemini parsing fails or returns unusable data."""

    def __init__(self, message: str, error_type: str = "invalid_model_response", details: Optional[str] = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details


class PolicyMandateParser:
    def __init__(self, api_key: Optional[str] = None, gemini_client: Any = None):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY") or os.getenv("ZENTRO_GEMINI_API_KEY") or "").strip()
        self.gemini_client = gemini_client
        self.model = (
            os.getenv("GEMINI_MODEL")
            or get_agent_config().get("model")
            or "gemini-3.8-flash"
        ).strip()

    @staticmethod
    def _coerce_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.replace(",", "").replace("₹", "").replace("Rs", "").replace("INR", "").strip()
            if not cleaned:
                return None
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    @staticmethod
    def _normalize_string(value: Any) -> str:
        return str(value or "").strip()

    @staticmethod
    def _as_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @staticmethod
    def _normalize_day_list(values: Iterable[str]) -> List[str]:
        days: List[str] = []
        for item in values:
            candidate = str(item).strip()
            if not candidate:
                continue
            normalized = candidate.lower().capitalize()
            if normalized in {day.lower(): day for day in VALID_DAYS}.values():
                day_name = next(day for day in VALID_DAYS if day.lower() == normalized.lower())
                if day_name not in days:
                    days.append(day_name)
        return days

    @staticmethod
    def _normalize_category_list(values: Iterable[str]) -> List[str]:
        categories: List[str] = []
        for item in values:
            normalized = str(item).strip().lower()
            if not normalized:
                continue
            if normalized in CATEGORY_ALIASES:
                normalized = CATEGORY_ALIASES[normalized]
            if normalized not in categories:
                categories.append(normalized)
        return categories

    def _fallback_rules(self, mandate_text: str) -> Dict[str, Any]:
        text = mandate_text.strip()
        lower = text.lower()
        currency = "INR"
        if "usd" in lower or "$" in lower:
            currency = "USD"
        elif "eur" in lower or "€" in lower:
            currency = "EUR"

        rules: Dict[str, Any] = {
            "max_transaction_amount": None,
            "allowed_categories": [],
            "blocked_categories": [],
            "allowed_days": [],
            "require_approval_above": None,
            "currency": currency,
            "merchant_verification_required": False,
            "require_user_confirmation": False,
            "require_user_confirmation_for": [],
            "unknown_merchant_blocked": False,
            "allow_unknown_merchants": False,
            "expires_on": None,
            "seller_restrictions": [],
        }

        amount_matches = re.findall(r"(?:under|below|less than|not more than|never spend more than|max(?:imum)?(?:\s+allowed)?(?:\s+amount)?\s*[:=]?\s*|allow(?:ed)?(?:\s+spending)?\s*(?:up\s+to)?\s*)\(?₹?\s?(\d+(?:,\d{3})*(?:\.\d+)?)", lower)
        if amount_matches:
            rules["max_transaction_amount"] = float(amount_matches[-1].replace(",", ""))
        else:
            for pattern in (
                r"(?:\bunder\b|\bbelow\b|\bless\s+than\b|\bnot\s+more\s+than\b)\s*₹?\s*(\d+(?:,\d{3})*(?:\.\d+)?)",
                r"(?:\bspend\s+more\s+than\b|\bmaximum\b)\s*₹?\s*(\d+(?:,\d{3})*(?:\.\d+)?)",
            ):
                match = re.search(pattern, lower)
                if match:
                    rules["max_transaction_amount"] = float(match.group(1).replace(",", ""))
                    break

        approval_match = re.search(r"(?:approval\s+(?:required|needed|above)|requires?\s+human\s+approval(?:\s+above)?|approval\s+threshold\s*[:=]?\s*)(\d+(?:,\d{3})*(?:\.\d+)?)", lower)
        if approval_match:
            rules["require_approval_above"] = float(approval_match.group(1).replace(",", ""))

        if "weekdays" in lower or "only during weekdays" in lower or "allow purchases only during weekdays" in lower:
            rules["allowed_days"] = [day for day in VALID_DAYS if day.lower() not in {"saturday", "sunday"}]
        elif "weekends" in lower:
            rules["allowed_days"] = ["Saturday", "Sunday"]

        if "unknown sellers" in lower or "unknown seller" in lower or "do not purchase anything from unknown sellers" in lower:
            rules["merchant_verification_required"] = True
            rules["unknown_merchant_blocked"] = True
            rules["require_user_confirmation"] = True
            rules["require_user_confirmation_for"] = ["unknown"]
            rules["allow_unknown_merchants"] = False

        if "verified seller" in lower or "verified sellers only" in lower or "only verified sellers" in lower:
            rules["merchant_verification_required"] = True

        if "food" in lower or "restaurant" in lower or "grocery" in lower:
            rules["allowed_categories"] = self._normalize_category_list(["food"])
        elif "electronics" in lower or "tech" in lower:
            rules["allowed_categories"] = self._normalize_category_list(["electronics"])
        elif "fashion" in lower or "clothing" in lower or "luxury" in lower:
            rules["allowed_categories"] = self._normalize_category_list(["clothing"])

        for category, canonical_name in CATEGORY_ALIASES.items():
            if category in lower and canonical_name not in rules["allowed_categories"]:
                rules["allowed_categories"].append(canonical_name)

        blocked_keywords = ["blocked", "forbidden", "disallow", "do not allow", "never buy", "cannot buy"]
        for keyword in ("jewelry", "luxury", "grocery", "travel"):
            if keyword in lower and keyword not in {"food", "electronics", "travel"}:
                rules["blocked_categories"].append(keyword)
        if any(keyword in lower for keyword in blocked_keywords):
            for category in rules["allowed_categories"]:
                if category not in rules["blocked_categories"]:
                    pass

        if "buy" in lower and "under" in lower and "₹" in text:
            rules["max_transaction_amount"] = self._coerce_float(re.search(r"₹?\s*(\d+(?:,\d{3})*(?:\.\d+)?)", text).group(1)) if re.search(r"₹?\s*(\d+(?:,\d{3})*(?:\.\d+)?)", text) else rules["max_transaction_amount"]

        # Support common monthly and per purchase natural-language cases.
        monthly_match = re.search(r"(?:monthly|per month)\s+(?:spending|budget|limit)?\s*(?:of|up to|under)?\s*₹?\s*(\d+(?:,\d{3})*(?:\.\d+)?)", lower)
        if monthly_match:
            rules["max_transaction_amount"] = float(monthly_match.group(1).replace(",", ""))

        # handle explicit exclude/allow statements gracefully.
        if "allow purchases only during weekdays" in lower:
            rules["allowed_days"] = [day for day in VALID_DAYS if day not in {"Saturday", "Sunday"}]

        if not rules["allowed_days"] and "weekday" in lower or "weekdays" in lower:
            rules["allowed_days"] = [day for day in VALID_DAYS if day not in {"Saturday", "Sunday"}]

        if "food purchases only" in lower:
            rules["allowed_categories"] = ["food"]

        return rules

    @staticmethod
    def _normalize_response(raw_response: Any) -> Dict[str, Any]:
        if raw_response is None:
            return {}
        text = str(raw_response).strip()
        if not text:
            return {}
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return {}
        if isinstance(payload, list):
            if payload and isinstance(payload[0], dict):
                payload = payload[0]
            else:
                return {}
        if not isinstance(payload, dict):
            return {}
        return payload

    @staticmethod
    def _classify_gemini_error(exc: Exception) -> str:
        message = str(exc).lower()
        status_code = getattr(exc, "status_code", None)
        if status_code in {401, 403} or any(token in message for token in ("unauthorized", "forbidden", "api key", "authentication", "permission denied")):
            return "authentication_error"
        if status_code == 429 or any(token in message for token in ("quota", "rate limit", "resource exhausted")):
            return "quota_error"
        if status_code in {408, 504} or any(token in message for token in ("timeout", "timed out")):
            return "timeout"
        if any(token in message for token in ("network", "connection", "dns", "ssl", "unreachable")):
            return "network_error"
        if any(token in message for token in ("model", "not found", "unsupported", "invalid model")):
            return "invalid_model_response"
        return "invalid_model_response"

    @staticmethod
    def _safe_error_message(error_type: str) -> str:
        messages = {
            "missing_api_key": "Live Gemini mandate parsing requires a valid GEMINI_API_KEY.",
            "authentication_error": "Gemini authentication failed. Please check the configured API key.",
            "quota_error": "Gemini API quota has been exhausted for this request.",
            "timeout": "Gemini request timed out while parsing the mandate.",
            "network_error": "Gemini network error while parsing the mandate.",
            "invalid_json": "Gemini returned malformed JSON for the mandate parser.",
            "invalid_mandate_schema": "Gemini returned an incomplete or invalid mandate schema.",
            "invalid_model_response": "Gemini returned an unusable response for mandate parsing.",
            "empty_response": "Gemini returned an empty response for mandate parsing.",
        }
        return messages.get(error_type, "Gemini mandate parsing failed.")

    def _call_gemini(self, mandate_text: str) -> Dict[str, Any]:
        if not self.api_key and self.gemini_client is None:
            raise MandateParsingError(self._safe_error_message("missing_api_key"), "missing_api_key")

        try:
            if self.gemini_client is not None:
                if hasattr(self.gemini_client, "models"):
                    response = self.gemini_client.models.generate_content(
                        model=self.model,
                        contents=[
                            {
                                "text": (
                                    "Convert this spending mandate into valid JSON with only these keys: "
                                    "max_transaction_amount, allowed_categories, blocked_categories, "
                                    "allowed_days, require_approval_above, currency, merchant_verification_required, "
                                    "require_user_confirmation, require_user_confirmation_for, unknown_merchant_blocked, "
                                    "allow_unknown_merchants, expires_on, seller_restrictions. "
                                    "Return JSON only."
                                )
                            },
                            {"text": mandate_text},
                        ],
                    )
                    raw = getattr(response, "text", "") or str(response)
                    payload = self._normalize_response(raw)
                    if not payload:
                        raise MandateParsingError(self._safe_error_message("empty_response"), "empty_response")
                    if not any(key in payload for key in SAFE_RULE_KEYS):
                        raise MandateParsingError(self._safe_error_message("invalid_mandate_schema"), "invalid_mandate_schema")
                    return payload
                if hasattr(self.gemini_client, "generate_content"):
                    response = self.gemini_client.generate_content(
                        "Convert this spending mandate into valid JSON. Return JSON only. Mandate: " + mandate_text
                    )
                    raw = getattr(response, "text", "") or str(response)
                    payload = self._normalize_response(raw)
                    if not payload:
                        raise MandateParsingError(self._safe_error_message("empty_response"), "empty_response")
                    if not any(key in payload for key in SAFE_RULE_KEYS):
                        raise MandateParsingError(self._safe_error_message("invalid_mandate_schema"), "invalid_mandate_schema")
                    return payload
            try:
                import google.generativeai as genai
            except Exception as exc:
                raise MandateParsingError(self._safe_error_message("missing_api_key"), "missing_api_key") from exc

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(
                "Return only a valid JSON object for this mandate; use no markdown and no extra explanation. "
                "Rules schema: max_transaction_amount, allowed_categories, blocked_categories, allowed_days, "
                "require_approval_above, currency, merchant_verification_required, require_user_confirmation, "
                "require_user_confirmation_for, unknown_merchant_blocked, allow_unknown_merchants, expires_on, seller_restrictions. "
                "Mandate: " + mandate_text,
                generation_config={"temperature": 0.1, "response_mime_type": "application/json"},
            )
            raw = getattr(response, "text", "") or str(response)
            payload = self._normalize_response(raw)
            if not payload:
                raise MandateParsingError(self._safe_error_message("empty_response"), "empty_response")
            if not any(key in payload for key in SAFE_RULE_KEYS):
                raise MandateParsingError(self._safe_error_message("invalid_mandate_schema"), "invalid_mandate_schema")
            return payload
        except MandateParsingError:
            raise
        except Exception as exc:
            error_type = self._classify_gemini_error(exc)
            raise MandateParsingError(self._safe_error_message(error_type), error_type) from exc

    def validate_rules(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(rules, dict):
            raise PolicyValidationError("Mandate rules must be provided as a JSON object.")

        cleaned: Dict[str, Any] = {
            "max_transaction_amount": None,
            "allowed_categories": [],
            "blocked_categories": [],
            "allowed_days": [],
            "require_approval_above": None,
            "currency": "INR",
            "merchant_verification_required": False,
            "require_user_confirmation": False,
            "require_user_confirmation_for": [],
            "unknown_merchant_blocked": False,
            "allow_unknown_merchants": False,
            "expires_on": None,
            "seller_restrictions": [],
        }

        for key, value in rules.items():
            if key not in SAFE_RULE_KEYS:
                continue
            cleaned[key] = value

        cleaned["max_transaction_amount"] = self._coerce_float(cleaned.get("max_transaction_amount"))
        cleaned["require_approval_above"] = self._coerce_float(cleaned.get("require_approval_above"))
        cleaned["allowed_categories"] = self._normalize_category_list(self._as_list(cleaned.get("allowed_categories")))
        cleaned["blocked_categories"] = self._normalize_category_list(self._as_list(cleaned.get("blocked_categories")))
        cleaned["allowed_days"] = self._normalize_day_list(self._as_list(cleaned.get("allowed_days")))
        cleaned["currency"] = str(cleaned.get("currency") or "INR").upper()
        cleaned["merchant_verification_required"] = bool(cleaned.get("merchant_verification_required", False))
        cleaned["require_user_confirmation"] = bool(cleaned.get("require_user_confirmation", False))
        cleaned["require_user_confirmation_for"] = self._as_list(cleaned.get("require_user_confirmation_for"))
        cleaned["unknown_merchant_blocked"] = bool(cleaned.get("unknown_merchant_blocked", False))
        cleaned["allow_unknown_merchants"] = bool(cleaned.get("allow_unknown_merchants", False))
        cleaned["expires_on"] = str(cleaned.get("expires_on") or "").strip() or None
        cleaned["seller_restrictions"] = self._as_list(cleaned.get("seller_restrictions"))

        if cleaned["max_transaction_amount"] is not None and cleaned["max_transaction_amount"] <= 0:
            raise PolicyValidationError("The maximum transaction amount must be a positive number.")
        if cleaned["require_approval_above"] is not None and cleaned["require_approval_above"] <= 0:
            cleaned["require_approval_above"] = None
        if cleaned["allowed_days"]:
            cleaned["allowed_days"] = [day for day in VALID_DAYS if day in cleaned["allowed_days"]]

        return cleaned

    def parse(self, mandate_text: str) -> Dict[str, Any]:
        text = (mandate_text or "").strip()
        if not text:
            raise PolicyValidationError("Mandate text is required.")

        if not self.api_key and self.gemini_client is None:
            raise MandateParsingError(self._safe_error_message("missing_api_key"), "missing_api_key")

        ai_result = self._call_gemini(text)
        if not ai_result:
            raise MandateParsingError(self._safe_error_message("invalid_model_response"), "invalid_model_response")

        validated = self.validate_rules(ai_result)
        return validated

    def parse_with_fallback(self, mandate_text: str) -> Dict[str, Any]:
        text = (mandate_text or "").strip()
        if not text:
            raise PolicyValidationError("Mandate text is required.")
        try:
            return {"source": "gemini", "rules": self.parse(text)}
        except MandateParsingError as exc:
            fallback_rules = self.validate_rules(self._fallback_rules(text))
            return {
                "source": "fallback",
                "warning": str(exc),
                "error_type": exc.error_type,
                "rules": fallback_rules,
            }


class PolicyDecisionEngine:
    def __init__(self, database_path: Optional[str] = None, parser: Optional[PolicyMandateParser] = None):
        base_dir = Path(__file__).resolve().parent
        self.database_path = Path(database_path or str(base_dir / "policy_store.sqlite3"))
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.parser = parser or PolicyMandateParser()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.database_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS policy_mandates (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    rules_json TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    raw_text TEXT,
                    expires_on TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS policy_decisions (
                    transaction_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    mandate_id TEXT,
                    decision TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    requested_amount REAL,
                    maximum_allowed REAL,
                    policy_violations_json TEXT,
                    full_result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS policy_evaluation_requests (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    mandate_id TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def store_mandate(self, user_id: str, mandate_id: str, rules: Dict[str, Any], name: str = "Mandate", raw_text: str = "") -> Dict[str, Any]:
        if not user_id:
            raise PolicyValidationError("A valid user ID is required.")
        if not mandate_id:
            raise PolicyValidationError("A valid mandate ID is required.")

        payload = self.parser.validate_rules(rules)
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        with self._connect() as conn:
            existing = conn.execute("SELECT version FROM policy_mandates WHERE id = ? AND user_id = ?", (mandate_id, user_id)).fetchone()
            version = (existing["version"] if existing is not None else 0) + 1
            conn.execute(
                """
                INSERT INTO policy_mandates (id, user_id, name, rules_json, version, active, created_at, updated_at, raw_text, expires_on)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    name = excluded.name,
                    rules_json = excluded.rules_json,
                    version = excluded.version,
                    active = excluded.active,
                    updated_at = excluded.updated_at,
                    raw_text = excluded.raw_text,
                    expires_on = excluded.expires_on
                """,
                (
                    mandate_id,
                    user_id,
                    name,
                    json.dumps(payload),
                    version,
                    now,
                    now,
                    raw_text,
                    payload.get("expires_on"),
                ),
            )
        return payload

    def list_user_mandates(self, user_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, user_id, name, rules_json, version, active, created_at, updated_at, expires_on FROM policy_mandates WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            ).fetchall()
        mandates: List[Dict[str, Any]] = []
        for row in rows:
            rules = json.loads(row["rules_json"]) if row["rules_json"] else {}
            mandates.append(
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "status": "Active" if row["active"] else "Paused",
                    "active": bool(row["active"]),
                    "rules": rules,
                    "version": row["version"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "expires_on": row["expires_on"],
                }
            )
        return mandates

    def get_mandate(self, user_id: str, mandate_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, user_id, name, rules_json, version, active, created_at, updated_at, expires_on FROM policy_mandates WHERE id = ?",
                (mandate_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Mandate {mandate_id} does not exist.")
        if row["user_id"] != user_id:
            raise PermissionError("You are not authorized to access this mandate.")
        rules = json.loads(row["rules_json"]) if row["rules_json"] else {}
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "status": "Active" if row["active"] else "Paused",
            "active": bool(row["active"]),
            "rules": rules,
            "version": row["version"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "expires_on": row["expires_on"],
        }

    def get_decision(self, transaction_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM policy_decisions WHERE transaction_id = ?",
                (transaction_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Decision record {transaction_id} does not exist.")
        return json.loads(row["full_result_json"]) if row["full_result_json"] else {}

    def _weekday_name(self, transaction_date: str) -> str:
        if not transaction_date:
            return datetime.utcnow().strftime("%A")
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d %b %Y"):
            try:
                return datetime.strptime(str(transaction_date), fmt).strftime("%A")
            except ValueError:
                continue
        return datetime.utcnow().strftime("%A")

    def evaluate_purchase(
        self,
        user_id: str,
        mandate_id: str,
        product_name: str,
        product_category: str,
        product_price: Any,
        merchant_name: str,
        merchant_trust_status: str,
        currency: str,
        transaction_date: Optional[str],
        mandate_rules: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if product_price is None or product_price == "":
            raise ValueError("Product price is required.")
        if not user_id:
            raise PolicyValidationError("A valid user ID is required.")
        if mandate_rules is None:
            if not mandate_id:
                raise PolicyValidationError("A valid mandate ID or mandate rules are required.")
            mandate_rules = self.get_mandate(user_id, mandate_id)["rules"]
        elif mandate_id and not mandate_rules:
            try:
                self.get_mandate(user_id, mandate_id)
            except PermissionError:
                raise

        rules = self.parser.validate_rules(mandate_rules or {})
        if not isinstance(product_price, (int, float)):
            price = self.parser._coerce_float(product_price)
            if price is None:
                raise ValueError("Product price must be numeric.")
        else:
            price = float(product_price)

        category = str(product_category or "").strip().lower()
        category_name = category if category else "uncategorized"
        merchant = (merchant_name or "").strip()
        trust_status = str(merchant_trust_status or "unknown").strip().lower()
        if not merchant:
            trust_status = "unknown"

        requested_amount = price
        max_allowed = rules.get("max_transaction_amount")
        approval_threshold = rules.get("require_approval_above")
        allow_unknown_merchants = bool(rules.get("allow_unknown_merchants", False))
        unknown_merchant_blocked = bool(rules.get("unknown_merchant_blocked", False))
        allowed_days = rules.get("allowed_days") or []
        allowed_categories = rules.get("allowed_categories") or []
        blocked_categories = rules.get("blocked_categories") or []
        allowed_category_names = {str(item).lower() for item in allowed_categories}
        blocked_category_names = {str(item).lower() for item in blocked_categories}
        known_category_names = set(CATEGORY_ALIASES.values()) | {
            "food", "electronics", "travel", "furniture", "software", "healthcare",
            "clothing", "jewelry", "books", "education"
        }
        violations: List[str] = []
        block = False
        escalate = False
        reason = "Purchase follows all active mandate rules."

        if allowed_categories and category_name not in allowed_category_names:
            if category_name in blocked_category_names:
                block = True
                violations.append("Product category is explicitly blocked by the mandate")
            elif category_name not in known_category_names:
                escalate = True
                violations.append("Product category is ambiguous and requires clarification")
            else:
                block = True
                violations.append("Product category is not allowed by the active mandate")
        if blocked_categories and category_name in blocked_category_names:
            block = True
            violations.append("Product category is explicitly blocked by the mandate")
        if max_allowed is not None and requested_amount > max_allowed:
            block = True
            violations.append("Transaction amount exceeds the mandate limit")
        if allowed_days and self._weekday_name(transaction_date) not in allowed_days:
            block = True
            violations.append("Transaction occurred on a disallowed day")

        expires_on = rules.get("expires_on")
        if expires_on:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d %b %Y"):
                try:
                    expiry_date = datetime.strptime(str(expires_on), fmt)
                    if datetime.utcnow() > expiry_date:
                        block = True
                        violations.append("Mandate has expired")
                    break
                except ValueError:
                    continue

        if rules.get("merchant_verification_required") and (not merchant or trust_status in {"unknown", "unverified", "untrusted", "missing"}):
            if not allow_unknown_merchants or unknown_merchant_blocked:
                escalate = True
                violations.append("Merchant information is missing or not verified")

        if rules.get("require_user_confirmation") or (rules.get("require_user_confirmation_for") and "unknown" in [str(item).lower() for item in rules.get("require_user_confirmation_for", [])]):
            if not merchant or trust_status in {"unknown", "unverified", "missing"}:
                escalate = True
                violations.append("User confirmation is required before approval")

        if approval_threshold is not None and requested_amount > approval_threshold and (max_allowed is None or requested_amount <= max_allowed):
            escalate = True
            violations.append("Purchase exceeds the normal approval threshold")

        if price <= 0:
            raise ValueError("Product price must be greater than zero.")

        if block:
            decision = "BLOCK"
            reason = "The purchase violates a mandatory rule in the active mandate."
            if max_allowed is not None and requested_amount > max_allowed:
                reason = "The product price exceeds the maximum transaction limit."
        elif escalate:
            decision = "ESCALATE"
            reason = "The purchase needs additional user authorization before approval."
        else:
            decision = "APPROVE"
            reason = "The purchase follows all active mandate constraints."

        result = {
            "decision": decision,
            "reason": reason,
            "requested_amount": requested_amount,
            "maximum_allowed": max_allowed,
            "policy_violations": violations,
            "product_name": product_name,
            "product_category": product_category,
            "merchant_name": merchant,
            "merchant_trust_status": trust_status,
            "currency": str(currency or rules.get("currency") or "INR").upper(),
            "transaction_date": transaction_date or datetime.utcnow().strftime("%Y-%m-%d"),
            "user_id": user_id,
            "mandate_id": mandate_id,
            "rules": rules,
            "decision_id": f"DEC-{uuid.uuid4().hex[:8].upper()}",
        }

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO policy_decisions (transaction_id, user_id, mandate_id, decision, reason, requested_amount, maximum_allowed, policy_violations_json, full_result_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(transaction_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    mandate_id = excluded.mandate_id,
                    decision = excluded.decision,
                    reason = excluded.reason,
                    requested_amount = excluded.requested_amount,
                    maximum_allowed = excluded.maximum_allowed,
                    policy_violations_json = excluded.policy_violations_json,
                    full_result_json = excluded.full_result_json,
                    created_at = excluded.created_at
                """,
                (
                    result["decision_id"],
                    user_id,
                    mandate_id,
                    decision,
                    reason,
                    requested_amount,
                    max_allowed,
                    json.dumps(violations),
                    json.dumps(result),
                    datetime.utcnow().isoformat(timespec="seconds") + "Z",
                ),
            )

        return result
