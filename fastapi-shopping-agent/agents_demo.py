"""Demo versions of the Risk Detection and Receipt Auditor agents (dummy logic, real flow)."""
import re
from statistics import mean

from agent import inr

GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z]\dZ[A-Z\d]$")


def risk_check(price: float, category: str, history: list[float]) -> dict:
    if len(history) < 2:
        return {"score": 10, "level": "Low", "note": f"Not enough {category} history to compare."}
    avg = mean(history)
    dev = (price - avg) / avg * 100
    score = 5 if dev <= 10 else min(95, int(10 + dev * 0.6))
    level = "Low" if score < 30 else "Medium" if score < 60 else "High"
    note = (f"{dev:.0f}% above the {category} average of {inr(avg)}." if dev > 10
            else f"In line with the {category} average of {inr(avg)}.")
    return {"score": score, "level": level, "note": note}


def make_receipt(tx: dict, total: float | None = None) -> dict:
    """Builds a dummy invoice and audits it. `total` lets seed data simulate a bad receipt."""
    amount = tx["amount"]
    total = amount if total is None else total
    subtotal = round(total / 1.18, 2)
    gst = round(total - subtotal, 2)
    gstin = "29ABCDE1234F1Z5"
    problems = []
    if not GSTIN_RE.match(gstin):
        problems.append("GSTIN format invalid")
    if abs(subtotal + gst - total) > 0.01:
        problems.append("Subtotal and GST do not add up")
    if abs(total - amount) > 0.01:
        problems.append(f"Receipt total {inr(total)} differs from approved {inr(amount)}")
    return {"invoice": f"INV-{tx['id'][-4:]}", "gstin": gstin, "subtotal": subtotal, "gst": gst,
            "total": total, "verified": not problems,
            "notes": "GSTIN format valid. Totals match the approved amount." if not problems
            else "; ".join(problems) + "."}
