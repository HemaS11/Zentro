"""Checks the three example requests from the brief.  Run: python test_agent.py"""
import os
from unittest.mock import patch

from agent import run_agent, parse_budget
from policy_client import evaluate


def run_rule_agent(query):
    with patch("agent.gemini_parse", return_value=None):
        return run_agent(query)


def names(r, key="recommended"):
    return [x["name"] for x in r[key]]


def test_laptops_under_50k():
    r = run_rule_agent("Find laptops under \u20b950,000")
    assert r["parsed"]["max_budget"] == 50000 and r["parsed"]["category"] == "Laptops"
    assert len(r["recommended"]) == 3 and all(x["price"] <= 50000 for x in r["recommended"])
    assert any("Vivobook" in n for n in names(r, "excluded"))  # 52,990 is excluded
    assert all(x["reason"] for x in r["excluded"])
    assert [p["rank"] for p in r["recommended"]] == [1, 2, 3]
    assert all(p["badges"] and p["why_recommended"] for p in r["recommended"])


def test_textbook_under_1000():
    r = run_rule_agent("Find a textbook under \u20b91,000")
    assert r["recommended"] and all(x["category"] == "Textbooks" and x["price"] <= 1000 for x in r["recommended"])


def test_wireless_headphones_under_2000():
    r = run_rule_agent("Find wireless headphones under \u20b92,000")
    assert len(r["recommended"]) == 4 and all(x["price"] <= 2000 for x in r["recommended"])
    assert "wireless" in r["parsed"]["keywords"]
    assert all("wireless" in x["badges"] for x in r["recommended"])


def test_budget_shorthand_and_no_budget():
    assert parse_budget("laptop under 50k")[0] == 50000
    assert parse_budget("laptop below 1.5 lakh")[0] == 150000
    assert parse_budget("gaming laptop, don't exceed \u20b970,000")[0] == 70000
    r = run_rule_agent("Find engineering textbooks")
    assert r["parsed"]["max_budget"] is None and len(r["recommended"]) >= 4
    gaming = run_rule_agent("Find a gaming laptop, don't exceed \u20b970,000")
    assert gaming["parsed"]["purpose"] == "gaming"
    assert gaming["recommended"][0]["id"] == "LAP-006"
    classes = run_rule_agent("I need headphones for online classes")
    assert classes["parsed"]["purpose"] == "online classes"
    assert classes["recommended"]


def test_nothing_fits_and_unknown():
    assert "cheapest" in run_rule_agent("laptop under 10000")["summary"]
    assert run_rule_agent("flying carpet")["recommended"] == []


def test_policy_decisions():
    p = lambda price: {"name": "x", "price": price, "category": "Laptops"}
    assert [evaluate(p(x))["decision"] for x in (5000, 45000, 150000)] == ["APPROVE", "ESCALATE", "BLOCK"]


def test_gemini_failure_falls_back_to_rules():
    from agent import understand

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("google.genai.Client", side_effect=RuntimeError("simulated outage")):
            parsed = understand("Find a gaming laptop under 70k")
    assert parsed["parser"] == "rules"
    assert parsed["category"] == "Laptops" and parsed["max_budget"] == 70000


def test_policy_engine_failure_escalates():
    import httpx

    product = {"name": "x", "price": 5000, "category": "Laptops"}
    with patch.dict(os.environ, {"POLICY_ENGINE_URL": "http://127.0.0.1:1"}):
        with patch("policy_client.httpx.post", side_effect=httpx.ConnectError("connection refused")):
            result = evaluate(product)
    assert result["decision"] == "ESCALATE" and result["source"] == "error"


def test_invalid_policy_response_escalates():
    from unittest.mock import Mock

    product = {"name": "x", "price": 5000, "category": "Laptops"}
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"decision": "ALLOW", "reason": "unrecognized"}
    with patch.dict(os.environ, {"POLICY_ENGINE_URL": "http://policy.test/evaluate"}):
        with patch("policy_client.httpx.post", return_value=response):
            result = evaluate(product)
    assert result["decision"] == "ESCALATE" and result["source"] == "error"


