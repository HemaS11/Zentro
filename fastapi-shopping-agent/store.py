"""In-memory app state and the purchase flow (no web framework needed, so it is easy to test).

Flow: search -> check_product (policy + risk) -> [resolve if ESCALATE] -> pay (receipt audit).
"""
from datetime import datetime

import policy_client
from agents_demo import make_receipt, risk_check
from mandates import MANDATES, add_mandate, find
from products import CATEGORIES
from seed import seed_transactions

TX: list[dict] = seed_transactions()
STATS = {"searches": 24, "checks": len(TX)}  # demo starting counts
ACCURACY = {"mandate": 98.1, "research": 94.8, "policy": 97.3, "risk": 96.5, "receipt": 98.2}  # demo values
LAST: dict = {"search": None, "decision": TX[0], "mandate": MANDATES[-1],
              "receipt": next((t["receipt"] for t in TX if t["receipt"]), None)}


class FlowError(ValueError):
    pass


def _get(tx_id: str) -> dict:
    tx = next((t for t in TX if t["id"] == tx_id), None)
    if not tx:
        raise FlowError("Transaction not found.")
    return tx


def check_product(product: dict, query: str = "") -> dict:
    result = policy_client.evaluate(product, query)
    if result["source"] in ("mock", "local-policy-engine") and result["decision"] == "APPROVE":
        mandate = find(product["category"])
        if mandate:
            reserved = sum(
                t["amount"]
                for t in TX
                if t["category"] == product["category"]
                and t["state"] in ("Awaiting you", "Ready to pay")
            )
            if mandate["spent"] + reserved + product["price"] > mandate["monthly_budget"]:
                result = {
                    **result,
                    "decision": "ESCALATE",
                    "reason": f"Would exceed the monthly budget of {mandate['name']}.",
                }

    history = [t["amount"] for t in TX if t["category"] == product["category"] and t["decision"] != "BLOCK"]
    state = {"APPROVE": "Ready to pay", "ESCALATE": "Awaiting you", "BLOCK": "Blocked"}[result["decision"]]
    tx = {"id": f"TXN-{len(TX) + 1:04d}", "product": product["name"], "vendor": "shop.example.com",
          "amount": product["price"], "category": product["category"], "decision": result["decision"],
          "state": state, "reason": result["reason"], "source": result["source"],
          "date": datetime.now().strftime("%d %b, %I:%M %p"), "agent": "Product Research",
          "risk": risk_check(product["price"], product["category"], history), "receipt": None}
    TX.insert(0, tx)
    STATS["checks"] += 1
    LAST["decision"] = tx
    return tx


def resolve(tx_id: str, action: str) -> dict:
    tx = _get(tx_id)
    if tx["state"] != "Awaiting you":
        raise FlowError("This purchase is not waiting for your decision.")
    if action == "allow":
        tx["state"], tx["reason"] = "Ready to pay", tx["reason"] + " You allowed this purchase."
    elif action == "reject":
        tx["state"], tx["reason"] = "Rejected", tx["reason"] + " You rejected this purchase."
    else:
        raise FlowError("Action must be allow or reject.")
    return tx


def pay(tx_id: str) -> dict:
    tx = _get(tx_id)
    if tx["state"] != "Ready to pay":
        raise FlowError("Only approved or allowed purchases can be paid.")
    tx["receipt"], tx["state"] = make_receipt(tx), "Paid"
    if (m := find(tx["category"])):
        m["spent"] += tx["amount"]
    LAST["receipt"] = tx["receipt"]
    return tx


def create_mandate(data: dict) -> dict:
    if data["category"] not in CATEGORIES:
        raise FlowError("Choose a valid category.")
    if find(data["category"]):
        raise FlowError(f"{data['category']} already has a mandate.")
    if min(data["max_per_purchase"], data["approval_above"], data["monthly_budget"]) <= 0:
        raise FlowError("Amounts must be greater than zero.")
    if data["approval_above"] > data["max_per_purchase"]:
        raise FlowError("Approval threshold cannot exceed the per-purchase limit.")
    if not data["name"].strip():
        raise FlowError("Give the mandate a name.")
    LAST["mandate"] = add_mandate({**data, "name": data["name"].strip()})
    return LAST["mandate"]


def record_search(r: dict) -> None:
    STATS["searches"] += 1
    LAST["search"] = {"query": r["query"], "engine": r["engine"], "parsed": r["parsed"],
                      "recommended": len(r["recommended"]), "excluded": len(r["excluded"])}


def overview(status: dict) -> dict:
    tasks = {"mandate": 9 + len(MANDATES), "research": STATS["searches"], "policy": STATS["checks"],
             "risk": STATS["checks"], "receipt": sum(1 for t in TX if t["receipt"])}
    agents = {k: {"tasks": tasks[k], "acc": ACCURACY[k]} for k in tasks}
    return {"stats": STATS, "transactions": TX, "mandates": MANDATES, "last": LAST, "status": status, "agents": agents}
