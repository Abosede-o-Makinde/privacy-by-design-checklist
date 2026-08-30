"""Combine principle scores and default checks into one assessment."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.checker.checklist_generator import Checklist, ChecklistGenerator
from src.checker.default_checker import DefaultChecker, DefaultCheckResult
from src.checker.principles_engine import PrinciplesEngine, PrinciplesResult
from src.checker.questionnaire import Questionnaire, SystemProfile


@dataclass
class Assessment:
    profile: SystemProfile
    principles: PrinciplesResult
    defaults: DefaultCheckResult
    checklist: Checklist
    band: str
    principle_score: float | None
    default_score: float | None
    blocks_pass: bool


def band_for(score: float | None, blocks_pass: bool) -> str:
    """Map a 0-100 score to FAIL / PARTIAL / PASS.

    Any Article 25(2) ``no`` answer blocks PASS even when the score is high.
    If every principle answer is n/a, there is no score — treat as PARTIAL.
    """
    if score is None:
        return "PARTIAL"
    if score < 50:
        return "FAIL"
    if blocks_pass or score < 80:
        return "PARTIAL"
    return "PASS"


def format_score(score: float | None) -> str:
    """Human-readable score for CLI, markdown, and PDF."""
    return "n/a" if score is None else f"{score}/100"


def safe_output_stem(system_id: str) -> str:
    """Keep filenames inside the output directory."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", system_id.strip())
    return cleaned or "system"


class AssessmentRunner:
    """Runs principles, defaults, and checklist for one system profile."""

    def __init__(self, questionnaire: Questionnaire | None = None) -> None:
        self.questionnaire = questionnaire or Questionnaire()
        self.principles_engine = PrinciplesEngine(self.questionnaire)
        self.default_checker = DefaultChecker(self.questionnaire)
        self.checklist_generator = ChecklistGenerator(self.questionnaire)

    def run(self, profile: SystemProfile) -> Assessment:
        principles = self.principles_engine.score(profile)
        defaults = self.default_checker.check(profile)
        checklist = self.checklist_generator.generate(profile)
        band = band_for(principles.overall_score, defaults.blocks_pass)
        return Assessment(
            profile=profile,
            principles=principles,
            defaults=defaults,
            checklist=checklist,
            band=band,
            principle_score=principles.overall_score,
            default_score=defaults.overall_score,
            blocks_pass=defaults.blocks_pass,
        )
