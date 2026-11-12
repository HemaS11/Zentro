"""Local Mandate Pay policy engine for purchase authorization."""

import math

from mandates import find


def evaluate(product: dict, reserved: float = 0) -> dict:
    """Evaluate one catalogue product against its active spending mandate."""

    price = product.get("price")
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        return {"decision": "BLOCK", "reason": "Purchase amount must be a number."}
    if not math.isfinite(price) or price <= 0:
        return {"decision": "BLOCK", "reason": "Purchase amount must be greater than zero."}

    mandate = find(product.get("category", ""))
    if not mandate:
        return {
            "decision": "ESCALATE",
            "reason": f"No active mandate covers {product.get('category', 'this category')}.",
        }

    if price > mandate["max_per_purchase"]:
        return {
            "decision": "BLOCK",
            "reason": (
                f"Exceeds the ₹{mandate['max_per_purchase']:,} per-purchase "
                f"limit of {mandate['name']}."
            ),
        }

    if price > mandate["approval_above"]:
        return {
            "decision": "ESCALATE",
            "reason": (
                f"Above ₹{mandate['approval_above']:,}, so your approval "
                "is required."
            ),
        }

    if mandate["spent"] + reserved + price > mandate["monthly_budget"]:
        return {
            "decision": "ESCALATE",
            "reason": f"Would exceed the monthly budget of {mandate['name']}.",
        }

    return {
        "decision": "APPROVE",
        "reason": f"Within the {mandate['name']} mandate.",
    }
