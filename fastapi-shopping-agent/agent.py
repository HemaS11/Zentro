
"""
Mandate Pay - AI Shopping & Research Agent

Workflow:
1. Understand the shopping request using Gemini.
2. Fall back to rule-based parsing if Gemini is unavailable.
3. Search the products.py CATALOG.
4. Filter products by category and budget.
5. Rank products based on keyword relevance and rating.
6. Return product recommendations.

"""

import json
import math
import os
import re
import sys
from importlib.util import find_spec

from dotenv import load_dotenv

load_dotenv()

# ==================================================
# CONFIGURATION
# ==================================================

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
HAVE_LANGGRAPH = find_spec("langgraph") is not None

CATEGORIES = [
    "Laptops",
    "Textbooks",
    "Headphones",
    "Accessories",
]


# ==================================================
# TEXT NORMALIZATION
# ==================================================

def _stem(word: str) -> str:
    """Simple keyword normalization."""

    word = word.lower().strip()

    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"

    if word.endswith(("ches", "shes", "sses", "xes", "zes")) and len(word) > 4:
        return word[:-2]

    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]

    return word


# ==================================================
# CATEGORY DETECTION
# ==================================================

def _extract_category(query: str):
    """Identify product category from the user's request."""

    q = query.lower()

    aliases = {
        "Laptops": [
            "laptop", "laptops", "notebook", "notebooks", "computer", "computers"
        ],
        "Textbooks": [
            "textbook", "textbooks", "book", "books"
        ],
        "Headphones": [
            "headphone", "headphones", "earphone",
            "earphones", "earbud", "earbuds",
            "neckband", "airpods"
        ],
        "Accessories": [
            "accessory", "accessories", "calculator",
            "mouse", "mice", "keyboard", "backpack", "bag"
        ],
    }

    for category, words in aliases.items():
        for word in words:
            if re.search(r"\b" + re.escape(word) + r"\b", q):
                return category

    return None


# ==================================================
# BUDGET EXTRACTION
# ==================================================

def _extract_budget(query: str):
    """Extract maximum shopping budget in INR."""

    q = query.lower().replace(",", "")

    unit = r"(k|thousand|lakhs?|l)"
    patterns = [
        rf"(?:do not exceed|don't exceed|not exceed|exceed|under|below|less than|within|up to|upto|maximum|max)\s*(?:₹|rs\.?\s*)?(\d+(?:\.\d+)?)\s*{unit}?",
        rf"(?:₹|rs\.?\s*)(\d+(?:\.\d+)?)\s*{unit}?",
        rf"(?:budget of|budget is|budget)\s*(?:₹|rs\.?\s*)?(\d+(?:\.\d+)?)\s*{unit}?",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)

        if match:
            amount = float(match.group(1))
            amount_unit = match.group(2)

            if amount_unit in ("k", "thousand"):
                amount *= 1000
            elif amount_unit in ("lakh", "lakhs", "l"):
                amount *= 100000

            return amount if math.isfinite(amount) and amount > 0 else None

    return None


def parse_budget(query: str) -> tuple[float | None, str | None]:
    """Compatibility helper returning the extracted budget and matched text."""

    return _extract_budget(query), None


def inr(amount: float) -> str:
    """Format an amount as Indian rupees."""

    return f"₹{amount:,.0f}"


def _extract_purpose(query: str) -> str | None:
    q = query.lower()
    purposes = (
        ("online classes", ("online class", "online classes", "virtual class")),
        ("coding", ("coding", "programming", "developer", "development")),
        ("gaming", ("gaming", "gamer", "games")),
        ("creative work", ("design", "video editing", "creative")),
        ("work", ("office work", "work", "business")),
        ("study", ("study", "student", "college", "school")),
    )
    for purpose, aliases in purposes:
        if any(alias in q for alias in aliases):
            return purpose
    return None


# ==================================================
# RULE-BASED PARSER
# ==================================================

def rule_parse(query: str) -> dict:
    """Parse shopping requests without Gemini."""

    category = _extract_category(query)
    budget = _extract_budget(query)
    purpose = _extract_purpose(query)

    cleaned = query.lower()

    cleaned = re.sub(
        r"(?:do not exceed|don't exceed|not exceed|exceed|under|below|less than|within|up to|upto|maximum|max|budget of|budget is|budget)",
        " ",
        cleaned,
    )

    cleaned = re.sub(
        r"(?:₹|rs\.?\s*)?\s*\d+(?:,\d+)*(?:\.\d+)?\s*(?:k|thousand|lakhs?|l)?",
        " ",
        cleaned,
    )

    ignored_words = {
        "a", "an", "the", "for", "with", "and", "or",
        "buy", "want", "need", "show", "find", "search",
        "best", "good", "please", "me", "some", "to",
        "of", "in", "my", "get", "recommend",
        "online", "class", "do", "not", "exceed",
    }

    category_words = {
        "laptop", "laptops", "notebook", "notebooks",
        "textbook", "textbooks", "book", "books",
        "headphone", "headphones", "earphone", "earphones",
        "earbud", "earbuds", "neckband", "airpods",
        "accessory", "accessories", "calculator",
        "mouse", "mice", "keyboard", "backpack", "bag",
    }

    keywords = [
        _stem(word)
        for word in re.findall(r"[a-zA-Z0-9]+", cleaned)
        if word not in ignored_words
        and word not in category_words
    ]

    purpose_keywords = {
        "online classes": ["calls"],
        "coding": ["coding"],
        "gaming": ["gaming"],
        "creative work": ["design"],
        "work": ["work"],
        "study": ["student"],
    }
    for keyword in purpose_keywords.get(purpose, []):
        if keyword not in keywords:
            keywords.append(keyword)

    return {
        "category": category,
        "max_budget": budget,
        "purpose": purpose,
        "keywords": keywords,
        "parser": "rules",
    }


