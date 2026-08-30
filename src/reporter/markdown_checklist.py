"""Write an engineer-facing checklist as Markdown."""

from __future__ import annotations

from pathlib import Path

from src.checker.assessment import Assessment, format_score


class MarkdownChecklistWriter:
    """Exports a prioritised go-live checklist to a Markdown file."""

    def write(self, assessment: Assessment, output_path: Path) -> Path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        profile = assessment.profile
        lines = [
            f"# Go-live checklist: {profile.name}",
            "",
            f"- System ID: `{profile.system_id}`",
            f"- Principle score: **{format_score(assessment.principle_score)}**",
            f"- Default score: **{format_score(assessment.default_score)}**",
            f"- Band: **{assessment.band}**",
            f"- Art. 25(2) blocks PASS: **{'yes' if assessment.blocks_pass else 'no'}**",
            "",
        ]
        if profile.description:
            lines.extend([f"**Description:** {profile.description}", ""])
        if profile.notes:
            lines.extend([f"**Notes:** {profile.notes}", ""])
        if not assessment.checklist.items:
            lines.extend(
                [
                    "No open gaps. Defaults and principles are clear for go-live review.",
                    "",
                ]
            )
        else:
            lines.extend(["## Prioritised actions", ""])
            for index, item in enumerate(assessment.checklist.items, start=1):
                articles = ", ".join(f"Art. {a}" for a in item.gdpr_articles) or "—"
                lines.append(
                    f"{index}. **[{item.answer.upper()}] {item.title}** "
                    f"(`{item.item_id}`, {articles})"
                )
                lines.append(f"   - {item.action}")
                lines.append("")

        lines.extend(
            [
                "---",
                "Decision-support only. Not legal advice. Review with a DPO before go-live.",
                "",
            ]
        )
        target.write_text("\n".join(lines), encoding="utf-8")
        return target
