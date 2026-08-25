"""Build a prioritised engineer checklist from unanswered gaps."""

from __future__ import annotations

from dataclasses import dataclass

from src.checker.questionnaire import Questionnaire, SystemProfile

GAP_ANSWERS = frozenset({"no", "partial"})

# Lower number = higher priority.
PRIORITY_DEFAULT = 1
PRIORITY_SECURITY = 2
PRIORITY_ARTICLE_5 = 3
PRIORITY_OTHER = 4


@dataclass
class ChecklistItem:
    item_id: str
    source: str
    priority: int
    answer: str
    title: str
    action: str
    gdpr_articles: list[str]


@dataclass
class Checklist:
    system_id: str
    system_name: str
    items: list[ChecklistItem]


class ChecklistGenerator:
    """Turns no/partial answers into a stable, prioritised go-live list."""

    def __init__(self, questionnaire: Questionnaire | None = None) -> None:
        self.questionnaire = questionnaire or Questionnaire()

    def generate(self, profile: SystemProfile) -> Checklist:
        items: list[ChecklistItem] = []
        items.extend(self._default_items(profile))
        items.extend(self._principle_items(profile))
        items.sort(key=lambda item: (item.priority, 0 if item.answer == "no" else 1))
        return Checklist(
            system_id=profile.system_id,
            system_name=profile.name,
            items=items,
        )

    def _default_items(self, profile: SystemProfile) -> list[ChecklistItem]:
        items: list[ChecklistItem] = []
        for rule in self.questionnaire.default_rules:
            answer = profile.default_answers.get(rule.id)
            if answer not in GAP_ANSWERS:
                continue
            items.append(
                ChecklistItem(
                    item_id=rule.id,
                    source="default",
                    priority=PRIORITY_DEFAULT,
                    answer=answer,
                    title=rule.label,
                    action=rule.question,
                    gdpr_articles=["25"],
                )
            )
        return items

    def _principle_items(self, profile: SystemProfile) -> list[ChecklistItem]:
        items: list[ChecklistItem] = []
        for principle in self.questionnaire.principles:
            for criterion in principle.criteria:
                answer = profile.answers.get(criterion.id)
                if answer not in GAP_ANSWERS:
                    continue
                items.append(
                    ChecklistItem(
                        item_id=criterion.id,
                        source="principle",
                        priority=_principle_priority(criterion.gdpr_articles),
                        answer=answer,
                        title=principle.short_name,
                        action=criterion.question,
                        gdpr_articles=list(criterion.gdpr_articles),
                    )
                )
        return items


def _principle_priority(articles: list[str]) -> int:
    tags = set(articles)
    if "32" in tags:
        return PRIORITY_SECURITY
    if "5" in tags:
        return PRIORITY_ARTICLE_5
    return PRIORITY_OTHER
