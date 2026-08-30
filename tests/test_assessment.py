"""Assessment band rules."""

from __future__ import annotations

from src.checker.assessment import (
    AssessmentRunner,
    band_for,
    format_score,
    safe_output_stem,
)
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
        assert band_for(None, blocks_pass=False) == "PARTIAL"

    def test_format_score(self) -> None:
        assert format_score(67.3) == "67.3/100"
        assert format_score(None) == "n/a"

    def test_safe_output_stem(self) -> None:
        assert safe_output_stem("MEETING-NOTES-001") == "MEETING-NOTES-001"
        assert safe_output_stem("../evil/id") == ".._evil_id"
        assert safe_output_stem("  ") == "system"

    def test_meeting_notetaker_is_partial(
        self, meeting_notetaker_profile: SystemProfile
    ) -> None:
        result = AssessmentRunner().run(meeting_notetaker_profile)
        assert result.band == "PARTIAL"
        assert result.blocks_pass is True
        assert result.principle_score == 67.3
        assert len(result.checklist.items) > 0

    def test_all_yes_is_pass(self, questionnaire: Questionnaire) -> None:
        result = AssessmentRunner(questionnaire).run(_fill(questionnaire, "yes"))
        assert result.band == "PASS"
        assert result.blocks_pass is False
        assert result.checklist.items == []

    def test_all_na_is_partial_not_fail(self, questionnaire: Questionnaire) -> None:
        result = AssessmentRunner(questionnaire).run(_fill(questionnaire, "n/a"))
        assert result.principle_score is None
        assert result.default_score is None
        assert result.blocks_pass is False
        assert result.band == "PARTIAL"
