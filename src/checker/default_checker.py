"""Check Article 25(2) privacy-by-default answers."""

from __future__ import annotations

from dataclasses import dataclass

from src.checker.questionnaire import ALLOWED_ANSWERS, Questionnaire, SystemProfile

ANSWER_SCORES = {"yes": 1.0, "partial": 0.5, "no": 0.0}


class DefaultCheckerError(ValueError):
    """Raised when default-settings answers cannot be scored."""


@dataclass
class RuleResult:
    rule_id: str
    label: str
    answer: str
    score: float | None
    blocks_pass: bool


@dataclass
class DefaultCheckResult:
    system_id: str
    rule_results: list[RuleResult]
    overall_score: float
    blocks_pass: bool


class DefaultChecker:
    """Scores the four default-settings rules and applies the PASS gate."""

    def __init__(self, questionnaire: Questionnaire | None = None) -> None:
        self.questionnaire = questionnaire or Questionnaire()

    def check(self, profile: SystemProfile) -> DefaultCheckResult:
        results = [
            self._score_rule(rule, profile.default_answers)
            for rule in self.questionnaire.default_rules
        ]
        counted = [item.score for item in results if item.score is not None]
        overall = round(sum(counted) / len(counted), 1) if counted else 0.0
        blocks_pass = any(item.blocks_pass for item in results)
        return DefaultCheckResult(
            system_id=profile.system_id,
            rule_results=results,
            overall_score=overall,
            blocks_pass=blocks_pass,
        )

    def _score_rule(self, rule, answers: dict[str, str]) -> RuleResult:
        if rule.id not in answers:
            raise DefaultCheckerError(f"Missing default answer for '{rule.id}'")
        raw = answers[rule.id]
        if raw not in ALLOWED_ANSWERS:
            raise DefaultCheckerError(f"Invalid default answer for '{rule.id}': {raw}")
        if raw == "n/a":
            return RuleResult(
                rule_id=rule.id,
                label=rule.label,
                answer=raw,
                score=None,
                blocks_pass=False,
            )
        return RuleResult(
            rule_id=rule.id,
            label=rule.label,
            answer=raw,
            score=round(ANSWER_SCORES[raw] * 100.0, 1),
            blocks_pass=raw == "no",
        )
