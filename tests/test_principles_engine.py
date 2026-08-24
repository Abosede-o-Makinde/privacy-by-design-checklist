"""Scoring rules for the seven privacy-by-design principles."""

from __future__ import annotations

import pytest

from src.checker.principles_engine import PrinciplesEngine, PrinciplesEngineError
from src.checker.questionnaire import Questionnaire, SystemProfile


def _fill(questionnaire: Questionnaire, value: str) -> SystemProfile:
    answers = {criterion_id: value for criterion_id in questionnaire.criterion_ids}
    defaults = {rule_id: "yes" for rule_id in questionnaire.default_ids}
    return SystemProfile(
        system_id="T-001",
        name="Test system",
        answers=answers,
        default_answers=defaults,
    )


class TestPrinciplesEngine:
    def test_all_yes_scores_100(self, questionnaire: Questionnaire) -> None:
        result = PrinciplesEngine(questionnaire).score(_fill(questionnaire, "yes"))
        assert result.overall_score == 100.0
        assert all(item.score == 100.0 for item in result.principle_scores)

    def test_all_no_scores_zero(self, questionnaire: Questionnaire) -> None:
        result = PrinciplesEngine(questionnaire).score(_fill(questionnaire, "no"))
        assert result.overall_score == 0.0
        assert all(item.score == 0.0 for item in result.principle_scores)

    def test_na_is_excluded_from_a_principle(self, questionnaire: Questionnaire) -> None:
        profile = _fill(questionnaire, "yes")
        profile.answers["p7-human-review"] = "n/a"
        result = PrinciplesEngine(questionnaire).score(profile)
        user_centric = next(item for item in result.principle_scores if item.principle_id == "p7")
        assert user_centric.skipped == 1
        assert user_centric.answered == 2
        assert user_centric.score == 100.0

    def test_all_na_principle_is_dropped_from_overall(
        self, questionnaire: Questionnaire
    ) -> None:
        profile = _fill(questionnaire, "yes")
        for criterion in questionnaire.principles[0].criteria:
            profile.answers[criterion.id] = "n/a"
        result = PrinciplesEngine(questionnaire).score(profile)
        first = result.principle_scores[0]
        assert first.score is None
        assert result.overall_score == 100.0

    def test_staff_access_sample_is_mixed(self, staff_access_profile: SystemProfile) -> None:
        result = PrinciplesEngine().score(staff_access_profile)
        by_id = {item.principle_id: item.score for item in result.principle_scores}
        assert by_id["p1"] == 83.3
        assert by_id["p2"] == 33.3
        assert by_id["p3"] == 50.0
        assert by_id["p4"] == 100.0
        assert by_id["p5"] == 62.5
        assert by_id["p6"] == 66.7
        assert by_id["p7"] == 75.0
        assert result.overall_score == 67.3

    def test_missing_answer_is_rejected(self, questionnaire: Questionnaire) -> None:
        profile = _fill(questionnaire, "yes")
        del profile.answers["p1-review"]
        with pytest.raises(PrinciplesEngineError, match="p1-review"):
            PrinciplesEngine(questionnaire).score(profile)

    def test_unknown_answer_is_rejected(self, questionnaire: Questionnaire) -> None:
        profile = _fill(questionnaire, "yes")
        profile.answers["p1-review"] = "maybe"
        with pytest.raises(PrinciplesEngineError, match="p1-review"):
            PrinciplesEngine(questionnaire).score(profile)
