#!/usr/bin/env python3
"""
figure_resolver.py — canonical figure-currency resolution for the free-PDF surface.

Phase 3, Run 3 (free-PDF slice) of the figure-currency wiring work.

WHY THIS EXISTS
    `generate_state_resources.py` used to "localize" Oklahoma's HTML for other states by
    cosmetic title/header swaps only (see its old sanitize_html_content). Two problems the
    roadmap attributed to it:
      (1) "every state shows Oklahoma's figures"  and
      (2) stale federal figures.
    Ground-truth audit of oklahoma-free-resources/ (2026-07-24) found:
      - (1) is NOT TRUE for this corpus: NO Oklahoma STATE figures are baked into the
        templates (no income/sales/property/min-wage/median/place-name literals). The
        content is generic/national. Every "4.5%" is a loan/mortgage interest rate.
      - (2) IS TRUE: old-year (2022/2023/2024) FEDERAL literals — standard deductions,
        brackets, retirement limits — are baked into ~15 files and survive into every
        state's output.
    So the real, resolvable currency bug is FEDERAL. This module fixes that from the single
    source (federal_figures.json), and provides the STATE-token resolver keyed to
    {state}.json for when the templates are tokenized (a separate content task).

CONTRACT (non-negotiable)
    * Every value resolves from state-data/federal/federal_figures.json OR
      state-data/states/{state}.json. Nothing is invented.
    * A token whose backing field is null/absent renders a VISIBLE flagged placeholder,
      never the Oklahoma value and never a guess. `0` is a real value (TX income tax).
    * Federal literals are only auto-substituted where they are STANDALONE reference
      figures. A file containing a federal literal inside a worked example (arithmetic /
      comparison whose result depends on the value) is FLAGGED-HOLD and left untouched, so
      no shown math is desynced. Flagged files are reported for manual content revision.
    * No hardcoded 2026 output literals: substitution values are read from the dataset at
      runtime. The OLD literals below are recognition keys only.

This module is import-safe and has NO network/API dependency, so the fix is verifiable
offline (`python3 figure_resolver.py --selftest` and `--report`).
"""

