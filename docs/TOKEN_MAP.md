# TOKEN_MAP — Figure-Currency Token Vocabulary

**Status:** written Phase 3, Run 3 (free-PDF slice), 2026-07-24.
**Purpose:** one canonical token → backing-field map so every surface (free PDF, live app,
print) resolves figures from the SAME two datasets instead of holding private copies. The
later live-resolver / print-resolver runs should adopt these token names (or map their
existing names onto these field paths) so the three surfaces share ONE contract rather than
three parallel vocabularies.

Two backing datasets, one per class of figure:

| Class | Backing dataset | Keyed by |
|---|---|---|
| Federal (national) | `state-data/federal/federal_figures.json` | field path below |
| State (per-state) | `state-data/states/{state}.json` | field path below |

**Golden rule (enforced by `generate_state_resources.py`):** a token whose backing field is
`null`/absent renders a visible flagged placeholder — `[[TODO: <field> unavailable for
<State> — see state-data/states/<state>.json]]` — never the Oklahoma value and never a
guess. `0` is a REAL value (e.g. Texas `income_tax_rate: 0`) and resolves to `0%`, NOT a
placeholder.

---

## Federal tokens → `federal_figures.json`

| Token | Backing field (dot path) | 2026 value | Render |
|---|---|---|---|
| `{{FED_TAX_YEAR}}` | `tax_year` | 2026 | `2026` |
| `{{FED_DATA_AS_OF}}` | `data_as_of` | 2026-07 | `2026-07` |
| `{{FED_STD_DEDUCTION_SINGLE}}` | `standard_deduction.single` | 16100 | `$16,100` |
| `{{FED_STD_DEDUCTION_MFJ}}` | `standard_deduction.mfj` | 32200 | `$32,200` |
| `{{FED_STD_DEDUCTION_HOH}}` | `standard_deduction.hoh` | 24150 | `$24,150` |
| `{{FED_STD_DEDUCTION_MFS}}` | `standard_deduction.mfs` | 16100 | `$16,100` |
| `{{FED_FICA_TOTAL_RATE}}` | `payroll_taxes.fica_total_rate` | 7.65 | `7.65%` |
| `{{FED_SOCIAL_SECURITY_RATE}}` | `payroll_taxes.social_security_rate` | 6.2 | `6.2%` |
| `{{FED_MEDICARE_RATE}}` | `payroll_taxes.medicare_rate` | 1.45 | `1.45%` |
| `{{FED_SS_WAGE_BASE}}` | `payroll_taxes.social_security_wage_base` | 184500 | `$184,500` |
| `{{FED_401K_ELECTIVE}}` | `retirement_contribution_limits.traditional_401k_elective_deferral` | 24500 | `$24,500` |
| `{{FED_401K_CATCHUP_50}}` | `retirement_contribution_limits.traditional_401k_catchup_50_plus` | 8000 | `$8,000` |
| `{{FED_IRA_LIMIT}}` | `retirement_contribution_limits.ira` | 7500 | `$7,500` |
| `{{FED_IRA_CATCHUP_50}}` | `retirement_contribution_limits.ira_catchup_50_plus` | 1100 | `$1,100` |
| `{{FED_HSA_SELF_ONLY}}` | `retirement_contribution_limits.hsa_self_only` | 4400 | `$4,400` |
| `{{FED_HSA_FAMILY}}` | `retirement_contribution_limits.hsa_family` | 8750 | `$8,750` |
| `{{FED_SALT_CAP_SINGLE}}` | `salt_deduction_cap.single` | 40400 | `$40,400` |
| `{{FED_STUDENT_LOAN_RATE}}` | `student_loan_rates.undergrad_direct_2026_27` | 6.52 | `6.52%` |
| `{{FED_INCOME_BRACKETS_SINGLE}}` | `income_tax_brackets.single[]` | (array) | rate/ceiling table |

### Old-year literals the free-PDF currency pass retires (federal)
These baked values in `oklahoma-free-resources/*.html` are what the generator maps to the
tokens above. Only **standalone reference** occurrences are auto-substituted; occurrences
inside a **worked example whose arithmetic/conclusion depends on the value** are STOP-flagged
for manual content revision (auto-substituting them would desync the shown math — e.g. a
"$15,000 exceeds the $13,850 standard deduction" example whose conclusion flips at $16,100).

