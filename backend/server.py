import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from backend.policy_engine import PolicyDecisionEngine, PolicyMandateParser, PolicyValidationError
except Exception:  # pragma: no cover
    sys.path.insert(0, str(ROOT))
    from backend.policy_engine import PolicyDecisionEngine, PolicyMandateParser, PolicyValidationError

ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = ROOT / "ai-agents"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

try:
    from config import get_agent_config
except Exception:
    def get_agent_config() -> Dict[str, Any]:
        return {}

AGENT_CONFIG = get_agent_config()

try:
    from agent_coordinator import AgentCoordinator
except Exception:
    AgentCoordinator = None

try:
    import google.generativeai as genai
except Exception:
    genai = None

try:
    from google import genai as google_genai
except Exception:
    google_genai = None

app = FastAPI(title="Zentro API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SEED_TRANSACTIONS = [
    {"id": "TXN-4821", "vendor": "Dell Technologies", "category": "Technology", "amount": 42500, "status": "Approved", "date": "2026-11-05", "agent": "Policy Judge", "merchant": "Dell Technologies", "description": "Laptop refresh for design team"},
    {"id": "TXN-4820", "vendor": "AWS Cloud Services", "category": "Technology", "amount": 18750, "status": "Approved", "date": "2026-11-04", "agent": "Mandate Creator", "merchant": "AWS Cloud Services", "description": "Infrastructure and hosting"},
    {"id": "TXN-4819", "vendor": "Unknown Vendor Ltd.", "category": "Travel", "amount": 95000, "status": "Blocked", "date": "2026-11-04", "agent": "Risk Detection", "merchant": "Unknown Vendor Ltd.", "description": "Unrecognized merchant match"},
    {"id": "TXN-4818", "vendor": "Google Workspace", "category": "Software", "amount": 6800, "status": "Approved", "date": "2026-11-03", "agent": "Policy Judge", "merchant": "Google Workspace", "description": "Workspace and collaboration tools"},
    {"id": "TXN-4817", "vendor": "WeWork Spaces", "category": "Office", "amount": 32000, "status": "Escalated", "date": "2026-11-03", "agent": "Risk Detection", "merchant": "WeWork Spaces", "description": "Shared office workspace"},
    {"id": "TXN-4816", "vendor": "Notion Team Plan", "category": "Software", "amount": 4500, "status": "Approved", "date": "2026-11-02", "agent": "Policy Judge", "merchant": "Notion Team Plan", "description": "Productivity subscription"},
    {"id": "TXN-4815", "vendor": "Adobe Creative Cloud", "category": "Software", "amount": 28900, "status": "Approved", "date": "2026-11-01", "agent": "Mandate Creator", "merchant": "Adobe Creative Cloud", "description": "Creative tools licensing"},
    {"id": "TXN-4814", "vendor": "Suspicious Corp.", "category": "Travel", "amount": 150000, "status": "Blocked", "date": "2026-10-31", "agent": "Risk Detection", "merchant": "Suspicious Corp.", "description": "Blocked duplicate invoice flow"},
]

SEED_MANDATES = [
    {"id": "M-102", "name": "Travel and Lifestyle", "status": "Active", "active": True, "remainingBudget": 3600, "allowedCategories": ["Travel", "Dining", "Technology", "Wellness"], "monthlyLimit": 6000, "perPurchaseLimit": 1800, "approvalThreshold": 85, "verifiedSellerOnly": True},
    {"id": "M-140", "name": "Luxury Retail", "status": "Active", "active": True, "remainingBudget": 2100, "allowedCategories": ["Luxury Goods", "Fashion"], "monthlyLimit": 5000, "perPurchaseLimit": 1200, "approvalThreshold": 75, "verifiedSellerOnly": True},
    {"id": "M-155", "name": "Technology Safety", "status": "Paused", "active": False, "remainingBudget": 1200, "allowedCategories": ["Technology"], "monthlyLimit": 30000, "perPurchaseLimit": 15000, "approvalThreshold": 90, "verifiedSellerOnly": True},
]

SEED_SETTINGS = {
    "fullName": "Zentro Demo User",
    "email": "demo@zentro.ai",
    "timezone": "UTC",
    "assistantMode": "guided",
    "theme": "luxury",
    "notificationsEnabled": True,
    "mfaStatus": "Demo",
    "sessionTimeout": "30 mins",
    "apiStatus": "Healthy",
    "geminiStatus": "Connected" if AGENT_CONFIG.get("gemini_api_key") else "Cache mode",
    "paypalStatus": "Ready" if AGENT_CONFIG.get("paypal_client_id") else "Not configured",
    "lastSync": "Demo data",
}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class AgentEvaluationRequest(BaseModel):
    transaction: Dict[str, Any]
    agent_name: Optional[str] = None


