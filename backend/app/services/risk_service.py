"""Transparent weighted risk scoring. Factors are persisted and returned to the UI."""

from typing import Any, Dict, List

from app.database import detection_rules as rules_repo
from app.utils.time import clamp

SEVERITY_FROM_SCORE = (
    (30, "low"),
    (60, "medium"),
    (80, "high"),
    (100, "critical"),
)


def severity_for_score(score: int) -> str:
    for limit, label in SEVERITY_FROM_SCORE:
        if score <= limit:
            return label
    return "critical"


class RiskService:
    def load_weights(self) -> Dict[str, int]:
        weights = {}
        for rule in rules_repo.select():
            if rule.get("enabled"):
                weights[rule["rule_name"]] = int(rule.get("weight") or 0)
        return weights

    def score(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        weights = self.load_weights()
        factors = []
        total = 0
        seen = set()
        for finding in findings:
            name = finding.get("rule_name")
            if name in seen:
                continue
            seen.add(name)
            points = int(finding.get("weight") or weights.get(name) or 0)
            if points <= 0:
                continue
            total += points
            factors.append(
                {
                    "indicator": name,
                    "points": points,
                    "detail": finding.get("detail"),
                    "severity": finding.get("severity"),
                }
            )
        score = clamp(total)
        return {
            "risk_score": score,
            "severity": severity_for_score(score),
            "factors": factors,
            "max_score": 100,
            "formula": "sum(enabled rule weights for matched unique indicators), clamped 0–100",
            "bands": {
                "low": "0–30",
                "medium": "31–60",
                "high": "61–80",
                "critical": "81–100",
            },
        }
