"""HTTP client for the Mandate Pay policy engine."""
import os

import httpx

VALID = {"APPROVE", "BLOCK", "ESCALATE"}
LOCAL_ENGINE = "Mandate Pay Local Policy Engine"


def build_payload(product: dict, query: str) -> dict:
    return {
        "product_id": product.get("id"),
        "product_name": product["name"],
        "amount": product["price"],
        "currency": "INR",
        "category": product["category"],
        "description": product.get("description", ""),
        "product_link": product.get("link", ""),
        "user_request": query,
    }


def evaluate(product: dict, query: str = "") -> dict:
    url = os.getenv("POLICY_ENGINE_URL", "").strip()
    if not url:
        from policy_engine import evaluate as evaluate_local

        return {**evaluate_local(product), "source": "local-policy-engine"}
    try:
        r = httpx.post(url, json=build_payload(product, query), timeout=8)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            raise ValueError("response must be a JSON object")
        decision = str(data.get("decision", "")).upper()
        if decision not in VALID:
            raise ValueError("response contained an unsupported decision")
        reason = data.get("reason", "")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("response reason must be non-empty text")
        engine = data.get("engine")
        source = "local-policy-engine" if engine == LOCAL_ENGINE else "policy-engine"
        return {"decision": decision, "reason": reason, "source": source}
    except (httpx.HTTPError, ValueError, TypeError) as error:
        return {
            "decision": "ESCALATE",
            "source": "error",
            "reason": (
                "Policy Engine was unavailable or returned an invalid response "
                f"({type(error).__name__}). Sent to you for review."
            ),
        }
