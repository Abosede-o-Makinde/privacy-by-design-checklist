"""Article 25(2) default-settings gate."""

from __future__ import annotations

import pytest

from src.checker.default_checker import DefaultChecker, DefaultCheckerError
from src.checker.questionnaire import Questionnaire, SystemProfile


def _fill(questionnaire: Questionnaire, default_value: str) -> SystemProfile:
    answers = {criterion_id: "yes" for criterion_id in questionnaire.criterion_ids}
    defaults = {rule_id: default_value for rule_id in questionnaire.default_ids}
    return SystemProfile(
        system_id="T-001",
        name="Test system",
        answers=answers,
        default_answers=defaults,
    )


class TestDefaultChecker:
    def test_all_yes_does_not_block_pass(self, questionnaire: Questionnaire) -> None:
        result = DefaultChecker(questionnaire).check(_fill(questionnaire, "yes"))
        assert result.overall_score == 100.0
        assert result.blocks_pass is False

    def test_any_no_blocks_pass(self, questionnaire: Questionnaire) -> None:
        profile = _fill(questionnaire, "yes")
        profile.default_answers["storage"] = "no"
        result = DefaultChecker(questionnaire).check(profile)
        assert result.blocks_pass is True
        storage = next(item for item in result.rule_results if item.rule_id == "storage")
        assert storage.score == 0.0

    def test_na_does_not_block_pass(self, questionnaire: Questionnaire) -> None:
        profile = _fill(questionnaire, "yes")
        profile.default_answers["extent"] = "n/a"
        result = DefaultChecker(questionnaire).check(profile)
        assert result.blocks_pass is False
        extent = next(item for item in result.rule_results if item.rule_id == "extent")
        assert extent.score is None
        assert result.overall_score == 100.0

    def test_staff_access_sample_blocks_pass(
        self, staff_access_profile: SystemProfile
    ) -> None:
        result = DefaultChecker().check(staff_access_profile)
        assert result.blocks_pass is True
        by_id = {item.rule_id: item.score for item in result.rule_results}
        assert by_id["amount"] == 0.0
        assert by_id["extent"] == 50.0
        assert by_id["storage"] == 0.0
        assert by_id["accessibility"] == 50.0
        assert result.overall_score == 25.0

    def test_missing_answer_is_rejected(self, questionnaire: Questionnaire) -> None:
        profile = _fill(questionnaire, "yes")
        del profile.default_answers["amount"]
        with pytest.raises(DefaultCheckerError, match="amount"):
            DefaultChecker(questionnaire).check(profile)

    def test_unknown_answer_is_rejected(self, questionnaire: Questionnaire) -> None:
        profile = _fill(questionnaire, "yes")
        profile.default_answers["amount"] = "maybe"
        with pytest.raises(DefaultCheckerError, match="amount"):
            DefaultChecker(questionnaire).check(profile)