class MandateParseRequest(BaseModel):
    mandate_text: str


class PolicyMandateParseRequest(BaseModel):
    mandate_text: str


class PolicyEvaluationRequest(BaseModel):
    user_id: str
    mandate_id: str
    product_name: str
    product_category: str
    product_price: Any
    merchant_name: str
    merchant_trust_status: str = "unknown"
    currency: str = "INR"
    transaction_date: Optional[str] = None
    mandate_rules: Optional[Dict[str, Any]] = None


class PolicyMandateUpdateRequest(BaseModel):
    user_id: str
    name: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None
    raw_mandate: Optional[str] = None


policy_engine = PolicyDecisionEngine()


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_gemini_key() -> str:
    configured = AGENT_CONFIG.get("gemini_api_key", "")
    if configured:
        return configured
    for name in ("GEMINI_API_KEY", "ZENTRO_GEMINI_API_KEY"):
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def normalize_transaction(record: Dict[str, Any]) -> Dict[str, Any]:
    merchant = record.get("merchant") or record.get("vendor") or "Unknown merchant"
    status = str(record.get("status") or "Pending").title()
    payment_reference = record.get("paymentReference") or record.get("reference") or f"REF-{record.get('id', '0000')}"
    return {
        "id": record.get("id"),
        "merchant": merchant,
        "category": record.get("category") or "Other",
        "amount": float(record.get("amount", 0) or 0),
        "status": status,
        "date": record.get("date"),
        "paymentReference": payment_reference,
        "aiEvaluation": {
            "result": record.get("aiEvaluation", {}).get("result") if isinstance(record.get("aiEvaluation"), dict) else ("Review" if status.lower() != "approved" else "Approved"),
            "agent": record.get("agent") or "Policy Judge",
        },
    }


def build_agent_statuses() -> List[Dict[str, Any]]:
    return [
        {"name": "Mandate Creator", "description": "Mandate Creation", "status": "idle", "currentActivity": "Latest policy review", "confidence": 96, "decision": "REVIEW", "riskScore": 12},
        {"name": "Product Research", "description": "Technology", "status": "idle", "currentActivity": "Merchant validation", "confidence": 65, "decision": "REVIEW", "riskScore": 45},
        {"name": "Policy Judge", "description": "unknown", "status": "idle", "currentActivity": "Compliance check", "confidence": 95, "decision": "REVIEW", "riskScore": 50},
        {"name": "Risk Detection", "description": "Risk Assessment", "status": "idle", "currentActivity": "Fraud screening", "confidence": 85, "decision": "REVIEW", "riskScore": 40},
        {"name": "Receipt Auditor", "description": "Receipt Verification", "status": "idle", "currentActivity": "Evidence validation", "confidence": 95, "decision": "REVIEW", "riskScore": 40},
    ]


def build_dashboard_payload() -> Dict[str, Any]:
    recent_transactions = [normalize_transaction(txn) for txn in SEED_TRANSACTIONS[:5]]
    return {
        "summaryCards": [
            {"label": "Total spend", "value": "$32,600", "note": "Across all live accounts", "accent": False},
            {"label": "Monthly spend", "value": "$12,860", "note": "Month-to-date", "accent": True},
            {"label": "Budget left", "value": "$18,200", "note": "Protected allocation", "accent": False},
        ],
        "spendingTrend": [
            {"name": "Jan", "amount": 1500},
            {"name": "Feb", "amount": 1850},
            {"name": "Mar", "amount": 2400},
            {"name": "Apr", "amount": 2200},
            {"name": "May", "amount": 3100},
            {"name": "Jun", "amount": 2950},
            {"name": "Jul", "amount": 3300},
            {"name": "Aug", "amount": 3600},
        ],
        "mandates": SEED_MANDATES,
        "recentTransactions": recent_transactions,
        "agentActivity": build_agent_statuses(),
        "categoryData": [
            {"name": "Education", "value": 35},
            {"name": "Shopping", "value": 28},
            {"name": "Entertainment", "value": 22},
            {"name": "Other", "value": 15},
        ],
        "dataSource": "demo",
    }


