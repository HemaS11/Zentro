"""FastAPI server: serves the Zentro dashboard and the API.
Run:  python main.py   (opens http://127.0.0.1:8000)
"""
import os
import threading
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402
from typing import Literal  # noqa: E402

import store  # noqa: E402
from agent import HAVE_LANGGRAPH, run_agent  # noqa: E402
from products import CATALOG  # noqa: E402
from policy_engine import evaluate as evaluate_policy  # noqa: E402

BASE = Path(__file__).parent
LOCAL_POLICY_URL = "http://127.0.0.1:8000/api/policy/evaluate"
if not os.getenv("POLICY_ENGINE_URL", "").strip():
    os.environ["POLICY_ENGINE_URL"] = LOCAL_POLICY_URL

app = FastAPI(title="Zentro Shopping Agent")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


class SearchIn(BaseModel):
    query: str


class PolicyIn(BaseModel):
    product: dict
    query: str = ""


class ResolveIn(BaseModel):
    action: str = ""


class MandateIn(BaseModel):
    name: str
    category: str
    max_per_purchase: float
    approval_above: float
    monthly_budget: float


class PolicyEvaluateIn(BaseModel):
    product_id: str
    product_name: str
    amount: float = Field(gt=0)
    currency: Literal["INR"]
    category: str
    description: str = ""
    product_link: str = ""
    user_request: str = ""


def status():
    return {"gemini": bool(os.getenv("GEMINI_API_KEY")), "langgraph": HAVE_LANGGRAPH,
            "policy": "external" if os.getenv("POLICY_ENGINE_URL") != LOCAL_POLICY_URL else "local",
            "products": len(CATALOG)}


def flow(fn, *args):
    try:
        return fn(*args)
    except store.FlowError as e:
        raise HTTPException(400, str(e))


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/favicon.ico")
def favicon():
    return FileResponse(BASE / "static" / "favicon.svg")


@app.get("/api/status")
def get_status():
    return status()


@app.get("/api/overview")
def overview():
    return store.overview(status())


@app.get("/api/products")
def products():
    return CATALOG


@app.post("/api/search")
def search(body: SearchIn):
    if not body.query.strip():
        raise HTTPException(400, "Enter what you want to buy.")
    r = run_agent(body.query.strip())
    store.record_search(r)
    return r


@app.post("/api/policy-check")
def policy_check(body: PolicyIn):
    product_id = body.product.get("id")
    product = next((item for item in CATALOG if item["id"] == product_id), None)
    if product is None:
        raise HTTPException(400, "Choose a product from the catalogue.")
    return store.check_product(product, body.query)


@app.post("/api/policy/evaluate")
def policy_evaluate(body: PolicyEvaluateIn):
    product = next((item for item in CATALOG if item["id"] == body.product_id), None)
    if product is None:
        raise HTTPException(404, "Product is not in the catalogue.")
    if (
        body.product_name != product["name"]
        or body.amount != product["price"]
        or body.category != product["category"]
    ):
        raise HTTPException(400, "Product details do not match the catalogue.")

    reserved = sum(
        tx["amount"]
        for tx in store.TX
        if tx["category"] == product["category"]
        and tx["state"] in ("Awaiting you", "Ready to pay")
    )
    result = evaluate_policy(product, reserved=reserved)
    return {**result, "engine": "Mandate Pay Local Policy Engine"}


@app.post("/api/transactions/{tx_id}/resolve")
def resolve(tx_id: str, body: ResolveIn):
    return flow(store.resolve, tx_id, body.action)


@app.post("/api/transactions/{tx_id}/pay")
def pay(tx_id: str):
    return flow(store.pay, tx_id)


@app.post("/api/mandates")
def create_mandate(body: MandateIn):
    return flow(store.create_mandate, body.model_dump())


if __name__ == "__main__":
    import uvicorn
    threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:8000")).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