| Old literal(s) | Vintage | Retire to |
|---|---|---|
| `$13,850` (single/MFS) | 2023 | `$16,100` |
| `$14,600` (single/MFS) | 2024 | `$16,100` |
| `$27,700` (MFJ) | 2023 | `$32,200` |
| `$29,200` (MFJ) | 2024 | `$32,200` |
| `$25,900` (MFJ) | 2022 | `$32,200` |
| `$20,800` (HoH) | 2023 | `$24,150` |
| `$22,500` (401k) | 2023 | `$24,500` |
| `$6,500` (IRA) | 2023 | `$7,500` |
| `2023` / `2024` tax-year label | — | `2026` |

Note: `7.65% / 6.2% / 1.45%` payroll rates are UNCHANGED in 2026 — they already equal the
dataset value, so no substitution is required; they nonetheless "trace to" the dataset.

---

## State tokens → `state-data/states/{state}.json`

| Token | Backing field (dot path) | Render | Null-handling |
|---|---|---|---|
| `{{STATE_NAME}}` | `state_name` | e.g. `North Carolina` | — (always present) |
| `{{STATE_CODE}}` | `state_code` | e.g. `NC` | — |
| `{{STATE_DATA_AS_OF}}` | `data_as_of` | `2026-07` | placeholder |
| `{{STATE_INCOME_TAX_RATE}}` | `taxes.income_tax_rate` | `3.99%` (TX → `0%`) | placeholder |
| `{{STATE_SALES_TAX}}` | `taxes.sales_tax` | `4.75%` | placeholder |
| `{{STATE_COMBINED_SALES_TAX_MAX}}` | `taxes.combined_sales_tax_max` | `7.5%` | placeholder |
| `{{STATE_PROPERTY_TAX_EFFECTIVE_RATE}}` | `taxes.property_tax_effective_rate` | `0.66%` | **placeholder for the 33 states where null** |
| `{{STATE_MIN_WAGE}}` | `employment.min_wage` | `$7.25` | placeholder |
| `{{STATE_MEDIAN_RENT}}` | `housing.median_rent` | `$1,395` | placeholder |
| `{{STATE_MEDIAN_HOME_PRICE}}` | `housing.median_home_price` | `$335,000` | placeholder |
| `{{STATE_AVG_MORTGAGE_RATE_30YR}}` | `housing.avg_mortgage_rate_30yr` | `7.10%` | placeholder |
| `{{STATE_UNEMPLOYMENT_RATE}}` | `employment.unemployment_rate` | `3.5%` | placeholder |
| `{{STATE_MAJOR_INDUSTRIES}}` | `employment.major_industries` | text | placeholder |
| `{{STATE_TAX_STRUCTURE}}` | `taxes.tax_structure` | text | placeholder |

### Cross-surface alignment note
The print resolver (`pfl-print-pipeline/resolver/resolve.mjs`) uses `{{STATE_MEDIAN_RENT}}`
/ `{{STATE_...}}` names; the live-app injector (`add_state_variables.py`) used bare
`{{INCOME_TAX_RATE}}` / `{{MEDIAN_RENT}}`. This map keys everything to the `{state}.json`
field PATH (the invariant), so any surface can adopt these names or alias its own onto the
same path. Unifying the literal token strings across surfaces is the remaining live/print
Phase-3 work; it is out of scope for the free-PDF slice.

---

## Corpus reality (free-PDF surface, verified 2026-07-24)

The `oklahoma-free-resources/` templates are **generic/national** content, NOT localized
with Oklahoma figures. Verified: `income_tax_rate 4.5%`-as-tax, `sales_tax`,
`property_tax_effective_rate 0.87%`, `min_wage 7.25`, median home/rent, place names
(Tulsa/Norman/Edmond) — **all absent as literals** across every OK source variant. Every
`4.5%` in the corpus is a loan/mortgage interest rate, not a tax rate.

Consequence: the STATE tokens above are the vocabulary for when these templates are
tokenized (a content task). On today's corpus the state pass legitimately finds **no
state-figure literals to currency-fix** — it only resolves `{{STATE_NAME}}` and cleans
residual "Oklahoma" branding. The FEDERAL tokens are the live currency target: old-year
federal literals ARE baked in (~15 files) and get retired to 2026.
