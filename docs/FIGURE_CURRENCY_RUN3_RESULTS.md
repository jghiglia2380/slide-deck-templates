# Figure-Currency Wiring — Run 3 Results (free-PDF slice)

**Date:** 2026-07-24 · **Branch:** `figure-currency-phase-3-free-pdf` (off merged `main`)
**Scope:** Phase 3 §3-Free-PDF only. Live resolver, print resolver, and Seb's Resource-Hub
download button are OUT of scope (noted, untouched).

## Deliverables
- `figure_resolver.py` — the resolution engine (federal currency + state tokens + null
  placeholder). Import-safe, no network. Self-test + corpus report built in.
- `generate_state_resources.py` — rewritten: cosmetic `sanitize_html_content()` replaced
  with `localize_html()` → `figure_resolver.resolve_file()`; repo-relative paths;
  data-driven state list; `--dry-run` (no API) and `--report` modes.
- `docs/TOKEN_MAP.md` — token → backing-field map per surface (for the later live/print
  unification).

Verify offline:
```
python3 figure_resolver.py --selftest     # NC/KY/TX figure resolution + federal currency
python3 figure_resolver.py --report       # corpus federal audit + state completeness
python3 generate_state_resources.py --dry-run   # localize NC/KY/TX, no API
```

---

## Headline deterministic finding (resolved from source, reported per guardrails)

**The premise "every state shows Oklahoma's figures" does NOT hold for this corpus.** The
`oklahoma-free-resources/` templates are generic/national content — verified across every OK
source variant, these OK STATE figures are **absent as literals**: income-tax-as-tax `4.5%`,
`sales_tax`, `property_tax_effective_rate 0.87%`, `min_wage 7.25`, median home/rent, place
names (Tulsa/Norman/Edmond). Every `4.5%` in the corpus is a loan/mortgage **interest rate**,
not a tax rate. So there is **no Oklahoma state-figure bleed to substitute out**, and none was
invented.

**The real, resolvable currency defect is baked old-year FEDERAL literals** — 2022/2023/2024
standard deductions, brackets, and retirement limits in ~10 files — which survived the old
cosmetic rebrand into every state's output. This run fixes those from the single source
(`federal_figures.json`, tax_year 2026).

True per-state localization (making a worksheet *show* NC's 3.99% income / 4.75% sales /
0.66% property) requires INJECTING figures into currently-generic content = content authoring,
not currency wiring. The STATE resolver + token vocabulary are built and proven; they act on
today's corpus only where a `{{STATE_*}}` token exists (none yet), so that step is a no-op
pending template tokenization (a separate content task). No figure was fabricated.

---

## Gate results

### Gate 1 — 3 non-OK states, zero Oklahoma figure bleed
`--dry-run` output for NC / KY / TX, grepped for OK figures:

| OK figure | files in NC/KY/TX output |
|---|---|
| `0.87%` (property) | 0 |
| `195,000` (median home) | 0 |
| Tulsa / Norman / Edmond | 0 |

Zero OK figure bleed. (One legitimate text mention of "Oklahoma" remains — it is an item in a
factual enumeration of states with a state income tax: *"…Ohio, Oklahoma, Oregon, Rhode
Island…"*. Replacing it would falsify the list; branding localization correctly leaves it.)

**State figure resolution proven** (self-test, tokenized fixture):

| State | income | sales | property |
|---|---|---|---|
| North Carolina | **3.99%** | 4.75% | 0.66% |
| Kentucky | 3.5% | 6% | 0.74% |
| Texas | **0%** (real, not placeholder) | 6.25% | **flagged placeholder** (null) |

Each resolves to THAT state's value from `{state}.json`; zero Oklahoma values.

### Gate 2 — zero baked 2023/2024 federal literals; all trace to federal_figures.json
Before/after on `tax-planning/chapter-2-3_Filing_Status_Chart.html` (NC output):

| | source (Oklahoma) | NC output |
|---|---|---|
| year label | `2024` | `2026` |
| Single std deduction | `$14,600` ×2 | `$16,100` ×2 |
| MFJ std deduction | `$29,200` ×2 | `$32,200` ×2 |

All new values read from `federal_figures.json` (`standard_deduction.single=16100`,
`.mfj=32200`, `tax_year=2026`). **5 files auto-updated, 12 substitutions each state.**

**Held for manual content revision (5 files)** — auto-substituting these would desync shown
arithmetic (a value used in a worked example / bracket table / base-catch-up pair). Reported,
left untouched to preserve internal consistency:

| File | stale literal(s) | why held |
|---|---|---|
| `charitable-giving/chapter-14-1_Tax_Benefits_Reference.html` | $13,850, $20,800, $27,700 | worked itemize-vs-standard example whose conclusion flips at $16,100 |
| `tax-planning/chapter-2-2_Tax_Bracket_Reference_Guide.html` | bracket table | ceilings + inline bracket math |
| `tax-planning/chapter-2-4_tax_calculation_flowchart.html` | $13,850, $20,800, $27,700 | inline taxable-income math chain |
| `career-planning/chapter-1-2_Financial_Aid_Reference_Guide.html` | bracket table | inline bracket math |
| `retirement-planning/chapter-6-1_retirement_planning_worksheet.html` | $22,500, $6,500 | base/catch-up pairs ($30,000 / $7,500 partners) |

These need a small content edit (recompute the example around the 2026 figure), which is
authoring, not currency wiring.

### Gate 3 — null property rate → flagged placeholder, not OK value / guess
Texas (`property_tax_effective_rate: null`) resolves the property token to:
```
[[TODO: taxes.property_tax_effective_rate unavailable for Texas — see state-data/states/texas.json]]
```
Never `0.87%` (Oklahoma) and never a fabricated number. `0` remains a REAL value (TX income
tax → `0%`), not treated as null.

### Processed-state count + incomplete states
- **36 states** have a canonical `{state}.json` and generate cleanly — **all** have the
  critical fields (income_tax_rate, sales_tax, min_wage, state_name). None is too incomplete
  to generate.
- **33 states** lack only `taxes.property_tax_effective_rate` (the known pending batch) → the
  property token renders the flagged placeholder for those; every other figure resolves.
- The old generator's `skip_states` list dropped processing to ~28 by skipping
  "already-processed" states. That skip is **removed** — those states carried the same stale
  federal figures and must be reprocessed. (The old docstring's "37 states" was also wrong;
  the real count is 36 data-backed states.)

---

## Safety design (why nothing is silently corrupted)
- Federal values are sourced from the dataset at runtime — **no hardcoded 2026 output
  literals** in the generator; the old literals are recognition keys only.
- A federal value is auto-substituted **only** where standalone; per-literal locking holds a
  value if ANY of its occurrences sits in dependent arithmetic (detected around dollar/number
  tokens, never a bare `=` which would match HTML attributes). A file with any held content is
  held whole, so it is never left half-current.
- Ambiguous coincidental numbers are never touched (every `4.5%` = a loan rate; `$6,500` is
  only treated as an IRA limit when in a retirement context).