# ==================================================
# GEMINI AI PARSER
# ==================================================

def gemini_parse(query: str):
    """
    Use Gemini to understand natural-language shopping requests.

    Requests a JSON response and validates its fields before using them.
    """

    key = os.getenv("GEMINI_API_KEY", "").strip()

    if not key:
        print(
            "[agent] Gemini API key missing. Using rule parser.",
            file=sys.stderr,
        )
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)

        prompt = f"""
You are an intelligent shopping research assistant
for an Indian shopping platform.

Understand the user's shopping request.

Available product categories:
{CATEGORIES}

Return ONLY valid JSON using this structure:

{{
    "category": "Laptops, Textbooks, Headphones, Accessories, or null",
    "max_budget": 50000,
    "keywords": ["relevant", "product", "requirements"]
}}

Instructions:

1. Identify the correct product category.
2. Extract the maximum budget in Indian rupees.
3. Convert 50k into 50000.
4. Convert 1 lakh into 100000.
5. Identify useful requirements such as gaming,
   16GB RAM, SSD, wireless, Bluetooth and battery life.
6. Do not include category names as keywords.
7. Do not invent requirements.
8. If no budget is mentioned, return null.
9. If the category is unclear, return null.
10. Identify the main purpose as coding, gaming, online classes,
    creative work, work, study, or null.
11. Return valid JSON only.

User shopping request:
{query}
"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "category": {
                            "type": "STRING",
                            "nullable": True,
                            "enum": CATEGORIES,
                        },
                        "max_budget": {
                            "type": "NUMBER",
                            "nullable": True,
                        },
                        "purpose": {
                            "type": "STRING",
                            "nullable": True,
                        },
                        "keywords": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                        },
                    },
                    "required": ["category", "max_budget", "purpose", "keywords"],
                },
            ),
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        data = json.loads(response.text)

        category = data.get("category")
        budget = data.get("max_budget")
        keywords = data.get("keywords", [])
        purpose = data.get("purpose")

        if category not in CATEGORIES:
            category = _extract_category(str(category or "")) or _extract_category(query)

        if isinstance(budget, (int, float)) and not isinstance(budget, bool):
            budget = float(budget)
            if not math.isfinite(budget) or budget <= 0:
                budget = _extract_budget(query)
        else:
            budget = _extract_budget(query)

        if not isinstance(keywords, list):
            keywords = []

        rule_result = rule_parse(query)
        normalized_keywords = [
            _stem(str(word))
            for word in keywords
            if isinstance(word, str) and word.strip()
        ]
        for word in rule_result["keywords"]:
            if word not in normalized_keywords:
                normalized_keywords.append(word)

        return {
            "category": category,
            "max_budget": budget,
            "purpose": purpose if isinstance(purpose, str) and purpose.strip()
            else rule_result["purpose"],
            "keywords": normalized_keywords,
            "parser": "gemini",
        }

    except Exception as error:
        print(
            f"[agent] Gemini unavailable, using rule parser: {error}",
            file=sys.stderr,
        )
        return None


# ==================================================
# REQUEST UNDERSTANDING
# ==================================================

def understand(query: str) -> dict:
    """Try Gemini first, then fall back to rule parsing."""

    parsed = gemini_parse(query)

    if parsed is not None:
        return parsed

    return rule_parse(query)


# ==================================================
# PRODUCT KEYWORD MATCHING
# ==================================================

def _hits(parsed: dict, product: dict) -> int:
    """Calculate keyword relevance score."""

    haystack = (
        str(product.get("name", "")) + " " +
        str(product.get("description", "")) + " " +
        str(product.get("tags", ""))
    ).lower()

    score = 0

    for keyword in parsed.get("keywords", []):
        keyword = str(keyword).lower().strip()

        if keyword and keyword in haystack:
            score += 1

    return score


# ==================================================
# CATEGORY MATCHING
# ==================================================

def _category_matches(requested: str, actual: str) -> bool:
    """Handle singular and plural category names."""

    if not requested:
        return True

    return _stem(requested.lower()) == _stem(actual.lower())


# ==================================================
# PRODUCT CATALOG SEARCH
# ==================================================

def search_catalog(parsed: dict) -> dict:
    """Search the actual CATALOG from products.py."""

    from products import CATALOG

    matches = []
    within = []
    excluded = []

    category = parsed.get("category")
    max_budget = parsed.get("max_budget")

    for product in CATALOG:

        # Category filtering
        if category and not _category_matches(
            category,
            product.get("category", ""),
        ):
            continue

        # Keyword relevance
        score = _hits(parsed, product)

        if not category and (not parsed.get("keywords") or score == 0):
            continue

        item = {
            **product,
            "match_score": score,
        }

        matches.append(item)

        # Budget filtering
        if max_budget is not None:
            if product["price"] > max_budget:
                excluded.append({
                    **item,
                    "reason": (
                        f"Price {inr(product['price'])} exceeds your "
                        f"{inr(max_budget)} budget."
                    ),
                })
                continue

        within.append(item)

    # Rank products by keyword relevance and rating
    sort_key = lambda p: (
        p["match_score"],
        p.get("rating", 0),
        -p["price"],
    )

    matches.sort(key=sort_key, reverse=True)
    within.sort(key=sort_key, reverse=True)
    excluded.sort(key=sort_key, reverse=True)

    return {
        "matches": matches,
        "within": within,
        "excluded": excluded,
    }


# ==================================================
# RECOMMENDATION ENGINE
# ==================================================

def recommend_products(
    products: list,
    limit: int = 5,
) -> list:
    """Return the best matching products."""

    return products[:limit]


# ==================================================
# COMPLETE SHOPPING AGENT
# ==================================================

def run_agent(query: str) -> dict:
    """
    Complete shopping research workflow.

    Returns:
        query
        parsed
        matches
        within
        excluded
        recommended
        summary
        parser
        engine
    """

    parsed = understand(query)

    search_result = search_catalog(parsed)

    matches = search_result["matches"]
    within = search_result["within"]
    excluded = search_result["excluded"]

    recommended = recommend_products(within)

    for rank, product in enumerate(recommended, start=1):
        product["rank"] = rank
        matched_keywords = list(dict.fromkeys(
            keyword
            for keyword in parsed.get("keywords", [])
            if keyword.lower() in (
                str(product.get("name", "")) + " "
                + str(product.get("description", "")) + " "
                + str(product.get("tags", ""))
            ).lower()
        ))[:3]
        product["badges"] = matched_keywords or ["Top match"]
        reasons = []
        if matched_keywords:
            reasons.append("Matches " + ", ".join(matched_keywords))
        elif parsed.get("category"):
            reasons.append("Top match in " + parsed["category"])
        if parsed.get("max_budget") is not None:
            reasons.append("within your budget")
        reasons.append(f"rated {product.get('rating', 0):.1f}/5")
        product["why_recommended"] = "; ".join(reasons) + "."

    if recommended:
        summary = (
            f"Found {len(within)} matching products within "
            f"your budget. Here are the top "
            f"{len(recommended)} recommendations."
        )

    elif matches:
        cheapest = min(matches, key=lambda product: product["price"])
        summary = (
            "Matching products were found, but none are within your budget. "
            f"The cheapest option is {cheapest['name']} at {inr(cheapest['price'])}."
        )

    else:
        summary = (
            "No matching products were found in the catalogue."
        )

    return {
        "query": query,
        "parsed": parsed,
        "matches": matches,
        "within": within,
        "excluded": excluded,
        "recommended": recommended,
        "summary": summary,
        "parser": parsed.get("parser", "rules"),
        "engine": "shopping-agent",
    }


# ==================================================
# TERMINAL OUTPUT
# ==================================================

def main():

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input(
            "Enter your shopping request: "
        ).strip()

    if not query:
        print("Please enter a shopping request.")
        return

    result = run_agent(query)

    print("\n==============================================")
    print("       MANDATE PAY - AI SHOPPING AGENT")
    print("==============================================")

    print("\nUSER REQUEST:")
    print(result["query"])

    print("\nAI UNDERSTANDING:")
    print(
        json.dumps(
            result["parsed"],
            indent=4,
        )
    )

    print("\nPARSER USED:")
    print(result["parser"].upper())

    print("\nSUMMARY:")
    print(result["summary"])

    print("\nRECOMMENDED PRODUCTS:")
    print("----------------------------------------------")

    if not result["recommended"]:
        print("No recommendations available.")

    for index, product in enumerate(
        result["recommended"],
        start=1,
    ):

        print(f"\n{index}. {product['name']}")

        print(
            f"   Product ID : {product['id']}"
        )

        print(
            f"   Price      : Rs. {product['price']}"
        )

        print(
            f"   Category   : {product['category']}"
        )

        print(
            f"   Rating     : {product['rating']}/5"
        )

        print(
            f"   Match Score: {product['match_score']}"
        )

        print(
            f"   Description: {product['description']}"
        )

        print(
            f"   Link       : {product['link']}"
        )

    print("\nPRODUCTS EXCLUDED BY BUDGET:")

    if not result["excluded"]:
        print("None.")

    for product in result["excluded"]:
        print(
            f"- {product['name']} "
            f"(Rs. {product['price']})"
        )

    print("\nTOTAL MATCHES:", len(result["matches"]))
    print("WITHIN BUDGET:", len(result["within"]))

    print("\n==============================================")


# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":
    main()
