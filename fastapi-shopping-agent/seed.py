"""Dummy transaction history so every page has content on first run."""
from agents_demo import make_receipt

TECH, EDU = "Within the Technology Purchases mandate.", "Within the Education & Books mandate."
ASK = "Above \u20b925,000, so your approval is required."

# date, product, category, amount, decision, state, reason, receipt total override, vendor
_ROWS = [
    ("20 Oct, 10:15 AM", "Casio fx-991EX Scientific Calculator", "Accessories", 1295, "APPROVE", "Paid", TECH, None, None),
    ("23 Oct, 04:40 PM", "Higher Engineering Mathematics - B.S. Grewal", "Textbooks", 699, "APPROVE", "Paid", EDU, None, None),
    ("25 Oct, 12:05 PM", "boAt Rockerz 255 Pro+ Wireless Neckband", "Headphones", 1299, "APPROVE", "Paid", TECH, 1399, None),
    ("27 Oct, 09:30 AM", "Acer Aspire 5 (Core i5, 16GB, 512GB SSD)", "Laptops", 44990, "ESCALATE", "Paid", ASK + " You allowed this purchase.", None, None),
    ("29 Oct, 06:20 PM", "Apple MacBook Air M2 (8GB, 256GB)", "Laptops", 89900, "ESCALATE", "Rejected", ASK + " You rejected this purchase.", None, None),
    ("30 Oct, 01:10 PM", "Thermodynamics: An Engineering Approach - Cengel", "Textbooks", 1350, "APPROVE", "Paid", EDU, None, None),
    ("01 Nov, 11:45 AM", "Gaming Desktop (unlisted vendor)", "Laptops", 150000, "BLOCK", "Blocked",
     "Exceeds the \u20b980,000 per-purchase limit of Technology Purchases.", None, "unknown-vendor.biz"),
    ("03 Nov, 03:25 PM", "Logitech M235 Wireless Mouse", "Accessories", 699, "APPROVE", "Paid", TECH, None, None),
    ("05 Nov, 10:00 AM", "Sony WH-CH520 Wireless Headphones", "Headphones", 3990, "APPROVE", "Paid", TECH, None, None),
    ("06 Nov, 05:15 PM", "ASUS TUF Gaming F15 (RTX 3050, 16GB)", "Laptops", 67990, "ESCALATE", "Awaiting you", ASK, None, None),
]


def seed_transactions() -> list[dict]:
    out = []
    for n, (date, product, cat, amount, decision, state, reason, total, vendor) in enumerate(_ROWS, 1):
        tx = {"id": f"TXN-{n:04d}", "product": product, "vendor": vendor or "shop.example.com", "amount": amount,
              "category": cat, "decision": decision, "state": state, "reason": reason, "source": "demo",
              "date": date, "agent": "Product Research", "risk": None, "receipt": None}
        if state == "Paid":
            tx["receipt"] = make_receipt(tx, total)
        out.append(tx)
    return out[::-1]  # newest first
