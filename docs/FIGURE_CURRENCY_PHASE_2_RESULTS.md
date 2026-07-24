# Figure-Currency Wiring — Phase 2 Results (Run 2)

**Date:** 2026-07-24. Branch: `figure-currency-phase-2-datasets` (off `docs/figure-currency-phase-2-3-plan`).
**Scope:** build the two canonical datasets. No code wiring (that is Phase 3). No prod/master pushes.
Print pipeline left extraction-only.

**Guardrail applied:** every value traces to an authoritative in-repo source
(`gate/fixtures/tax_brackets_2026.json`, `docs/TAX_CURRENCY_2026_HANDOFF.md`, or the corrected
`sources/state-variables/*.json`) **or** is a clearly-marked `TODO` STOP-flagged for a human. **Zero
figures were invented.**

---

## 2A — State-source reconciliation

### Which source is canonical
The **corrected print-pipeline source** (`pfl-print-pipeline/sources/state-variables/*.json`) is
authoritative — it carries `data_as_of` stamps from the Feb/Jul-2026 correction work; the
`state-data/states/*.json` copies did not. **Action taken:** the corrected copy is now made canonical in
`state-data/states/` (see Oklahoma below).

### Scope limit (deterministic, from source)
The corrected set contains **exactly one state file: `oklahoma.json`** (plus a `.stale-backup`). Its
README confirms OK was the SINGLE drop-in point (Amendment C) and that the corrected copy had been the
"OPEN ITEM 1 — not yet located." It is now located and applied. **There is therefore only one
cross-source divergence pair to report — Oklahoma.** No other state exists in the corrected set, so no
other state-to-state divergence is possible from these two sources.

### Oklahoma divergence list (corrected → what was in `state-data/states/oklahoma.json`)
Value corrections (stale → corrected):

| Field | Stale (state-data) | Corrected (canonical) |
|---|---|---|
| `taxes.income_tax_rate` | **4.75** | **4.5** (HB 2764 top marginal, eff. 2026-01-01) |
| `taxes.tax_structure` (text) | "Flat 4.75% income tax…" | "Flat 4.5% income tax…" |
| `calculated_values.calculated_state_tax_70k` | 3325 | 3150 |
| `calculated_values.property_tax_300k` | **363** (implausible) | **2610** (= 0.87% × 300k) |
| `calculated_values.state_tax_on_3500_monthly` | 166 | 158 |
| `calculated_values.state_withholding_48k_monthly` | 190 | 180 |
| `calculated_values.take_home_pay_70k` | 51560 | 51695 |
| `calculated_values.total_effective_rate` | 18.6 | 18.5 |

Fields present in corrected but **missing** from the stale copy (now added by making corrected canonical):
`data_as_of`, `taxes.property_tax_effective_rate` (0.87), `taxes.capital_gains_tax`, `taxes.estate_tax`,
`housing.days_on_market`, `housing.construction_trend`, `housing.realtor_website`,
`insurance.uninsured_rate`, `insurance.medicaid_expansion_status`, `employment.median_income`,
`employment.population_growth`, `employment.job_growth`, `education.tuition_community`,
`education.grant_program`, `education.plan_529_name`, `education.plan_529_url`,
`consumer_protection.age_of_majority`, `consumer_protection.security_deposit_limit`,
`consumer_protection.landlord_tenant_law_url`, `data_sources.economic_development_url`.
(No field was present in the stale copy but absent from corrected — corrected is a strict superset.)

**Result:** `state-data/states/oklahoma.json` == corrected copy. Oklahoma reconciled to **4.5%**; **zero
`4.75%` remains in `oklahoma.json`.** (Remaining `4.75` occurrences elsewhere are legitimate and
unrelated: Louisiana Shreveport & Illinois/Chicago *local sales* rates.)

### Additional flags found during 2A (NOT auto-changed)

1. **Kentucky — pre-existing UNCOMMITTED correction in the working tree.** `state-data/states/kentucky.json`
   already carried, before this run, `income_tax_rate 4.0 → 3.5`, `data_as_of "2026-07"`,
   `property_tax_effective_rate 0.74`, and recomputed `calculated_values`. It was **not** authored this
   run and its values have **no traceable in-repo authoritative source** (the corrected set has only OK).
   The change is internally consistent (0.74% × 300k = 2220 = its `property_tax_300k`) and matches the
   real 2026 KY flat-rate cut, but **provenance is unverified.** Left exactly as-is; committed with the
   Phase-2 batch so the branch is self-consistent. **STOP-FLAG:** confirm KY's 3.5% and 0.74 against an
   authoritative source before merge.

2. **North Carolina — `income_tax_rate: 4.75` looks stale for 2026.** NC's flat rate was 4.75% in 2023
   and has been stepping down annually. No authoritative in-repo 2026 source exists, so it was **not
   changed.** **STOP-FLAG:** confirm/supply the NC 2026 rate.

3. Ignored per instruction as pre-Feb-2026 stale: `STATE_CORRECTIONS_MASTER`, `ALL-STATES-COMBINED`.

---

## 2B — `state-data/federal/federal_figures.json`

New file created: `state-data/federal/federal_figures.json` (new `federal/` dir). Carries
`data_as_of: "2026-07"`. Validates as JSON; all expected top-level keys present or explicitly TODO'd.