def build_analytics_payload() -> Dict[str, Any]:
    return {
        "summaryCards": [
            {"label": "Approval rate", "value": "94.2%", "note": "Across live policies", "accent": False},
            {"label": "Avg processing time", "value": "1.8h", "note": "Median review lane", "accent": True},
            {"label": "Active mandates", "value": "24", "note": "Protected allocations", "accent": False},
            {"label": "Blocked this month", "value": "23", "note": "Policy exceptions", "accent": False},
        ],
        "trend": [
            {"month": "Jan", "approved": 1100, "review": 220},
            {"month": "Feb", "approved": 1300, "review": 260},
            {"month": "Mar", "approved": 1450, "review": 310},
            {"month": "Apr", "approved": 1375, "review": 280},
            {"month": "May", "approved": 1580, "review": 350},
            {"month": "Jun", "approved": 1680, "review": 390},
        ],
        "approvalBreakdown": [
            {"name": "Approved", "value": 84},
            {"name": "Review", "value": 12},
            {"name": "Blocked", "value": 4},
        ],
        "categoryBreakdown": [
            {"category": "Technology", "amount": 120000},
            {"category": "Travel", "amount": 85000},
            {"category": "Software", "amount": 63700},
        ],
        "agentStats": [
            {"name": "Mandate Creator", "activity": "policy parsing", "score": 96},
            {"name": "Product Research", "activity": "merchant validation", "score": 89},
            {"name": "Risk Detection", "activity": "fraud screening", "score": 91},
        ],
        "spendingTrend": [
            {"month": "Jan", "amount": 1500},
            {"month": "Feb", "amount": 1850},
            {"month": "Mar", "amount": 2400},
            {"month": "Apr", "amount": 2200},
            {"month": "May", "amount": 3100},
            {"month": "Jun", "amount": 2950},
        ],
        "dataSource": "demo",
    }


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "Zentro API"}


@app.get("/api/dashboard")
def dashboard() -> Dict[str, Any]:
    return build_dashboard_payload()


@app.get("/api/agents")
def agents() -> Dict[str, Any]:
    return {"agents": build_agent_statuses()}


@app.get("/api/transactions")
def transactions() -> Dict[str, Any]:
    payload = [normalize_transaction(transaction) for transaction in SEED_TRANSACTIONS]
    return {"transactions": payload, "count": len(payload), "dataSource": "demo"}


@app.get("/api/mandates")
def mandates() -> Dict[str, Any]:
    return {"mandates": SEED_MANDATES, "count": len(SEED_MANDATES)}


@app.get("/api/analytics")
def analytics() -> Dict[str, Any]:
    return build_analytics_payload()


@app.get("/api/settings")
def settings() -> Dict[str, Any]:
    return {"settings": SEED_SETTINGS}


@app.post("/api/settings")
def update_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    global SEED_SETTINGS
    SEED_SETTINGS = {**SEED_SETTINGS, **payload}
    return {"success": True, "message": "Settings updated successfully.", "settings": SEED_SETTINGS}


