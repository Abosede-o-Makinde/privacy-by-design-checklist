"""Score a system profile against the seven privacy-by-design principles."""

from __future__ import annotations

from dataclasses import dataclass

from src.checker.questionnaire import ALLOWED_ANSWERS, Questionnaire, SystemProfile

ANSWER_SCORES = {"yes": 1.0, "partial": 0.5, "no": 0.0}


class PrinciplesEngineError(ValueError):
    """Raised when a profile cannot be scored."""


@dataclass
class PrincipleScore:
    principle_id: str
    name: str
    short_name: str
    score: float | None
    answered: int
    skipped: int


@dataclass
class PrinciplesResult:
    system_id: str
    system_name: str
    principle_scores: list[PrincipleScore]
    overall_score: float


class PrinciplesEngine:
    """Turns questionnaire answers into 0-100 principle scores."""

    def __init__(self, questionnaire: Questionnaire | None = None) -> None:
        self.questionnaire = questionnaire or Questionnaire()

    def score(self, profile: SystemProfile) -> PrinciplesResult:
        principle_scores = [
            self._score_principle(principle, profile.answers)
            for principle in self.questionnaire.principles
        ]
        counted = [item.score for item in principle_scores if item.score is not None]
        overall = round(sum(counted) / len(counted), 1) if counted else 0.0
        return PrinciplesResult(
            system_id=profile.system_id,
            system_name=profile.name,
            principle_scores=principle_scores,
            overall_score=overall,
        )

    def _score_principle(self, principle, answers: dict[str, str]) -> PrincipleScore:
        values: list[float] = []
        skipped = 0
        for criterion in principle.criteria:
            if criterion.id not in answers:
                raise PrinciplesEngineError(f"Missing answer for '{criterion.id}'")
            raw = answers[criterion.id]
            if raw not in ALLOWED_ANSWERS:
                raise PrinciplesEngineError(f"Invalid answer for '{criterion.id}': {raw}")
            if raw == "n/a":
                skipped += 1
                continue
            values.append(ANSWER_SCORES[raw])

        score = None if not values else round((sum(values) / len(values)) * 100.0, 1)
        return PrincipleScore(
            principle_id=principle.id,
            name=principle.name,
            short_name=principle.short_name,
            score=score,
            answered=len(values),
            skipped=skipped,
        )
