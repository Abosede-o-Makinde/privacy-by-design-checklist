# Privacy by Design guide — Article 25

Plain-English overview of UK GDPR **Article 25** and how this tool turns it into a pre-go-live checklist for engineers.

## Why this matters

Article 25 requires **data protection by design and by default**. In practice that means:

- Privacy controls are built into the system from the start, not bolted on after launch.
- Default settings collect only what the purpose needs, for only as long as needed, and only for people who need access.

Teams often meet Article 25 in policy slides or late-stage reviews. This CLI is for the week **before go-live**: describe the system, score the design, and print a prioritised engineer checklist.

## What Article 25 covers

### Article 25(1) — by design

Controllers must implement appropriate technical and organisational measures, considering:

- State of the art
- Cost of implementation
- Nature, scope, context, and purpose of processing
- Risks to individuals

This tool does not automate that full legal test. It scores engineer-facing criteria mapped to the **seven privacy-by-design principles** (proactive, default, embedded, full functionality, security, transparency, user-centric).

### Article 25(2) — by default

By default, the system should only process personal data that is **necessary** for each purpose. ICO guidance frames this around:

| Factor | Question |
| ------ | -------- |
| **Amount** | How much personal data is collected by default? |
| **Extent** | How far is processing limited to the stated purpose? |
| **Storage** | How long is data kept, and is retention enforced? |
| **Accessibility** | Who can access the data by default? |

In this tool, any default answer of **no** blocks an overall **PASS** band — even when principle scores are high.

## How scoring works

Answers for each criterion:

| Answer | Score | Effect |
| ------ | ----- | ------ |
| `yes` | 1.0 | Counts toward the principle or default score |
| `partial` | 0.5 | Counts; appears on the checklist |
| `no` | 0.0 | Counts; appears on the checklist; defaults can block PASS |
| `n/a` | skipped | Excluded — does not fake a fail when a question does not apply |

**Principle score:** average of answered criteria per principle, scaled to 0–100.  
**Default score:** average of the four Article 25(2) rules, scaled to 0–100.  
**Overall band** (decision-support label, not an ICO grade):

| Band | Rule |
| ---- | ---- |
| **FAIL** | Principle score below 50 |
| **PARTIAL** | Score 50–79, or any blocking default, or no score (all `n/a`) |
| **PASS** | Principle score 80+ and no blocking default |

If every answer is `n/a`, overall scores show as `n/a` and the band is **PARTIAL**.

## Checklist priority

Failed and partial answers become checklist items, ordered:

1. Article 25(2) defaults (amount, extent, storage, accessibility)
2. Security gaps (encryption, access control, disposal, logging)
3. Article 5 / transparency items
4. Remaining principle gaps

High-risk processing (for example continuous workplace recording) should trigger a **DPIA** under Article 35. This tool flags gaps such as an unfinished DPIA; it does not replace a DPIA generator or DPO sign-off.

## How to use this tool

1. **Describe the system** — JSON profile or interactive prompts (`yes` / `partial` / `no` / `n/a`).
2. **Run a mode:**
   - `assess` — terminal scores and band
   - `checklist` — adds a Markdown go-live checklist
   - `report` — adds a PDF assessment
3. **Review gaps** — fix items before go-live, or accept them with a recorded reason and DPO review.

```bash
python main.py --mode assess --input sample_data/meeting_notetaker.json
python main.py --mode checklist --input sample_data/meeting_notetaker.json --output outputs/
python main.py --mode report --input sample_data/meeting_notetaker.json --output outputs/
```

Everything runs locally. No cloud dependency.

## What this tool is not

- **Not legal advice** — decision-support for design reviews only
- **Not an ICO certification** — Article 25(3) certification is a separate ICO mechanism
- **Not a DPIA** — use your DPIA process for Article 35 high-risk processing
- **Not a compliance guarantee** — a PASS band means the described design met this checklist, not that the organisation is GDPR compliant overall

Review outputs with a qualified DPO before go-live.

## Further reading

- [ICO — Data protection by design and default](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/guide-to-accountability-and-governance/data-protection-by-design-and-by-default/)
- UK GDPR Article 25 and Article 35 (DPIA)
