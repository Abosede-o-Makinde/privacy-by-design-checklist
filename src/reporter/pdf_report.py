"""Privacy-by-design assessment PDF via fpdf2."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fpdf import FPDF

from src import __version__
from src.checker.assessment import Assessment


class Colour:
    DARK_BLUE = (31, 56, 100)
    WHITE = (255, 255, 255)
    LIGHT_GREY = (245, 245, 245)
    TEXT_DARK = (30, 30, 30)
    PASS = (0, 128, 0)
    PARTIAL = (200, 120, 0)
    FAIL = (160, 0, 0)


class PrivacyByDesignReport:
    """Writes a short A4 PDF from a completed assessment."""

    MARGIN = 20

    def generate(self, assessment: Assessment, output_path: Path) -> Path:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=self.MARGIN)
        pdf.set_margins(self.MARGIN, self.MARGIN, self.MARGIN)
        self._add_cover(pdf, assessment)
        self._add_principles(pdf, assessment)
        self._add_defaults(pdf, assessment)
        self._add_checklist(pdf, assessment)

        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        pdf.output(str(target.resolve()))
        return target

    def _add_cover(self, pdf: FPDF, assessment: Assessment) -> None:
        pdf.add_page()
        pdf.set_fill_color(*Colour.DARK_BLUE)
        pdf.rect(0, 0, 210, 45, style="F")
        pdf.set_text_color(*Colour.WHITE)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_y(12)
        pdf.cell(
            0,
            10,
            "privacy-by-design-checklist",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_font("Helvetica", size=11)
        pdf.cell(
            0,
            8,
            f"Article 25 assessment v{__version__}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_text_color(*Colour.TEXT_DARK)
        pdf.ln(18)
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(
            0,
            10,
            self._safe("Privacy by Design Assessment"),
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(4)
        profile = assessment.profile
        self._row(pdf, "System", profile.name)
        self._row(pdf, "System ID", profile.system_id)
        if profile.organisation:
            self._row(pdf, "Organisation", profile.organisation)
        if profile.purpose:
            self._row(pdf, "Purpose", profile.purpose)
        self._row(pdf, "Generated (UTC)", datetime.now(UTC).strftime("%Y-%m-%d %H:%M"))
        self._row(pdf, "Principle score", f"{assessment.principle_score}/100")
        self._row(pdf, "Default score", f"{assessment.default_score}/100")

        colour = {
            "PASS": Colour.PASS,
            "PARTIAL": Colour.PARTIAL,
            "FAIL": Colour.FAIL,
        }[assessment.band]
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(35, 8, "Overall band:")
        pdf.set_fill_color(*colour)
        pdf.set_text_color(*Colour.WHITE)
        pdf.cell(40, 8, assessment.band, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*Colour.TEXT_DARK)
        if assessment.blocks_pass:
            pdf.ln(4)
            pdf.set_font("Helvetica", size=10)
            self._para(
                pdf,
                "Art. 25(2) gate: at least one default-settings answer is NO, "
                "so PASS is blocked.",
            )
        pdf.ln(8)
        pdf.set_font("Helvetica", "I", 9)
        self._para(
            pdf,
            "Decision-support only. Not legal advice. Review with a DPO before go-live.",
        )

    def _add_principles(self, pdf: FPDF, assessment: Assessment) -> None:
        pdf.add_page()
        self._header(pdf, "Seven privacy-by-design principles")
        for item in assessment.principles.principle_scores:
            score = "n/a" if item.score is None else f"{item.score}/100"
            self._row(pdf, item.short_name, score)
            pdf.set_font("Helvetica", size=8)
            self._para(pdf, item.name)
            pdf.ln(1)

    def _add_defaults(self, pdf: FPDF, assessment: Assessment) -> None:
        pdf.add_page()
        self._header(pdf, "Privacy by default (Article 25(2))")
        for item in assessment.defaults.rule_results:
            score = "n/a" if item.score is None else f"{item.score}/100"
            flag = " BLOCKS PASS" if item.blocks_pass else ""
            self._row(pdf, item.label, f"{item.answer} ({score}){flag}")

    def _add_checklist(self, pdf: FPDF, assessment: Assessment) -> None:
        pdf.add_page()
        self._header(pdf, "Engineer go-live checklist")
        if not assessment.checklist.items:
            self._para(pdf, "No open gaps.")
            return
        for index, item in enumerate(assessment.checklist.items, start=1):
            articles = ", ".join(item.gdpr_articles) or "-"
            pdf.set_font("Helvetica", "B", 10)
            self._para(
                pdf,
                f"{index}. [{item.answer.upper()}] {item.title} ({item.item_id}; Art. {articles})",
            )
            pdf.set_font("Helvetica", size=9)
            self._para(pdf, item.action)
            pdf.ln(2)

    def _header(self, pdf: FPDF, title: str) -> None:
        pdf.set_fill_color(*Colour.LIGHT_GREY)
        pdf.set_text_color(*Colour.DARK_BLUE)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, self._safe(title), fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_text_color(*Colour.TEXT_DARK)

    def _row(self, pdf: FPDF, key: str, value: str) -> None:
        pdf.set_x(self.MARGIN)
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(
            0,
            6,
            self._safe(f"{key}: {value}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )

    def _para(self, pdf: FPDF, text: str) -> None:
        pdf.set_x(self.MARGIN)
        pdf.multi_cell(0, 5, self._safe(text), new_x="LMARGIN", new_y="NEXT")

    @staticmethod
    def _safe(text: str) -> str:
        replacements = {
            "\u2014": "-",
            "\u2013": "-",
            "\u2022": "-",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
        }
        cleaned = text
        for source, target in replacements.items():
            cleaned = cleaned.replace(source, target)
        return cleaned.encode("latin-1", errors="replace").decode("latin-1")
