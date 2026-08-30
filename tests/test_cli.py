"""CLI smoke tests for assess, checklist, and report modes."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from main import cli

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "sample_data" / "meeting_notetaker.json"


class TestCli:
    def test_assess_sample(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--mode", "assess", "--input", str(SAMPLE)])
        assert result.exit_code == 0, result.output
        assert "PARTIAL" in result.output
        assert "67.3" in result.output
        assert "Art. 25(2)" in result.output

    def test_checklist_writes_markdown(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        local = Path("sample.json")
        local.write_text(SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        out = Path("out")
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--mode", "checklist", "--input", str(local), "--output", str(out)],
        )
        assert result.exit_code == 0, result.output
        checklist = out / "MEETING-NOTES-001_checklist.md"
        assert checklist.is_file()
        text = checklist.read_text(encoding="utf-8")
        assert "Go-live checklist" in text
        assert "amount" in text

    def test_report_writes_pdf_and_markdown(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        local = Path("sample.json")
        local.write_text(SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        out = Path("out")
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--mode", "report", "--input", str(local), "--output", str(out)],
        )
        assert result.exit_code == 0, result.output
        assert (out / "MEETING-NOTES-001_checklist.md").is_file()
        pdf = out / "MEETING-NOTES-001_assessment.pdf"
        assert pdf.is_file()
        assert pdf.stat().st_size > 500

    def test_missing_input_fails(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--mode", "assess", "--input", "missing.json"],
        )
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_unsafe_system_id_sanitised_in_filename(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
        payload["system_id"] = "../evil/path"
        payload["description"] = "AI notes for internal staff meetings"
        payload["notes"] = "Recording on by default; retention not set"
        local = Path("sample.json")
        local.write_text(json.dumps(payload), encoding="utf-8")
        out = Path("out")
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--mode", "checklist", "--input", str(local), "--output", str(out)],
        )
        assert result.exit_code == 0, result.output
        checklist = out / ".._evil_path_checklist.md"
        assert checklist.is_file()
        assert not (tmp_path / "evil").exists()
        text = checklist.read_text(encoding="utf-8")
        assert "AI notes for internal staff meetings" in text
        assert "Recording on by default; retention not set" in text
