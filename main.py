"""
privacy-by-design-checklist CLI entry point.

Routes --mode flags to assess, checklist, and report workflows.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src import __version__
from src.checker.assessment import Assessment, AssessmentRunner
from src.checker.questionnaire import Questionnaire, QuestionnaireError
from src.reporter.markdown_checklist import MarkdownChecklistWriter
from src.reporter.pdf_report import PrivacyByDesignReport

console = Console()
DEFAULT_OUTPUT_DIR = Path("outputs")


def _load_profile(input_path: Path | None):
    questionnaire = Questionnaire()
    if input_path is None:
        return questionnaire.interactive()
    return questionnaire.from_json(Path(input_path))


def _print_assessment(assessment: Assessment) -> None:
    table = Table(title="Principle scores")
    table.add_column("Principle")
    table.add_column("Score")
    table.add_column("Answered")
    for item in assessment.principles.principle_scores:
        score = "n/a" if item.score is None else f"{item.score}/100"
        table.add_row(item.short_name, score, str(item.answered))
    console.print(table)

    defaults = Table(title="Privacy by default (Art. 25(2))")
    defaults.add_column("Rule")
    defaults.add_column("Answer")
    defaults.add_column("Score")
    for item in assessment.defaults.rule_results:
        score = "n/a" if item.score is None else f"{item.score}/100"
        answer = item.answer
        if item.blocks_pass:
            answer = f"[red]{answer}[/red]"
        defaults.add_row(item.label, answer, score)
    console.print(defaults)

    gate = "yes — PASS blocked" if assessment.blocks_pass else "no"
    console.print(
        Panel(
            f"System: [bold]{assessment.profile.name}[/bold]\n"
            f"Principle score: [bold]{assessment.principle_score}/100[/bold]\n"
            f"Default score: [bold]{assessment.default_score}/100[/bold]\n"
            f"Band: [bold]{assessment.band}[/bold]\n"
            f"Art. 25(2) gate: {gate}\n"
            f"Open checklist items: {len(assessment.checklist.items)}",
            title="Assessment summary",
        )
    )


def _print_checklist(assessment: Assessment) -> None:
    if not assessment.checklist.items:
        console.print("[green]No open gaps.[/green]")
        return
    table = Table(title="Engineer go-live checklist")
    table.add_column("#")
    table.add_column("Priority")
    table.add_column("Answer")
    table.add_column("Item")
    table.add_column("Action")
    for index, item in enumerate(assessment.checklist.items, start=1):
        table.add_row(
            str(index),
            str(item.priority),
            item.answer,
            f"{item.title} ({item.item_id})",
            item.action,
        )
    console.print(table)


def _run_assess(input_path: Path | None) -> Assessment:
    profile = _load_profile(input_path)
    assessment = AssessmentRunner().run(profile)
    _print_assessment(assessment)
    return assessment


def _run_checklist(input_path: Path | None, output_dir: Path) -> Assessment:
    assessment = _run_assess(input_path)
    _print_checklist(assessment)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    checklist_path = output_dir / f"{assessment.profile.system_id}_checklist.md"
    MarkdownChecklistWriter().write(assessment, checklist_path)
    console.print(Panel(f"Checklist written to {checklist_path}", title="Checklist export"))
    return assessment


def _run_report(input_path: Path | None, output_dir: Path) -> Assessment:
    assessment = _run_checklist(input_path, output_dir)
    output_dir = Path(output_dir)
    pdf_path = output_dir / f"{assessment.profile.system_id}_assessment.pdf"
    PrivacyByDesignReport().generate(assessment, pdf_path)
    console.print(Panel(f"PDF written to {pdf_path}", title="Report export"))
    return assessment


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["assess", "checklist", "report"]),
    default="assess",
    show_default=True,
    help="Workflow mode to run.",
)
@click.option(
    "--input",
    "input_path",
    type=click.Path(path_type=Path),
    help="JSON system profile. Omit to answer questions interactively.",
)
@click.option(
    "--output",
    "output_dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    show_default=True,
    help="Directory for checklist and PDF outputs.",
)
@click.version_option(version=__version__, prog_name="privacy-by-design-checklist")
def cli(mode: str, input_path: Path | None, output_dir: Path) -> None:
    """Score a system design against Article 25 privacy-by-design principles."""
    try:
        if mode == "assess":
            _run_assess(input_path)
        elif mode == "checklist":
            _run_checklist(input_path, output_dir)
        else:
            _run_report(input_path, output_dir)
    except (QuestionnaireError, OSError, ValueError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    cli(standalone_mode=True)
    sys.exit(0)
