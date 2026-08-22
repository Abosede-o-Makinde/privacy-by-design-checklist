"""Collect a system profile from JSON or an interactive prompt."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

ALLOWED_ANSWERS = frozenset({"yes", "partial", "no", "n/a"})
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_DIR = REPO_ROOT / "config"


class QuestionnaireError(ValueError):
    """Raised when a profile or rules file cannot be used."""


@dataclass
class Criterion:
    id: str
    question: str
    gdpr_articles: list[str]


@dataclass
class Principle:
    id: str
    name: str
    short_name: str
    criteria: list[Criterion]


@dataclass
class DefaultRule:
    id: str
    label: str
    question: str


@dataclass
class SystemProfile:
    """Answers the scoring engines will consume."""

    system_id: str
    name: str
    description: str = ""
    purpose: str = ""
    organisation: str = ""
    answers: dict[str, str] = field(default_factory=dict)
    default_answers: dict[str, str] = field(default_factory=dict)
    notes: str = ""


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise QuestionnaireError(f"File not found: {path}")
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise QuestionnaireError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise QuestionnaireError(f"{path} must contain a JSON object")
    return payload


def _require_answer(value: object, key: str) -> str:
    if not isinstance(value, str) or value not in ALLOWED_ANSWERS:
        raise QuestionnaireError(
            f"Answer for '{key}' must be one of: {', '.join(sorted(ALLOWED_ANSWERS))}"
        )
    return value


class Questionnaire:
    """Loads scoring questions and builds a SystemProfile."""

    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
        self.principles = self._load_principles()
        self.default_rules = self._load_default_rules()
        self.criterion_ids = [
            criterion.id
            for principle in self.principles
            for criterion in principle.criteria
        ]
        self.default_ids = [rule.id for rule in self.default_rules]

    def _load_principles(self) -> list[Principle]:
        data = _read_json(self.config_dir / "pbdd_principles.json")
        principles: list[Principle] = []
        for item in data.get("principles", []):
            criteria = [
                Criterion(
                    id=row["id"],
                    question=row["question"],
                    gdpr_articles=list(row.get("gdpr_articles", [])),
                )
                for row in item.get("criteria", [])
            ]
            if not criteria:
                raise QuestionnaireError(f"Principle '{item.get('id')}' has no criteria")
            principles.append(
                Principle(
                    id=item["id"],
                    name=item["name"],
                    short_name=item.get("short_name", item["name"]),
                    criteria=criteria,
                )
            )
        if len(principles) != 7:
            raise QuestionnaireError("pbdd_principles.json must define seven principles")
        return principles

    def _load_default_rules(self) -> list[DefaultRule]:
        data = _read_json(self.config_dir / "default_settings_rules.json")
        rules = [
            DefaultRule(id=row["id"], label=row["label"], question=row["question"])
            for row in data.get("rules", [])
        ]
        if not rules:
            raise QuestionnaireError("default_settings_rules.json has no rules")
        return rules

    def from_json(self, path: Path) -> SystemProfile:
        """Load a completed profile from a JSON file."""
        payload = _read_json(Path(path))
        return self.from_dict(payload)

    def from_dict(self, payload: dict) -> SystemProfile:
        system_id = str(payload.get("system_id", "")).strip()
        name = str(payload.get("name", "")).strip()
        if not system_id or not name:
            raise QuestionnaireError("Profile needs system_id and name")

        raw_answers = payload.get("answers")
        raw_defaults = payload.get("default_answers")
        if not isinstance(raw_answers, dict) or not isinstance(raw_defaults, dict):
            raise QuestionnaireError("Profile needs answers and default_answers objects")

        answers = {
            key: _require_answer(value, key) for key, value in raw_answers.items()
        }
        default_answers = {
            key: _require_answer(value, key) for key, value in raw_defaults.items()
        }
        self._check_keys(answers, self.criterion_ids, "answers")
        self._check_keys(default_answers, self.default_ids, "default_answers")

        return SystemProfile(
            system_id=system_id,
            name=name,
            description=str(payload.get("description", "")),
            purpose=str(payload.get("purpose", "")),
            organisation=str(payload.get("organisation", "")),
            answers=answers,
            default_answers=default_answers,
            notes=str(payload.get("notes", "")),
        )

    def _check_keys(
        self, given: dict[str, str], expected: list[str], label: str
    ) -> None:
        missing = [key for key in expected if key not in given]
        extra = [key for key in given if key not in expected]
        if missing:
            raise QuestionnaireError(f"{label} missing: {', '.join(missing)}")
        if extra:
            raise QuestionnaireError(f"{label} has unknown keys: {', '.join(extra)}")

    def interactive(self) -> SystemProfile:
        """Ask every question on stdin. Answers: yes, partial, no, n/a."""
        print("System profile")
        system_id = _ask_text("System ID")
        name = _ask_text("System name")
        organisation = _ask_text("Organisation", required=False)
        purpose = _ask_text("Purpose", required=False)
        description = _ask_text("Short description", required=False)

        answers: dict[str, str] = {}
        for principle in self.principles:
            print(f"\n{principle.short_name}: {principle.name}")
            for criterion in principle.criteria:
                answers[criterion.id] = _ask_choice(criterion.question)

        default_answers: dict[str, str] = {}
        print("\nPrivacy by default")
        for rule in self.default_rules:
            default_answers[rule.id] = _ask_choice(f"{rule.label}: {rule.question}")

        notes = _ask_text("Notes", required=False)
        return self.from_dict(
            {
                "system_id": system_id,
                "name": name,
                "organisation": organisation,
                "purpose": purpose,
                "description": description,
                "answers": answers,
                "default_answers": default_answers,
                "notes": notes,
            }
        )


def _ask_text(label: str, *, required: bool = True) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value or not required:
            return value
        print("This field is required.")


def _ask_choice(question: str) -> str:
    hint = "yes / partial / no / n/a"
    while True:
        value = input(f"{question} ({hint}): ").strip().lower()
        if value in ALLOWED_ANSWERS:
            return value
        print(f"Please answer with {hint}.")