**Authoritative values included** (traceable):
standard deduction (all 4 statuses) + additional std deduction; full single/MFJ/HoH bracket ceilings;
filing thresholds; 401(k) $24,500 (+catch-ups $8,000 / $11,250); IRA $7,500 (+catch-up $1,100); undergrad
Direct loan rate **6.52%**; FICA total **7.65%** (resolver §Formulas), Social Security **6.2%** (handoff),
Medicare **1.45%** (= 7.65 − 6.2).

**TODO — STOP-flagged (no authoritative in-repo source; do not invent):**

| Field | Blocks live PR merge? |
|---|---|
| `salt_deduction_cap.cap_2026` | **YES** — see SALT finding below |
| `payroll_taxes.social_security_wage_base` | no (handoff states it is unpublished) |
| `payroll_taxes.social_security_employee_max` (= wage_base × 0.062) | no (blocked on wage base) |
| `retirement_contribution_limits.hsa_self_only / hsa_family / hsa_catchup_55_plus` | no |
| `payroll_taxes.additional_medicare_rate / additional_medicare_threshold` | no |

### SALT question from Run 1 — RESOLVED
**Yes — the SALT cap IS read in the live compute path.**
`Sync-90/src/lib/taxCalculations.ts` → `calculateItemizedDeductions()` uses
`Math.min(stateTaxes, saltCap)` with `saltCap` hardcoded `10000` (identical in all 6 `taxCalculations.ts`
copies). Because it feeds the itemized-vs-standard decision, **the missing authoritative 2026 SALT figure
BLOCKS the live PR merge** — the hardcoded `10000` is the pre-2026 value and cannot be confirmed current
for 2026 without a supplied source.

---

## 2C — `{state}.json` backfill

Applied to all 36 files:

- **`data_as_of`** added to every file (gate: every dataset file carries the stamp — **PASS**).
  - Oklahoma → `2026-07` (corrected source). Kentucky → `2026-07` (pre-existing). The other 34 →
    `2025-11`, derived from each file's in-repo `last_updated` (Nov 2025). This honestly reflects data
    vintage — these 34 states have NOT been re-verified for 2026, and the stamp correctly signals that to
    the resolver's staleness watermark. (Not a financial figure; traces to `last_updated`.)
- **`property_tax_effective_rate`**:
  - **Oklahoma 0.87** — authoritative (corrected source).
  - **Kentucky 0.74** — pre-existing working-tree value, provenance unverified (see 2A flag).
  - **Other 34 states → `null` + `property_tax_effective_rate_todo`** naming the field. **No authoritative
    2026 in-repo source exists for these** (the corrected set has only OK; the uncorrected
    `calculated_values.property_tax_300k` is unreliable — OK's stale copy had 363, off by ~7×). Per
    guardrail, not invented. **STOP-FLAG:** supply 34 authoritative effective property-tax rates (list below).

**34 states needing an authoritative `property_tax_effective_rate`:** alabama, california, colorado,
connecticut, delaware, florida, georgia, illinois, indiana, iowa, kansas, louisiana, maine, maryland,
michigan, minnesota, mississippi, missouri, nebraska, new-hampshire, new-jersey, new-york,
north-carolina, ohio, oregon, pennsylvania, rhode-island, south-carolina, tennessee, texas, utah,
virginia, west-virginia, wisconsin.

### 6 dangling tokens — backing CONFIRMED
All six Run-1 tokens are backed by real fields present in **all 36** `{state}.json` files:

| Token | Backing field | Present in all 36? |
|---|---|---|
| `{{STATE_MEDIAN_RENT}}` | `housing.median_rent` | ✅ |
| `{{STATE_MEDIAN_HOME_PRICE}}` | `housing.median_home_price` | ✅ |
| `{{STATE_HOUSING_MARKET_TRENDS}}` | `housing.housing_market_trends` | ✅ |
| `{{STATE_UNEMPLOYMENT_RATE}}` | `employment.unemployment_rate` | ✅ |
| `{{STATE_MAJOR_INDUSTRIES}}` | `employment.major_industries` | ✅ |
| `{{STATE_AVG_MORTGAGE_RATE_30YR}}` | `housing.avg_mortgage_rate_30yr` | ✅ |

None missing. (The resolver-map wiring of these tokens is a Phase-3 code edit, out of scope here.)

---

## Gate checklist

| Gate | Status |
|---|---|
| Every dataset file carries `data_as_of` | ✅ 36/36 states + federal |
| Every value traces to authoritative source or flagged TODO (zero invented) | ✅ |
| `federal_figures.json` validates (keys present or TODO'd) | ✅ |
| Oklahoma reconciled to 4.5%; zero `4.75%` in canonical OK source | ✅ |

## STOP-flags for Seb/Denis to supply (blocking merge decisions)

1. **2026 SALT cap** — **blocks live PR merge** (in compute path).
2. **2026 SS wage base** (→ derives SS employee max + p286 figure).
3. **34 states' `property_tax_effective_rate`** (list above).
4. **Confirm Kentucky 3.5% / 0.74** (unverified working-tree provenance).
5. **Confirm North Carolina 2026 income rate** (4.75% looks stale).
6. HSA 2026 limits; additional-Medicare rate + threshold.