def test_full_flow():
    import store
    mk = lambda price, name: {"id": "T", "name": name, "price": price, "category": "Laptops", "description": "", "link": ""}
    ok = store.check_product(mk(22000, "Small laptop"), "q")
    assert ok["state"] == "Ready to pay" and ok["risk"]["level"] in ("Low", "Medium", "High")
    spent = store.find("Laptops")["spent"]
    paid = store.pay(ok["id"])
    assert paid["state"] == "Paid" and paid["receipt"]["verified"] and store.find("Laptops")["spent"] == spent + 22000
    ask = store.check_product(mk(60000, "Big laptop"), "q")
    assert ask["state"] == "Awaiting you"
    assert store.resolve(ask["id"], "allow")["state"] == "Ready to pay"
    ask2 = store.check_product(mk(61000, "Another"), "q")
    assert store.resolve(ask2["id"], "reject")["state"] == "Rejected"
    for bad in (lambda: store.pay(ask2["id"]), lambda: store.resolve(ok["id"], "allow"),
                lambda: store.create_mandate({"name": "x", "category": "Laptops", "max_per_purchase": 1, "approval_above": 1, "monthly_budget": 1})):
        try:
            bad(); assert False
        except store.FlowError:
            pass
    blocked = store.check_product(mk(150000, "Huge"), "q")
    assert blocked["state"] == "Blocked"
    try:
        store.pay(blocked["id"])
        assert False
    except store.FlowError:
        pass


def test_seed_and_receipt_audit():
    import store
    assert len(store.TX) >= 10 and {t["decision"] for t in store.TX} == {"APPROVE", "ESCALATE", "BLOCK"}
    assert any(t["receipt"] and not t["receipt"]["verified"] for t in store.TX)  # auditor flags a mismatch


def test_gemini_json_mode_without_network():
    from agent import gemini_parse

    response = type("Response", (), {
        "text": '{"category":"Laptops","max_budget":70000,"purpose":"gaming","keywords":["gaming"]}'
    })()
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-3.8-flash"}):
        with patch("google.genai.Client") as client_class:
            client_class.return_value.models.generate_content.return_value = response
            result = gemini_parse("gaming laptop under 70k")

    assert result["parser"] == "gemini"
    assert result["category"] == "Laptops" and result["max_budget"] == 70000
    client_class.assert_called_once_with(api_key="test-key")
    config = client_class.return_value.models.generate_content.call_args.kwargs["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema is not None


def test_policy_endpoint_uses_catalog_values():
    from fastapi.testclient import TestClient
    from main import app
    from policy_engine import evaluate as evaluate_local

    client = TestClient(app)
    approve = client.post("/api/policy/evaluate", json={
        "product_id": "HP-001",
        "product_name": "boAt Rockerz 255 Pro+ Wireless Neckband",
        "amount": 1299,
        "currency": "INR",
        "category": "Headphones",
        "user_request": "headphones",
    })
    escalate = client.post("/api/policy/evaluate", json={
        "product_id": "LAP-001",
        "product_name": "Acer Aspire 5 (Core i5, 16GB, 512GB SSD)",
        "amount": 44990,
        "currency": "INR",
        "category": "Laptops",
    })
    block = client.post("/api/policy/evaluate", json={
        "product_id": "LAP-007",
        "product_name": "Apple MacBook Air M2 (8GB, 256GB)",
        "amount": 89900,
        "currency": "INR",
        "category": "Laptops",
    })
    with patch(
        "policy_client.evaluate",
        side_effect=lambda product, query="": {
            **evaluate_local(product),
            "source": "local-policy-engine",
        },
    ):
        blocked_purchase = client.post("/api/policy-check", json={
            "product": {"id": "LAP-007"},
            "query": "premium laptop",
        })
    blocked_pay = client.post(f"/api/transactions/{blocked_purchase.json()['id']}/pay")

    result = {"decision": "APPROVE", "reason": "Test decision", "source": "local-policy-engine"}
    with patch("policy_client.evaluate", return_value=result):
        response = client.post("/api/policy-check", json={
            "product": {
                "id": "LAP-001",
                "name": "Forged product",
                "price": 1,
                "category": "Textbooks",
            },
            "query": "test",
        })
        invalid = client.post("/api/policy-check", json={
            "product": {"id": "NOT-IN-CATALOG", "price": 1},
        })
        with patch("agent.gemini_parse", return_value=None):
            search = client.post("/api/search", json={"query": "Find a laptop under 50000"})
        page = client.get("/")
        status = client.get("/api/status")

    assert approve.status_code == 200 and approve.json()["decision"] == "APPROVE"
    assert approve.json()["engine"] == "Mandate Pay Local Policy Engine"
    assert escalate.status_code == 200 and escalate.json()["decision"] == "ESCALATE"
    assert block.status_code == 200 and block.json()["decision"] == "BLOCK"
    assert blocked_purchase.status_code == 200 and blocked_purchase.json()["state"] == "Blocked"
    assert blocked_pay.status_code == 400
    assert response.status_code == 200
    assert response.json()["product"] == "Acer Aspire 5 (Core i5, 16GB, 512GB SSD)"
    assert response.json()["amount"] == 44990
    assert invalid.status_code == 400
    assert search.status_code == 200 and search.json()["parser"] == "rules"
    assert page.status_code == 200 and "Zentro" in page.text
    assert status.status_code == 200 and status.json()["policy"] == "local"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
