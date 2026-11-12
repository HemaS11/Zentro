# Zentro – AI Shopping & Research Agent (Module 3)

Searches products from plain English, filters by budget, compares the rest, and
sends the chosen product to Hema's Policy Engine (APPROVE / BLOCK / ESCALATE).
The agent recommends. It never authorizes payments.

## Run in VS Code
1. Open this folder in VS Code (File > Open Folder).
2. Terminal > New Terminal, then:

   **Windows**
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```
   **macOS / Linux**
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```
3. Your browser opens http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs

## Optional settings (copy `.env.example` to `.env`)
- `GEMINI_API_KEY` – Gemini reads the request. Without it, a built-in rule parser is used.
- `GEMINI_MODEL` – model name passed to the Gemini API; defaults to `gemini-3.8-flash`.
- `POLICY_ENGINE_URL` – policy API URL. Defaults to this app's
  `http://127.0.0.1:8000/api/policy/evaluate` local policy engine. The Technology
  mandate approves up to ₹25,000, escalates up to ₹80,000, and blocks above;
  Education has lower limits. An unreachable external service or invalid
  response results in ESCALATE, never APPROVE. The API validates the product
  ID, name, category and amount against the catalogue before evaluating it.

The app only accepts catalogue product IDs for policy checks and uses the
catalogue's price and category, not values supplied by the browser. The payment
button creates a local demo receipt; this project does not move real money.

## Files
| File | Purpose |
|---|---|
| `main.py` | FastAPI server, routes and in-memory transaction log |
| `store.py` | App state and the purchase flow (check, allow/reject, pay) |
| `seed.py`, `agents_demo.py` | Dummy history, risk scoring and receipt audit |
| `mandates.py` | Spending limits used by the local policy engine |
| `policy_engine.py` | Local Mandate Pay policy rules and authorization decisions |
| `agent.py` | Gemini JSON parsing with rule fallback, product search and ranking |
| `products.py` | Mock catalog (swap for a real Product API) |
| `policy_client.py` | Connection to the Policy Engine |
| `static/index.html` | Zentro dashboard (Dashboard, Product Research, AI Agents, Transactions, Mandates, Analytics, Settings) |
| `test_agent.py` | `python test_agent.py` checks shopping, Gemini JSON configuration, policy decisions and flow |

CLI check without the UI: `python agent.py "laptop under 50k"`

## Demo flow
1. **Product Research**: search, e.g. "laptops under 50k". Gemini parses the request when configured; rules are used if Gemini fails. The agent filters and ranks.
2. **Check with Policy Engine**: the local policy API applies the mandates, and the Risk Detection demo scores the price against past purchases.
3. **ESCALATE** waits for you: use *Allow* or *Reject* (here or under Transactions; the bell shows waiting items).
4. **Pay now (demo)**: no real payment. A dummy invoice is created and the Receipt Auditor checks GSTIN format and totals.
5. **Mandates**: create a rule for a category and it applies immediately. Paying raises that mandate's spend.

Tests mock Gemini so they run deterministically without making external API calls.
Seed data lives in `seed.py` (10 sample transactions, one with a receipt
mismatch). Searches, decisions, mandates and receipts are kept in memory;
restarting the server resets them.
