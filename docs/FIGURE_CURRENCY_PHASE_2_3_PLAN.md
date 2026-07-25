# Figure-Currency Wiring — Phase 2 & 3 Plan

**Status:** written 2026-07-24, post Run-1 ground-truth audit. Supersedes the stale
`docs/FIGURE_CURRENCY_WIRING_MAP.md` for anything below. Print pipeline stays
extraction-only; nothing here pushes from print back to live.

**Prereq already shipped (Run 1, Phase B):** `taxCalculations.ts` 2024→2026 constants
— PR https://github.com/jghiglia2380/pfl-academy-90-dashboards/pull/1. That is a Phase-1
stopgap hand-fix, not the single source. Phases 2–3 below kill the copies.

---

## Goal

After Phase 3 a figure lives in exactly **one** place per class:
- **Federal (national)** → one `federal_figures.json`.
- **State (per-state)** → one `{state}.json` per state.

Every surface (live, free PDFs, print) *reads* those two datasets instead of holding
its own hardcoded copy.

---

## Phase 2 — Complete the two canonical datasets

### 2A. Federal — create `federal_figures.json`

**Author it from the file that already holds the verified 2026 IRS numbers:**
- Source of values: `pfl-print-pipeline/gate/fixtures/tax_brackets_2026.json`
  (IRS Rev. Proc. 2025-32 — brackets, standard deduction, additional std deduction,
  401k/IRA limits, undergrad Direct loan rate 6.52%).
- **New file to create:** `state-data/federal/federal_figures.json` (new `federal/` dir
  sibling to `state-data/states/`). It is a superset of the gate fixture plus the figures
  the fixture is missing:
  - **Missing / to add:** Social Security wage base + per-worker max (the handoff
    `TAX_CURRENCY_2026_HANDOFF.md` flags p286 SS dollar figure as year-relabelled only,
    NOT recomputed — set `ss_wage_base_2026` and derive `ss_employee_max = wage_base ×
    0.062`); FICA rate (currently hardcoded 7.65% in `resolver/resolve.mjs:30`).
  - **Add a `data_as_of` stamp** (the fixture has none; the resolver requires one).
- **Keep the gate fixture as-is** — gate T4 asserts rendered tables match it. Either
  point the gate at the new file, or make the fixture a derived extract of it. Do NOT
  maintain both by hand (that recreates the copy problem). Note only; wire in Phase 3.

### 2B. State — complete `{state}.json` + fix the Oklahoma split

**Directory:** `state-data/states/` — 36 files today (`enabled_states` in
`state-data/automation/config.json` = 36 codes).

Two gaps to close:

1. **Oklahoma has two divergent copies — reconcile to one.**
   - STALE: `state-data/states/oklahoma.json` — `income_tax_rate: 4.75`,
     `property_tax_county_rate: 0.30`, **no** `property_tax_effective_rate`, **no**
     `data_as_of`.
   - CORRECTED (what the resolver actually loads): `pfl-print-pipeline/sources/state-variables/oklahoma.json`
     — `income_tax_rate: 4.5`, `property_tax_effective_rate: 0.87`, `data_as_of: "2026-07"`.
   - **Fix:** make `state-data/states/oklahoma.json` the canonical corrected copy, and
     have the print resolver read from `state-data/states/` (see 3-Print) so the
     `pfl-print-pipeline/sources/state-variables/` drop-in is no longer a parallel source.

2. **Add the two fields every state file is missing** so the resolver's strict keys pass
   for all states, not just Oklahoma:
   - `taxes.property_tax_effective_rate` (resolver keys to this with **no fallback**).
   - top-level `data_as_of` (resolver requires it via `fmtAsOf`).
   The updater already refreshes the underlying housing/employment/tax vars — these two
   are derived/label fields, not new data pulls.

### The 6 unresolved resolver tokens (name them; data already exists)

All six live in `f-sync-90/content/Standard-10/10.1/student/day2.md` (L-30 Day 2). The
data backing each is already present in every `{state}.json`; the gap is purely that
`resolver/resolve.mjs` `buildVariableMapping` never maps `housing.*` or `employment.*`:

| Token | Backing field in `{state}.json` |
|---|---|
| `{{STATE_MEDIAN_RENT}}` | `housing.median_rent` |
| `{{STATE_MEDIAN_HOME_PRICE}}` | `housing.median_home_price` |
| `{{STATE_HOUSING_MARKET_TRENDS}}` | `housing.housing_market_trends` |
| `{{STATE_UNEMPLOYMENT_RATE}}` | `employment.unemployment_rate` |
| `{{STATE_MAJOR_INDUSTRIES}}` | `employment.major_industries` |
| `{{STATE_AVG_MORTGAGE_RATE_30YR}}` | `housing.avg_mortgage_rate_30yr` |

**Fix location:** add these six to `directFields` in
`pfl-print-pipeline/resolver/resolve.mjs` (and to `CONTRACTED_TOKENS`, lines ~112-121),
plus `TOKEN_SPEC.md`. This is a resolver-map edit, not a data change.

---

## Phase 3 — Point every surface at the datasets (kill the copies)

### 3-Print (smallest; resolver already reads state JSON)
- `pfl-print-pipeline/resolver/resolve.mjs`:
  - Add the 6 tokens above to `buildVariableMapping` / `CONTRACTED_TOKENS`.
  - Repoint `STATE_JSON` (line ~26) from `sources/state-variables/oklahoma.json` to
    `state-data/states/{state}.json` (parameterized per state).
  - Inject **federal** figures from `state-data/federal/federal_figures.json` instead of
    reading the gate fixture; replace hardcoded FICA 7.65% (line ~30) with a dataset read.
