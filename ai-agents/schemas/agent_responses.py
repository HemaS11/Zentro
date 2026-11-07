from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AgentResponse:
    agent: str
    decision: str
    confidence: float
    risk_score: int
    matched_policy: str
    notes: Optional[str] = None


@dataclass
class AgentBatchResponse:
    transaction: dict
    results: List[AgentResponse]
