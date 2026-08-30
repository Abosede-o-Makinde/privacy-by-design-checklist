"""Assessment band rules."""

from __future__ import annotations

from src.checker.assessment import AssessmentRunner, band_for
from src.checker.questionnaire import Questionnaire, SystemProfile


def _fill(questionnaire: Questionnaire, value: str) -> SystemProfile:
    answers = {criterion_id: value for criterion_id in questionnaire.criterion_ids}
    defaults = {rule_id: value for rule_id in questionnaire.default_ids}
    return SystemProfile(
        system_id="T-001",
        name="Test system",
        answers=answers,
        default_answers=defaults,
    )


class TestAssessment:
    def test_band_pass_partial_fail(self) -> None:
        assert band_for(90, blocks_pass=False) == "PASS"
        assert band_for(90, blocks_pass=True) == "PARTIAL"
        assert band_for(65, blocks_pass=False) == "PARTIAL"
        assert band_for(40, blocks_pass=False) == "FAIL"

    def test_staff_access_is_partial(self, staff_access_profile: SystemProfile) -> None:
        result = AssessmentRunner().run(staff_access_profile)
        assert result.band == "PARTIAL"
        assert result.blocks_pass is True
        assert result.principle_score == 67.3
        assert len(result.checklist.items) > 0

    def test_all_yes_is_pass(self, questionnaire: Questionnaire) -> None:
        result = AssessmentRunner(questionnaire).run(_fill(questionnaire, "yes"))
        assert result.band == "PASS"
        assert result.blocks_pass is False
        assert result.checklist.items == []