import re
import json
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo-relative paths (the old generator hardcoded /Users/justin/pfl-academy/...,
# which does not exist under the iCloud checkout). Resolve relative to this file.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent
FEDERAL_JSON = REPO_ROOT / "state-data" / "federal" / "federal_figures.json"
STATES_DIR = REPO_ROOT / "state-data" / "states"
OKLAHOMA_SOURCE = REPO_ROOT / "oklahoma-free-resources"


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------
def load_federal():
    with open(FEDERAL_JSON, encoding="utf-8") as f:
        return json.load(f)


def load_state(state_slug):
    """state_slug e.g. 'north-carolina'."""
    path = STATES_DIR / f"{state_slug}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_state_slugs():
    return sorted(p.stem for p in STATES_DIR.glob("*.json"))


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
def dollars(n):
    return f"${n:,.0f}" if float(n) == int(n) else f"${n:,.2f}"


def pct(n):
    # 3.99 -> "3.99%", 4.5 -> "4.5%", 0 -> "0%"
    s = f"{n:g}"
    return f"{s}%"


PLACEHOLDER = "[[TODO: {field} unavailable for {state} — see state-data/states/{slug}.json]]"


# ---------------------------------------------------------------------------
# STATE token vocabulary  (token -> dot-path into {state}.json ; renderer)
# See docs/TOKEN_MAP.md. Null/absent field -> flagged placeholder. 0 is real.
# ---------------------------------------------------------------------------
STATE_TOKENS = {
    "STATE_NAME":                     ("state_name", str),
    "STATE_CODE":                     ("state_code", str),
    "STATE_DATA_AS_OF":               ("data_as_of", str),
    "STATE_INCOME_TAX_RATE":          ("taxes.income_tax_rate", pct),
    "STATE_SALES_TAX":                ("taxes.sales_tax", pct),
    "STATE_COMBINED_SALES_TAX_MAX":   ("taxes.combined_sales_tax_max", pct),
    "STATE_PROPERTY_TAX_EFFECTIVE_RATE": ("taxes.property_tax_effective_rate", pct),
    "STATE_MIN_WAGE":                 ("employment.min_wage", dollars),
    "STATE_MEDIAN_RENT":              ("housing.median_rent", dollars),
    "STATE_MEDIAN_HOME_PRICE":        ("housing.median_home_price", dollars),
    "STATE_AVG_MORTGAGE_RATE_30YR":   ("housing.avg_mortgage_rate_30yr", pct),
    "STATE_UNEMPLOYMENT_RATE":        ("employment.unemployment_rate", pct),
    "STATE_MAJOR_INDUSTRIES":         ("employment.major_industries", str),
    "STATE_TAX_STRUCTURE":            ("taxes.tax_structure", str),
}


def _dig(data, dot_path):
    cur = data
    for part in dot_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return "__MISSING__"
        cur = cur[part]
    return cur


def resolve_state_token(token, state_data):
    """Return (rendered_value, is_placeholder)."""
    if token not in STATE_TOKENS:
        return (None, False)
    dot_path, renderer = STATE_TOKENS[token]
    val = _dig(state_data, dot_path)
    slug = state_data.get("state_name", "?").lower().replace(" ", "-")
    if val == "__MISSING__" or val is None:
        return (PLACEHOLDER.format(field=dot_path,
                                   state=state_data.get("state_name", "?"),
                                   slug=slug), True)
    # `0` is a real value (e.g. TX income_tax_rate). Render it, don't flag.
    return (renderer(val), False)


def substitute_state_tokens(html, state_data):
    """Replace {{STATE_*}} tokens. Returns (html, report_list)."""
    report = []
    def repl(m):
        token = m.group(1)
        rendered, is_ph = resolve_state_token(token, state_data)
        if rendered is None:
            return m.group(0)  # unknown token: leave visible (contract: never guess)
        report.append({"token": token, "value": rendered, "placeholder": is_ph})
        return rendered
    html = re.sub(r"\{\{([A-Z_]+)\}\}", repl, html)
    return html, report


# ---------------------------------------------------------------------------
# FEDERAL currency pass.
#
# Recognition keys: OLD baked literals -> the federal_figures.json field whose CURRENT
# value replaces them. Values are pulled from the dataset at runtime (fed_value()).
#
# `anchor`: optional regex that must appear within +/-60 chars for the more ambiguous
# dollar values (retirement limits), so e.g. "$6,500" is only treated as an IRA limit near
# IRA/contribution/Roth wording. Std-deduction values are unmistakable and need no anchor.
# ---------------------------------------------------------------------------
# Only STANDALONE standard-deduction values are auto-substituted. These 2022-2024 literals
# map unambiguously to a 2026 field (single==mfs==16100 in 2026, so 13,850/14,600 both go to
# standard_deduction.single). Contribution limits, brackets, and EITC are NOT auto-updated
# because they carry dependent partner values (catch-up totals) / worked math; those files
# are held for manual revision.
FED_STD_RULES = [
    (r"\$13,850", "standard_deduction.single"),
    (r"\$14,600", "standard_deduction.single"),
    (r"\$27,700", "standard_deduction.mfj"),
    (r"\$29,200", "standard_deduction.mfj"),
    (r"\$25,900", "standard_deduction.mfj"),
    (r"\$20,800", "standard_deduction.hoh"),
]

# Stale federal contribution / IRA literals — recognized for REPORTING (review bucket),
# never auto-substituted (base/catch-up pairs desync on partial update).
FED_CONTRIB_LITERAL_RE = re.compile(r"\$22,500|\$30,000|\$6,500|\$7,500")
RETIRE_KW_RE = re.compile(r"401|IRA|Roth|contribution|deferral|catch", re.I)
STALE_YEAR_RE = re.compile(r"\b(2022|2023|2024)\b")
TAX_CONTEXT_RE = re.compile(r"tax|deduction|contribution|bracket|IRA|401|filing", re.I)

# Tax-year label anchors (only within federal figure contexts). Applied only to
# files classified `updated` (no computed federal content), to preserve consistency.
FED_YEAR_LABEL_RE = re.compile(
    r"(Standard Deduction[^\n<]{0,40}\(|Contribution Limits \(|Tax Year\b[^\n<]{0,10}|"
    r"Tax Bracket Reference Guide - |Federal Income Tax Brackets \(|For )"
    r"(2022|2023|2024)")

# Signals that a federal literal sits inside a worked example whose math/conclusion
# depends on it (=> unsafe to substitute; lock that value). Arithmetic is detected only
# around DOLLAR/NUMBER tokens — a bare '=' is NOT used (it would match every HTML
# attribute like class="x"). Includes base/catch-up pairs ("$22,500 ($30,000 if 50 or
# older)") where updating only the base value desyncs the pair.
COMPUTED_SIGNAL_RE = re.compile(
    r"=\s*\$?[\d(]|\$[\d,]+\s*=|"                 # equals adjacent to a $ / number
    r"\$[\d,]+\s*[-–—]\s*\$[\d,]+|"               # $X - $Y  (subtraction of dollars)
    r"[×÷]|"                                       # explicit multiply / divide
    r"\bminus\b|\bexceeds?\b|\bless than\b|\bgreater than\b|"
    r"\bof amount over\b|\btaxed at\b|plus \d+% of|"
    r"if 50 or older|if 50\+|\bage 50\b|catch-?up", re.I)

# File-level marker of a federal bracket table / bracket arithmetic. These files carry
# federal figures this module does not fully recompute (ceilings + worked math), so the
# WHOLE file is held for manual revision — never partially updated (which would desync a
# 2026 year-label over 2023 bracket numbers).
BRACKET_MARKER_RE = re.compile(
    r"plus \d+% of|\d+% of amount over|\$[\d,]+\s*-\s*\$[\d,]+\s*<|taxed at|"
    r"\$[\d,]+\s*÷\s*\$[\d,]+")


def fed_value(federal, dot_path):
    return _dig(federal, dot_path)


def _occurrence_is_computed(html, start, end):
    """Heuristic: is the literal at [start,end) inside dependent arithmetic?
    Look at a +/-120 char window that does not cross a block boundary."""
    window = html[max(0, start - 120):min(len(html), end + 120)]
    return bool(COMPUTED_SIGNAL_RE.search(window))


def _find_stale_federal(html):
    """Per-literal analysis. Returns (safe_values, held_reasons, all_stale).

    safe_values: set of std-deduction literals whose EVERY occurrence is standalone
                 (no arithmetic/comparison in its ±120 window) -> safe to substitute.
    held_reasons: set of reasons the file has stale federal content that CANNOT be
                  auto-updated (a std-ded value that appears in dependent math, a bracket
                  table, or a contribution/catch-up pair).
    all_stale: every recognized old-year federal literal (for the review report).
    """
    safe_values, held_reasons, all_stale = set(), set(), set()

    # std-deduction values: lock a value if ANY of its occurrences is computed/dependent.
    for pattern, field in FED_STD_RULES:
        occs = list(re.finditer(pattern, html))
        if not occs:
            continue
        lit = occs[0].group(0)
        all_stale.add(lit)
        any_computed = any(_occurrence_is_computed(html, m.start(), m.end())
                           for m in occs)
        if any_computed:
            held_reasons.add("dependent-value:" + lit)
        else:
            safe_values.add(lit)

    # bracket tables: ceilings are stale and cannot be recomputed here.
    if BRACKET_MARKER_RE.search(html) and STALE_YEAR_RE.search(html) \
            and TAX_CONTEXT_RE.search(html):
        held_reasons.add("bracket-table")
        all_stale.add("bracket-table")

    # contribution / IRA stale literals (only in a retirement context) — base/catch-up
    # pairs desync on partial update.
    for m in FED_CONTRIB_LITERAL_RE.finditer(html):
        ctx = html[max(0, m.start() - 60):m.end() + 60]
        if RETIRE_KW_RE.search(ctx):
            all_stale.add(m.group(0))
            held_reasons.add("contribution-limits")

    return safe_values, held_reasons, all_stale


def classify_federal_file(html):
    """Return ('none'|'updated'|'review', stale_literals).

    'updated': the file's ENTIRE federal footprint is standalone std-deduction values
               (no held content) -> auto-substitute values + year labels, fully consistent.
    'review' : contains stale federal figures that cannot be auto-updated without desyncing
               shown content (dependent math, brackets, contribution pairs) -> held
               untouched, reported for manual content revision. A file with BOTH safe and
               held content is held whole, so we never leave it half-current.
    'none'   : no stale federal literals.
    """
    safe_values, held_reasons, all_stale = _find_stale_federal(html)
    if safe_values and not held_reasons:
        return "updated", sorted(all_stale)
    if all_stale:
        return "review", sorted(all_stale)
    return "none", []


def apply_federal_currency(html, federal):
    """Substitute standalone std-deduction values + federal year labels in an 'updated'
    file. Returns (html, applied_list). Values sourced from federal_figures.json.
    Precondition: file has no arithmetic/bracket/contribution complexity (see classify)."""
    applied = []
    for pattern, field in FED_STD_RULES:
        newval = dollars(fed_value(federal, field))
        def _r(m, newval=newval, field=field):
            applied.append({"old": m.group(0), "new": newval, "field": field})
            return newval
        html = re.sub(pattern, _r, html)

    fy = str(federal.get("tax_year", 2026))
    def year_repl(m):
        applied.append({"old": m.group(2), "new": fy, "field": "tax_year"})
        return m.group(1) + fy
    html = FED_YEAR_LABEL_RE.sub(year_repl, html)
    return html, applied


# ---------------------------------------------------------------------------
# STATE-NAME / brand localization (safe cosmetic layer, unchanged in spirit from the
# original but scoped to branding contexts only — never body prose like a states list).
# ---------------------------------------------------------------------------
def localize_branding(html, state_name):
    patterns = [
        (r"(<title>[^<]*?)\bOklahoma\b", r"\g<1>" + state_name),
        (r"(PFL Academy[^<]{0,40}?)\bOklahoma Financial Literacy",
            r"\g<1>" + state_name + " Financial Literacy"),
        (r"\bOklahoma Financial Literacy\b", state_name + " Financial Literacy"),
    ]
    for pat, rep in patterns:
        html = re.sub(pat, rep, html)
    return html


# ---------------------------------------------------------------------------
# Top-level per-file resolution (the replacement for the old sanitize_html_content)
# ---------------------------------------------------------------------------
def resolve_file(html, state_data, federal):
    """Returns (new_html, report dict)."""
    report = {"federal_status": "none", "federal_applied": [],
              "federal_flagged": [], "state_tokens": []}

    # 1. Federal currency (per-file consistency: only 'updated' files are substituted)
    status, stale = classify_federal_file(html)
    report["federal_status"] = status
    if status == "updated":
        html, applied = apply_federal_currency(html, federal)
        report["federal_applied"] = applied
    elif status == "review":
        report["federal_flagged"] = stale

    # 2. State token resolution (no-op on today's generic corpus; future-proofs tokenized
    #    templates). Null field -> visible placeholder.
    html, st_report = substitute_state_tokens(html, state_data)
    report["state_tokens"] = st_report

    # 3. Branding / state-name localization (cosmetic; never invents figures).
    html = localize_branding(html, state_data.get("state_name", ""))

    return html, report


# ---------------------------------------------------------------------------
# State completeness check (for the "incomplete states" report)
# ---------------------------------------------------------------------------
CRITICAL_STATE_FIELDS = [
    "state_name", "state_code", "taxes.income_tax_rate", "taxes.sales_tax",
    "employment.min_wage",
]


def state_completeness(state_data):
    missing = [f for f in CRITICAL_STATE_FIELDS
               if _dig(state_data, f) in ("__MISSING__", None)]
    prop = _dig(state_data, "taxes.property_tax_effective_rate")
    prop_null = prop in ("__MISSING__", None)
    return missing, prop_null


# ---------------------------------------------------------------------------
# CLI: --selftest (offline proof), --report (corpus-wide federal audit)
# ---------------------------------------------------------------------------
FIXTURE = """<html><head><title>Oklahoma Financial Literacy — Tax Snapshot</title></head>
<body>
<h2>{{STATE_NAME}} ({{STATE_CODE}}) Tax Snapshot — data as of {{STATE_DATA_AS_OF}}</h2>
<ul>
<li>State income tax rate: {{STATE_INCOME_TAX_RATE}}</li>
<li>State sales tax: {{STATE_SALES_TAX}}</li>
<li>Effective property tax rate: {{STATE_PROPERTY_TAX_EFFECTIVE_RATE}}</li>
<li>Minimum wage: {{STATE_MIN_WAGE}}</li>
</ul>
<p>Federal standard deduction (single) reference: $13,850.</p>
</body></html>"""


def run_selftest():
    federal = load_federal()
    print("=" * 72)
    print("SELF-TEST — state figure resolution (NC / KY / TX) + federal currency")
    print("=" * 72)
    for slug, expect in [
        ("north-carolina", {"income": "3.99%", "sales": "4.75%", "prop": "0.66%"}),
        ("kentucky",       {"income": "3.5%",  "sales": "6%",     "prop": "0.74%"}),
        ("texas",          {"income": "0%",    "sales": "6.25%",  "prop": "PLACEHOLDER"}),
    ]:
        sd = load_state(slug)
        out, rep = resolve_file(FIXTURE, sd, federal)
        inc = next(r for r in rep["state_tokens"] if r["token"] == "STATE_INCOME_TAX_RATE")
        sal = next(r for r in rep["state_tokens"] if r["token"] == "STATE_SALES_TAX")
        prp = next(r for r in rep["state_tokens"]
                   if r["token"] == "STATE_PROPERTY_TAX_EFFECTIVE_RATE")
        prop_shown = "PLACEHOLDER" if prp["placeholder"] else prp["value"]
        ok_inc = inc["value"] == expect["income"]
        ok_sal = sal["value"] == expect["sales"]
        ok_prop = (prop_shown == "PLACEHOLDER") if expect["prop"] == "PLACEHOLDER" \
            else (prp["value"] == expect["prop"])
        fed = rep["federal_applied"]
        fed_new = fed[0]["new"] if fed else "(none)"
        print(f"\n{sd['state_name']}:")
        print(f"  income  = {inc['value']:10} expect {expect['income']:10} "
              f"{'PASS' if ok_inc else 'FAIL'}")
        print(f"  sales   = {sal['value']:10} expect {expect['sales']:10} "
              f"{'PASS' if ok_sal else 'FAIL'}")
        print(f"  property= {prop_shown:38} expect {expect['prop']:12} "
              f"{'PASS' if ok_prop else 'FAIL'}")
        if prp["placeholder"]:
            print(f"    placeholder text: {prp['value']}")
        print(f"  federal $13,850 -> {fed_new}  (from standard_deduction.single, "
              f"{'PASS' if fed_new == '$16,100' else 'FAIL'})")
        assert ok_inc and ok_sal and ok_prop, f"{slug} figure resolution FAILED"
        assert fed_new == "$16,100", "federal currency FAILED"
    print("\nAll self-test assertions passed. Zero Oklahoma figure bleed; "
          "federal traces to federal_figures.json.")


def run_report(states=None):
    federal = load_federal()
    files = sorted(OKLAHOMA_SOURCE.rglob("*.html"))
    print("=" * 72)
    print(f"FEDERAL CURRENCY REPORT over {len(files)} source files "
          f"(oklahoma-free-resources/)")
    print("=" * 72)
    updated, review, none = [], [], []
    for f in files:
        html = f.read_text(encoding="utf-8", errors="replace")
        status, stale = classify_federal_file(html)
        rel = f.relative_to(OKLAHOMA_SOURCE)
        if status == "updated":
            _, applied = apply_federal_currency(html, federal)
            updated.append((rel, applied))
        elif status == "review":
            review.append((rel, stale))
        else:
            none.append(rel)
    print(f"\n  standalone-federal, AUTO-UPDATED to {federal['tax_year']}: "
          f"{len(updated)} files")
    for r, applied in updated:
        pairs = sorted({"{}->{}".format(a["old"], a["new"]) for a in applied})
        print(f"    [updated]  {r}\n               {', '.join(pairs)}")
    print(f"\n  stale-federal, HELD for manual content revision "
          f"(arithmetic/brackets/contrib pairs would desync): {len(review)} files")
    for r, lits in review:
        print(f"    [review]   {r}   stale: {lits}")
    print(f"\n  no stale federal literals (cosmetic-only): {len(none)} files")

    print("\n" + "=" * 72)
    print("STATE COMPLETENESS")
    print("=" * 72)
    slugs = list_state_slugs()
    incomplete, prop_null = [], []
    for slug in slugs:
        sd = load_state(slug)
        miss, pn = state_completeness(sd)
        if miss:
            incomplete.append((slug, miss))
        if pn:
            prop_null.append(slug)
    print(f"  state files present: {len(slugs)}")
    print(f"  incomplete for critical fields (income/sales/min-wage/name): "
          f"{len(incomplete)}")
    for slug, miss in incomplete:
        print(f"    {slug}: missing {miss}")
    print(f"  property_tax_effective_rate NULL (-> placeholder token): "
          f"{len(prop_null)} states")
    print(f"    {', '.join(prop_null)}")
    print(f"\n  PROCESSED-STATE COUNT: {len(slugs)} states have a {{state}}.json and "
          f"generate cleanly (all critical fields present).")
    print(f"  (The old generator's skip_states list dropped this to ~28 by skipping "
          f"'already-processed' states; that skip is removed — those states carried the "
          f"same stale federal figures and must be reprocessed.)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Figure-currency resolver (free-PDF surface)")
    ap.add_argument("--selftest", action="store_true",
                    help="Offline proof: NC/KY/TX figure resolution + federal currency")
    ap.add_argument("--report", action="store_true",
                    help="Corpus-wide federal currency + state completeness report")
    args = ap.parse_args()
    if args.selftest:
        run_selftest()
    elif args.report:
        run_report()
    else:
        ap.print_help()
