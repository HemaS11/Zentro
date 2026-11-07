
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from google import genai


@dataclass
class ResearchAgentResult:
    agent: str = "Product Research"
    decision: str = "REVIEW"
    confidence: float = 0.0
    risk_score: int = 0
    matched_policy: str = "Not evaluated"
    notes: str = ""


class ResearchAgent:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = self.config.get("gemini_api_key", "")
        self.model = self.config.get("model", "gemini-3.8-flash")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def evaluate(self, transaction: Dict[str, Any]) -> ResearchAgentResult:
        if not self.client:
            return ResearchAgentResult(
                notes="Demo mode: Gemini API key is not configured."
            )

        prompt = f"""
        You are Zentro's Product Research Agent.

        Analyse the following purchase information:
        {json.dumps(transaction, default=str)}

        Evaluate:
        1. Merchant and product information.
        2. Product category.
        3. Price reasonableness based only on supplied evidence.
        4. Seller information and missing details.
        5. Whether further human review is needed.

        Never invent products, prices, sellers or market research.
        If information is missing, clearly state that.

        Return ONLY valid JSON:
        {{
          "decision": "REVIEW",
          "confidence": 0.0,
          "risk_score": 0,
          "matched_policy": "category or unknown",
          "notes": "explanation"
        }}

        This agent provides research recommendations only.
        It must never authorize or capture payments.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": self.config.get("temperature", 0.2)}
            )

            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            data = json.loads(text)

            return ResearchAgentResult(
                decision="REVIEW",
                confidence=max(0.0, min(1.0, float(data.get("confidence", 0.0)))),
                risk_score=max(0, min(100, int(data.get("risk_score", 0)))),
                matched_policy=str(data.get("matched_policy", "Unknown")),
                notes=str(data.get("notes", "Research completed.")),
            )

        except Exception as error:
            return ResearchAgentResult(
                decision="REVIEW",
                notes=f"Gemini research unavailable: {error}"
            )
