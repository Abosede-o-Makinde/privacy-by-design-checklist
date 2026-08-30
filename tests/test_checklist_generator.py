"""Prioritised go-live checklist from no/partial answers."""

from __future__ import annotations

from src.checker.checklist_generator import ChecklistGenerator
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


class TestChecklistGenerator:
    def test_all_yes_has_no_items(self, questionnaire: Questionnaire) -> None:
        result = ChecklistGenerator(questionnaire).generate(_fill(questionnaire, "yes"))
        assert result.items == []

    def test_na_is_not_listed(self, questionnaire: Questionnaire) -> None:
        profile = _fill(questionnaire, "yes")
        profile.answers["p7-human-review"] = "n/a"
        profile.default_answers["extent"] = "n/a"
        result = ChecklistGenerator(questionnaire).generate(profile)
        ids = [item.item_id for item in result.items]
        assert "p7-human-review" not in ids
        assert "extent" not in ids

    def test_defaults_come_before_principles(self, questionnaire: Questionnaire) -> None:
        profile = _fill(questionnaire, "yes")
        profile.default_answers["storage"] = "no"
        profile.answers["p5-encryption"] = "no"
        ids = [
            item.item_id
            for item in ChecklistGenerator(questionnaire).generate(profile).items
        ]
        assert ids[0] == "storage"
        assert ids[1] == "p5-encryption"

    def test_no_ranks_above_partial_in_the_same_band(
        self, questionnaire: Questionnaire
    ) -> None:
        profile = _fill(questionnaire, "yes")
        profile.default_answers["extent"] = "partial"
        profile.default_answers["storage"] = "no"
        ids = [
            item.item_id
            for item in ChecklistGenerator(questionnaire).generate(profile).items
        ]
        assert ids == ["storage", "extent"]

    def test_meeting_notetaker_order_is_stable(
        self, meeting_notetaker_profile: SystemProfile
    ) -> None:
        result = ChecklistGenerator().generate(meeting_notetaker_profile)
        ids = [item.item_id for item in result.items]
        assert ids[:4] == ["amount", "storage", "extent", "accessibility"]
        assert ids[4:6] == ["p5-disposal", "p5-access-control"]
        assert ids[6:8] == ["p2-opt-in", "p6-audit"]
        assert ids[8] == "p2-optional-off"
        assert "p7-human-review" not in ids
        assert "p4-fallback" not in ids
        assert result.items[0].answer == "no"
        assert result.items[2].answer == "partial"