- `pfl-print-pipeline/gate/validate-data.mjs` + gate T4: assert against
  `federal_figures.json` (or the fixture derived from it).

### 3-Live (largest; no resolver exists today)

**Repo note:** the actively-maintained live app is the nested clone
`Sync-90/resources/pfl-academy-sync-90` (remote `pfl-academy-sync-90.git`, Dec 2025),
NOT the older outer `Sync-90` (remote `pfl-academy-90-dashboards.git`, Apr 2025). No
`vercel.json` is committed in either, so which one is the production Vercel project must
be confirmed by Seb. The Phase-1 calculator PR was opened against BOTH (PR
`pfl-academy-90-dashboards#1`, PR `pfl-academy-sync-90#2`) — merge whichever is live.

**Two DIFFERENT token vocabularies exist — unify them.** The live app already inserted
its own `{{TOKEN}}` set into markdown (via `pfl-academy-sync-90/add_state_variables.py`):
`{{STATE_NAME}}`, `{{INCOME_TAX_RATE}}`, `{{SALES_TAX}}`, `{{MIN_WAGE}}`,
`{{MEDIAN_RENT}}`, `{{MEDIAN_HOME_PRICE}}`, `{{AVG_MORTGAGE_RATE_30YR}}`,
`{{PROPERTY_TAX_COUNTY_RATE}}`, `{{HOMEOWNERS_AVG_MONTHLY}}`, etc. — but **no runtime
resolver reads them** (commit message says values "will be populated" — future tense).
These names differ from the print resolver's `{{STATE_MEDIAN_RENT}}` / `{{STATE_...}}`
convention. Phase 3 must pick ONE token vocabulary keyed to `{state}.json` field paths so
live and print share the resolver contract, not two parallel ones.

Live currently has **no** figure resolver — federal numbers are baked literally in
Supabase content prose AND hardcoded in `taxCalculations.ts`; state figures are dangling
`{{TOKEN}}` placeholders with no substitution layer. Build the read path:
- **Federal constants:** replace the literal arrays in
  `Sync-90/src/lib/taxCalculations.ts` with a build-time import of
  `federal_figures.json` (a generated `taxConstants.generated.ts`, or a Vite JSON
  import). Removes the hand-maintained constants the Phase-1 PR just corrected.
- **Federal prose:** the 2023 figures are literal text in the Supabase-baked chapter
  content (student `day1.md` → Supabase `chapter_content`). Introduce token placeholders
  in content and a seed-time substitution from `federal_figures.json`, so a re-seed
  updates prose. (Design decision: seed-time substitution vs runtime resolve — seed-time
  is simpler and matches how content is already delivered.)
- **De-duplicate:** `taxCalculations.ts` exists byte-identical in **6 locations** (all
  Sync-90 variants + dojo + "Sync-90 copy"). Collapse to one shared module the build
  imports; delete the copies. (Single-source violation flagged in Run 1.)

### 3-Free-PDF (fixes wrong-state AND currency in one move)
- `generate_state_resources.py` today rebrands Oklahoma's HTML for ~28 states with only
  cosmetic title/header edits — **body figures are Oklahoma's, name-swapped**. Rewrite so
  per-state output resolves tokens from `federal_figures.json` + `state-data/states/{state}.json`
  instead of copying Oklahoma. This replaces `sanitize_html_content()`'s
  title-only rewrite with real token substitution.
- **Download stub:** the roadmap flags a `console.log`-only download handler. Run-1 audit
  found **no** such stub in `generate_state_resources.py` (it emits no JS), nor in the
  Oklahoma source HTML, nor in the generated `free-resources/` output. Locate the actual
  broken download surface before "fixing" it — likely a front-end "Download Materials"
  button in the live app, not this generator. (Deterministic follow-up; do not guess.)

---

## What needs Seb / Denis vs. what CC can do alone

| Work | Owner | Why |
|---|---|---|
| Create `federal_figures.json` from the gate fixture | **CC** | pure file authoring from verified source |
| Add `property_tax_effective_rate` + `data_as_of` to 36 `{state}.json` | **CC** | derived/label fields; data already present |
| Reconcile Oklahoma stale vs corrected copy | **CC** | file merge |
| Add 6 tokens to `resolve.mjs` + `CONTRACTED_TOKENS` + `TOKEN_SPEC.md` | **CC** | code edit, testable via gate |
| Repoint print resolver `STATE_JSON` / federal read | **CC** | code edit |
| Rewrite `generate_state_resources.py` token substitution | **CC** | code edit (needs `ANTHROPIC_API_KEY` in env for the standards-mapping call — already env-based) |
| Wire `taxCalculations.ts` to import `federal_figures.json` + collapse 6 copies | **CC** | code edit; open PR |
| **Set the 2026 SS wage base / per-worker max value** | **Seb/Denis** | authoritative figure not yet published in any in-repo source; must be entered by a human (handoff explicitly says do not invent) |
| **Supabase re-seed of chapter content** (apply tokenized prose + new figures) | **Seb** | requires the Supabase **service key** (RLS-gated); CC cannot write to `chapter_content` |
| **Deploy / cache-bust live** after re-seed | **Seb** | needs the deploy hook / prod credentials |
| Rotate the ~14 hardcoded API keys (Phase 0 outstanding) | **Seb** | key rotation is an account action |
| Approve/merge PRs (financial changes never auto-merge) | **Seb/Denis** | human-confirm gate on tax data |

**CC-alone deliverable for the next run:** author `federal_figures.json`, backfill the two
missing fields across all `{state}.json`, reconcile Oklahoma, wire the 6 tokens, and open
PRs for the print resolver + free-PDF generator + `taxCalculations.ts` de-dup. Everything
that touches Supabase content or a live deploy stops at Seb.
