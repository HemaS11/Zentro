from typing import Any, Dict, List, Optional

from config import get_agent_config
from mandate_creator import MandateCreator
from policy_judge import PolicyJudge
from receipt_auditor import ReceiptAuditor
from research_agent import ResearchAgent
from risk_agent import RiskAgent


class AgentCoordinator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_agent_config()
        self.agents = {
            "Mandate Creator": MandateCreator(self.config),
            "Product Research": ResearchAgent(self.config),
            "Policy Judge": PolicyJudge(self.config),
            "Risk Detection": RiskAgent(self.config),
            "Receipt Auditor": ReceiptAuditor(self.config),
        }

    def _build_result(self, agent_name: str, result: Any) -> Dict[str, Any]:
        return {
            "agent": agent_name,
            "decision": getattr(result, "decision", "REVIEW"),
            "confidence": float(getattr(result, "confidence", 0.0)),
            "risk_score": int(getattr(result, "risk_score", 0)),
            "matched_policy": getattr(result, "matched_policy", "Not evaluated"),
            "notes": getattr(result, "notes", ""),
        }

    def _final_authorization(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        policy_decision = "REVIEW"
        max_risk = 0
        for item in results:
            max_risk = max(max_risk, int(item.get("risk_score", 0)))
            if item["agent"] == "Policy Judge":
                policy_decision = str(item.get("decision", "REVIEW")).upper()

        if policy_decision == "BLOCK":
            decision = "BLOCK"
            requires_human_approval = False
        elif policy_decision == "ESCALATE" or max_risk >= 70:
            decision = "ESCALATE"
            requires_human_approval = True
        elif policy_decision == "APPROVE" and max_risk < 40:
            decision = "APPROVE"
            requires_human_approval = False
        else:
            decision = "REVIEW"
            requires_human_approval = True

        return {
            "decision": decision,
            "authorized": False,
            "requires_human_approval": requires_human_approval,
            "risk_score": max_risk,
        }

    def run_all(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        transaction_copy = dict(transaction or {})
        mandate = transaction_copy.get("mandate") or transaction_copy.get("policy") or {}
        if not mandate and (transaction_copy.get("mandate_text") or transaction_copy.get("instruction")):
            mandate = self.agents["Mandate Creator"].evaluate(transaction_copy).mandate or {}
        if mandate:
            transaction_copy["mandate"] = mandate

        ordered_names = [
            "Mandate Creator",
            "Product Research",
            "Policy Judge",
            "Risk Detection",
            "Receipt Auditor",
        ]
        results: List[Dict[str, Any]] = []
        for name in ordered_names:
            try:
                result = self.agents[name].evaluate(transaction_copy)
                results.append(self._build_result(name, result))
            except Exception as exc:  # pragma: no cover
                results.append(
                    {
                        "agent": name,
                        "decision": "REVIEW",
                        "confidence": 0.0,
                        "risk_score": 0,
                        "matched_policy": "Error",
                        "notes": f"Agent failed gracefully: {exc}",
                    }
                )

        final = self._final_authorization(results)
        return {
            "success": True,
            "transaction_id": transaction_copy.get("id", "TXN-UNKNOWN"),
            "mandate": mandate or {},
            "results": results,
            "final_authorization": final,
        }

    def run_selected(self, agent_name: str, transaction: Dict[str, Any]) -> Dict[str, Any]:
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        result = self.agents[agent_name].evaluate(transaction)
        return self._build_result(agent_name, result)
