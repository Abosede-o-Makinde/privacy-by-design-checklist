"""Questionnaire loading and answer normalisation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.checker.questionnaire import Questionnaire, QuestionnaireError


def _minimal_principles() -> dict:
    return {
        "principles": [
            {
                "id": f"p{i}",
                "name": f"Principle {i}",
                "short_name": f"P{i}",
                "criteria": [
                    {
                        "id": f"p{i}-a",
                        "question": "Q?",
                        "gdpr_articles": ["25"],
                    }
                ],
            }
            for i in range(1, 8)
        ]
    }


def _minimal_defaults() -> dict:
    return {
        "rules": [
            {"id": "amount", "label": "Amount", "question": "Q?"},
            {"id": "extent", "label": "Extent", "question": "Q?"},
            {"id": "storage", "label": "Storage", "question": "Q?"},
            {"id": "accessibility", "label": "Accessibility", "question": "Q?"},
        ]
    }


def _write_config(tmp_path: Path) -> Path:
    config = tmp_path / "config"
    config.mkdir()
    (config / "pbdd_principles.json").write_text(
        json.dumps(_minimal_principles()), encoding="utf-8"
    )
    (config / "default_settings_rules.json").write_text(
        json.dumps(_minimal_defaults()), encoding="utf-8"
    )
    return config


class TestQuestionnaire:
    def test_answers_are_normalised(self, tmp_path: Path) -> None:
        q = Questionnaire(config_dir=_write_config(tmp_path))
        answers = {cid: "YES" for cid in q.criterion_ids}
        answers[q.criterion_ids[0]] = " Partial "
        defaults = {rid: "No" for rid in q.default_ids}
        profile = q.from_dict(
            {
                "system_id": "SYS-1",
                "name": "Demo",
                "answers": answers,
                "default_answers": defaults,
            }
        )
        assert profile.answers[q.criterion_ids[0]] == "partial"
        assert profile.default_answers["amount"] == "no"

    def test_malformed_principles_raise_questionnaire_error(
        self, tmp_path: Path
    ) -> None:
        config = tmp_path / "config"
        config.mkdir()
        (config / "pbdd_principles.json").write_text(
            json.dumps(
                {
                    "principles": [
                        {
                            "id": "p1",
                            "name": "Broken",
                            "criteria": [{"question": "missing id"}],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (config / "default_settings_rules.json").write_text(
            json.dumps(_minimal_defaults()), encoding="utf-8"
        )
        with pytest.raises(QuestionnaireError, match="Invalid pbdd_principles"):
            Questionnaire(config_dir=config)

    def test_malformed_defaults_raise_questionnaire_error(self, tmp_path: Path) -> None:
        config = tmp_path / "config"
        config.mkdir()
        (config / "pbdd_principles.json").write_text(
            json.dumps(_minimal_principles()), encoding="utf-8"
        )
        (config / "default_settings_rules.json").write_text(
            json.dumps({"rules": [{"label": "broken"}]}), encoding="utf-8"
        )
        with pytest.raises(QuestionnaireError, match="Invalid default_settings"):
            Questionnaire(config_dir=config)
