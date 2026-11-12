"""Spending mandates evaluated by the local Mandate Pay policy engine.
`spent` is sample data until a payments module reports real spend."""

MANDATES = [
    {"id": "MD-TECH-01", "name": "Technology Purchases", "categories": ["Laptops", "Headphones", "Accessories"],
     "max_per_purchase": 80000, "approval_above": 25000, "monthly_budget": 150000, "spent": 52273,
     "status": "Active", "expires": "Dec 31, 2026"},
    {"id": "MD-EDU-01", "name": "Education & Books", "categories": ["Textbooks"],
     "max_per_purchase": 5000, "approval_above": 3000, "monthly_budget": 20000, "spent": 2049,
     "status": "Active", "expires": "Dec 31, 2026"},
]


def find(category: str):
    return next((m for m in MANDATES if category in m["categories"]), None)


def add_mandate(data: dict) -> dict:
    m = {"id": f"MD-{len(MANDATES) + 1:02d}-{data['category'][:3].upper()}", "name": data["name"],
         "categories": [data["category"]], "max_per_purchase": data["max_per_purchase"],
         "approval_above": data["approval_above"], "monthly_budget": data["monthly_budget"],
         "spent": 0, "status": "Active", "expires": "Dec 31, 2026"}
    MANDATES.append(m)
    return m
