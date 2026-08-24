"""Shared fixtures. Pytest loads this file automatically."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.checker.questionnaire import Questionnaire, SystemProfile

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def questionnaire() -> Questionnaire:
    return Questionnaire(config_dir=ROOT / "config")


@pytest.fixture
def staff_access_profile(questionnaire: Questionnaire) -> SystemProfile:
    return questionnaire.from_json(ROOT / "sample_data" / "staff_access.json")