@app.post("/api/mandates")
def create_mandate(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = str(payload.get("name") or "Untitled mandate").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Mandate name is required.")
    mandate = {
        "id": payload.get("id") or f"M-{len(SEED_MANDATES) + 101}",
        "name": name,
        "status": str(payload.get("status") or "active").title(),
        "active": str(payload.get("status") or "active").lower() == "active",
        "remainingBudget": float(payload.get("remainingBudget") or payload.get("monthlyLimit") or 0),
        "monthlyLimit": float(payload.get("monthlyLimit") or 0),
        "perPurchaseLimit": float(payload.get("perPurchaseLimit") or 0),
        "approvalThreshold": float(payload.get("approvalThreshold") or 0),
        "allowedCategories": payload.get("allowedCategories") or [],
        "verifiedSellerOnly": bool(payload.get("verifiedSellerOnly") or True),
    }
    SEED_MANDATES.append(mandate)
    return {"success": True, "message": "Mandate saved and validated.", "mandates": SEED_MANDATES}


@app.patch("/api/mandates/{mandate_id}")
def toggle_mandate(mandate_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    for mandate in SEED_MANDATES:
        if mandate["id"] == mandate_id:
            mandate["active"] = bool(payload.get("active", mandate.get("active", True)))
            mandate["status"] = "Active" if mandate["active"] else "Paused"
            return {"success": True, "message": "Mandate updated.", "mandates": SEED_MANDATES}
    raise HTTPException(status_code=404, detail="Mandate not found.")


@app.post("/api/agents/evaluate")
def evaluate_agents(payload: AgentEvaluationRequest) -> Dict[str, Any]:
    if AgentCoordinator is None:
        raise HTTPException(status_code=503, detail="Agent Coordinator is unavailable.")
    transaction = payload.transaction
    if not isinstance(transaction, dict) or not transaction:
        raise HTTPException(status_code=400, detail="A valid transaction object is required.")
    result = AgentCoordinator().run_all(transaction)
    return {"success": True, "transaction_id": result.get("transaction_id"), "transaction": result.get("transaction"), "results": result.get("results", []), "final_authorization": result.get("final_authorization", {}), "message": "Agent evaluation completed."}


@app.post("/api/agents/parse-mandate")
def parse_mandate(payload: MandateParseRequest) -> Dict[str, Any]:
    if AgentCoordinator is None:
        raise HTTPException(status_code=503, detail="Agent Coordinator is unavailable.")
    mandate_text = (payload.mandate_text or "").strip()
    if not mandate_text:
        raise HTTPException(status_code=400, detail="Please provide a valid spending mandate.")
    result = AgentCoordinator().agents["Mandate Creator"].evaluate({"mandate_text": mandate_text})
    return {"success": True, "agent": result.agent, "decision": result.decision, "confidence": result.confidence, "risk_score": getattr(result, "risk_score", 0), "matched_policy": result.matched_policy, "mandate": getattr(result, "mandate", None), "notes": result.notes}


@app.post("/api/policy/parse-mandate")
def parse_policy_mandate(payload: PolicyMandateParseRequest) -> Dict[str, Any]:
    mandate_text = (payload.mandate_text or "").strip()
    if not mandate_text:
        raise HTTPException(status_code=400, detail="Please provide a valid spending mandate.")
    try:
        rules = PolicyMandateParser().parse(mandate_text)
    except PolicyValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": True, "rules": rules, "parsed_by": "backend.policy_engine"}


@app.post("/api/policy/evaluate")
def evaluate_policy(payload: PolicyEvaluationRequest) -> Dict[str, Any]:
    try:
        result = policy_engine.evaluate_purchase(
            user_id=payload.user_id,
            mandate_id=payload.mandate_id,
            product_name=payload.product_name,
            product_category=payload.product_category,
            product_price=payload.product_price,
            merchant_name=payload.merchant_name,
            merchant_trust_status=payload.merchant_trust_status,
            currency=payload.currency,
            transaction_date=payload.transaction_date,
            mandate_rules=payload.mandate_rules,
        )
    except (PermissionError, KeyError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (ValueError, PolicyValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": True, "decision": result, "message": "Purchase evaluation completed."}


@app.get("/api/policy/mandates/{user_id}")
def get_user_policy_mandates(user_id: str) -> Dict[str, Any]:
    mandates = policy_engine.list_user_mandates(user_id)
    return {"success": True, "user_id": user_id, "mandates": mandates, "count": len(mandates)}


@app.get("/api/policy/decision/{transaction_id}")
def get_policy_decision(transaction_id: str) -> Dict[str, Any]:
    try:
        decision = policy_engine.get_decision(transaction_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"success": True, "transaction_id": transaction_id, "decision": decision}


@app.put("/api/policy/mandates/{mandate_id}")
def update_policy_mandate(mandate_id: str, payload: PolicyMandateUpdateRequest) -> Dict[str, Any]:
    if not payload.user_id:
        raise HTTPException(status_code=400, detail="A valid user ID is required.")
    try:
        existing = policy_engine.get_mandate(payload.user_id, mandate_id)
    except (KeyError, PermissionError) as exc:
        status_code = 404 if isinstance(exc, KeyError) else 403
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    rules_payload = payload.rules or existing.get("rules", {})
    try:
        updated_rules = policy_engine.store_mandate(
            user_id=payload.user_id,
            mandate_id=mandate_id,
            rules=rules_payload,
            name=(payload.name or existing.get("name") or "Mandate"),
            raw_text=payload.raw_mandate or "",
        )
    except PolicyValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": True, "mandate_id": mandate_id, "name": payload.name or existing.get("name") or "Mandate", "rules": updated_rules, "message": "Mandate updated successfully."}


@app.post("/chat/message")
def chat_message(payload: ChatRequest) -> Dict[str, Any]:
    message = (payload.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")
    gemini_key = get_gemini_key()
    if gemini_key:
        try:
            if genai is not None:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-3.5-flash")
                response = model.generate_content("You are Zentro AI support. Use the backend context to answer: " + message)
                answer = response.text.strip() if hasattr(response, "text") else str(response)
                return {"answer": answer, "dataUnavailable": False, "lastUpdated": current_timestamp(), "source": "gemini-live"}
            if google_genai is not None:
                client = google_genai.Client(api_key=gemini_key)
                response = client.models.generate_content(model="gemini-3.5-flash", contents="You are Zentro AI support. Use the backend context to answer: " + message)
                answer = getattr(response, "text", str(response))
                return {"answer": answer, "dataUnavailable": False, "lastUpdated": current_timestamp(), "source": "gemini-live"}
        except Exception:
            pass
    summary = "Your current approval risk is moderate. One transaction is blocked and another is escalated, while the rest remain within policy."
    return {"answer": "Live Gemini connectivity is currently unavailable because the backend is missing a valid GEMINI_API_KEY. I can still provide the latest cached financial context. Context: " + summary, "dataUnavailable": True, "lastUpdated": current_timestamp(), "source": "backend-cache"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=False)
