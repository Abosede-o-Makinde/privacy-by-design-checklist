# privacy-by-design-checklist

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GDPR Art. 25](https://img.shields.io/badge/GDPR-Art.%2025-important)](docs/PRIVACY_BY_DESIGN_GUIDE.md)

Article 25 compliance tool — scores a new system design against privacy-by-design principles and privacy-by-default rules, then prints an engineer go-live checklist and PDF.

## The problem this solves

Under UK GDPR **Article 25**, privacy must be built into systems by design and by default. In practice teams struggle because:

- Article 25 is treated as a policy statement, not a build checklist
- Optional features ship switched on and collect more data than the purpose needs
- There is no quick pre-go-live review before engineering signs off

**privacy-by-design-checklist** takes a system profile, scores seven privacy-by-design principles plus Article 25(2) defaults, and exports a prioritised engineer checklist — locally, with no cloud dependency.

## Features

| Capability | Module | CLI mode |
| ---------- | ------ | -------- |
| JSON or interactive profile capture | `questionnaire.py` | omit `--input` |
| Seven-principle scoring | `principles_engine.py` | `--mode assess` |
| Article 25(2) default gate | `default_checker.py` | `--mode assess` |
| Prioritised go-live checklist | `checklist_generator.py` | `--mode checklist` |
| Markdown + PDF export | `markdown_checklist.py` / `pdf_report.py` | `--mode checklist` / `report` |

## Installation

```bash
pip install -r requirements.txt
python main.py --help
python main.py --version
```

## Commands

| Mode | Required flags | What you get |
| ---- | -------------- | ------------ |
| `assess` | optional `--input profile.json` | Principle scores, default check, FAIL / PARTIAL / PASS band |
| `checklist` | optional `--input`, optional `--output` | Terminal output + Markdown checklist file |
| `report` | optional `--input`, optional `--output` | Checklist + PDF assessment |

### Examples

```bash
# Score the sample system
python main.py --mode assess --input sample_data/meeting_notetaker.json

# Assessment + Markdown checklist
python main.py --mode checklist --input sample_data/meeting_notetaker.json --output outputs/

# Checklist + PDF
python main.py --mode report --input sample_data/meeting_notetaker.json --output outputs/

# Answer questions interactively (no JSON file)
python main.py --mode assess
```

Output filenames use a sanitised `system_id` stem (for example `MEETING-NOTES-001_checklist.md`).

## Worked example — AI meeting notetaker

A professional-services firm wants an **AI meeting notetaker** for internal calls. Recording and transcript storage are on for every meeting by default.

```bash
python main.py --mode assess --input sample_data/meeting_notetaker.json
```

Typical result on that profile:

| Signal | Result |
| ------ | ------ |
| Principle score | **67.3 / 100** |
| Default score | **25.0 / 100** |
| Band | **PARTIAL** |
| Art. 25(2) gate | **PASS blocked** |

The checklist prioritises defaults first — for example collect only what the purpose needs by default, set and enforce retention, tighten admin export, finish the DPIA.

### Sample output (Markdown excerpt)

Pre-generated artefacts: [`sample_outputs/`](sample_outputs/)

```text
Band: PARTIAL
Art. 25(2) blocks PASS: yes

1. [NO] Amount of personal data collected (amount, Art. 25)
2. [NO] Period of storage (storage, Art. 25)
3. [PARTIAL] Extent of processing (extent, Art. 25)
4. [PARTIAL] Accessibility (accessibility, Art. 25)
```

See [docs/PRIVACY_BY_DESIGN_GUIDE.md](docs/PRIVACY_BY_DESIGN_GUIDE.md) for scoring rules and band definitions.

## GDPR coverage

| Article | Obligation | Handled by |
| ------- | ---------- | ---------- |
| Art. 25(1) | Data protection by design | Seven-principle scoring engine |
| Art. 25(2) | Data protection by default | Default checker (amount, extent, storage, accessibility) |
| Art. 35 | DPIA for high-risk processing | Flagged on checklist when answers are partial/no — not a full DPIA |

## Repository structure

```text
privacy-by-design-checklist/
├── main.py
├── src/checker/          # questionnaire, engines, checklist
├── src/reporter/         # Markdown and PDF export
├── config/               # principle and default rule JSON
├── sample_data/          # meeting_notetaker.json
├── sample_outputs/       # committed demo checklist and PDF
├── docs/                 # Article 25 guide
└── tests/
```

## Limitations

- Decision-support only — not legal advice; a DPO should review outputs before go-live
- Local CLI only — no cloud sync or multi-user access control
- Scoring reflects this tool's methodology, not an ICO grade or Article 25(3) certification
- High-risk processing still needs a proper DPIA and qualified review

## Licence

MIT. This tool is decision-support only and is not legal advice.
