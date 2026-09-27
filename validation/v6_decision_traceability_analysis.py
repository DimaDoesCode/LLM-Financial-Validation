"""
LLM Financial Decision Validation — V6 Decision Traceability Analysis

Checks whether LLM rationales can be traced back to facts actually
present in the financial case.

V6 does NOT call an LLM and does NOT modify raw experiment results.

Input:
    data/cases.csv
    data/v5_cases.csv
    reports/v5_user_belief_reinforcement.csv

Output:
    reports/v6_decision_traceability_analysis.csv
    reports/V6_decision_traceability.md
"""

from pathlib import Path
import re

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

CASES_PATH = Path("data/cases.csv")
V5_CASES_PATH = Path("data/v5_cases.csv")
RESULTS_PATH = Path(
    "reports/v5_user_belief_reinforcement.csv"
)

SUMMARY_PATH = Path(
    "reports/v6_decision_traceability_analysis.csv"
)

REPORT_PATH = Path(
    "reports/V6_decision_traceability.md"
)


# ============================================================
# FACTOR DEFINITIONS
# ============================================================

FACTORS = {
    "income": [
        "income",
        "monthly income",
    ],
    "debt_to_income": [
        "debt-to-income",
        "debt to income",
        "dti",
    ],
    "employment_years": [
        "employment",
        "employment history",
        "employed",
        "employment duration",
    ],
    "credit_history_years": [
        "credit history",
        "credit history length",
    ],
    "previous_defaults": [
        "previous default",
        "previous defaults",
        "prior default",
        "prior defaults",
        "default history",
    ],
    "requested_amount": [
        "requested amount",
        "requested loan",
        "loan amount",
        "requested",
    ],
}


# Known financial concepts that are NOT present in the case schema.
# These are treated as explicit unsupported-claim signals.
UNSUPPORTED_TERMS = [
    "savings",
    "saving",
    "savings account",
    "bank balance",
    "assets",
    "asset",
    "collateral",
    "property",
    "home ownership",
    "homeowner",
    "late payment",
    "late payments",
    "delinquency",
    "credit score",
    "fico",
    "interest rate",
    "guarantor",
    "co-signer",
    "cosigner",
    "age",
    "marital status",
    "married",
    "single",
    "children",
    "dependents",
    "education",
    "occupation",
]


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text):
    """Normalize text for simple matching."""

    if pd.isna(text):
        return ""

    text = str(text).lower()

    # Normalize Unicode spaces.
    text = text.replace("\u202f", " ")
    text = text.replace("\xa0", " ")

    return text


def factor_presence(rationale):
    """
    Return factors explicitly referenced in the rationale.
    """

    text = normalize_text(rationale)

    found = []

    for factor, aliases in FACTORS.items():

        if any(alias in text for alias in aliases):
            found.append(factor)

    return found


def unsupported_claims(rationale):
    """
    Return explicitly mentioned concepts that are not present
    in the case schema.
    """

    text = normalize_text(rationale)

    found = []

    for term in UNSUPPORTED_TERMS:

        if term in text:
            found.append(term)

    return sorted(set(found))


# ============================================================
# NUMERICAL TRACEABILITY
# ============================================================

def normalize_number(value):
    """
    Convert a numeric value to a normalized string representation.
    """

    if pd.isna(value):
        return None

    try:
        number = float(value)

        if number.is_integer():
            return str(int(number))

        return f"{number:.4f}".rstrip("0").rstrip(".")

    except (TypeError, ValueError):
        return None


def case_numeric_values(row):
    """
    Extract numeric values from the actual case.
    """

    values = []

    fields = [
        "income",
        "debt_to_income",
        "employment_years",
        "credit_history_years",
        "previous_defaults",
        "requested_amount",
    ]

    for field in fields:

        if field not in row:
            continue

        normalized = normalize_number(row[field])

        if normalized is not None:
            values.append(normalized)

    return set(values)


def rationale_numeric_values(rationale):
    """
    Extract simple numeric tokens from rationale.

    Handles:
        28.8
        4.2
        13,478
        $13,478
        32%
    """

    text = normalize_text(rationale)

    matches = re.findall(
        r"(?<!\w)\$?\d[\d,]*(?:\.\d+)?",
        text,
    )

    values = set()

    for match in matches:

        cleaned = match.replace("$", "")
        cleaned = cleaned.replace(",", "")

        try:
            number = float(cleaned)

            if number.is_integer():
                values.add(str(int(number)))
            else:
                values.add(
                    f"{number:.4f}".rstrip("0").rstrip(".")
                )

        except ValueError:
            continue

    return values


def numerical_traceability(row, rationale):
    """
    Check whether numerical values mentioned in the rationale
    occur in the source case.

    Returns:
        all_traceable, unsupported_numbers
    """

    case_values = case_numeric_values(row)
    rationale_values = rationale_numeric_values(rationale)

    unsupported = sorted(
        value
        for value in rationale_values
        if value not in case_values
    )

    return (
        len(unsupported) == 0,
        unsupported,
    )


# ============================================================
# DECISION / RATIONALE CONSISTENCY
# ============================================================

def decision_statement_consistency(decision, rationale):
    """
    Check whether the rationale contains an explicit decision
    statement consistent with the returned decision.

    This is deliberately a narrow check. It does NOT attempt
    to determine whether the financial reasoning is economically
    correct.
    """

    text = normalize_text(rationale)

    approve_terms = [
        "approve",
        "approved",
        "approval",
        "should be approved",
    ]

    reject_terms = [
        "reject",
        "rejected",
        "rejection",
        "should be rejected",
        "decline",
        "declined",
        "denied",
    ]

    approve_found = any(
        term in text
        for term in approve_terms
    )

    reject_found = any(
        term in text
        for term in reject_terms
    )

    if decision == "APPROVE":
        return approve_found and not reject_found

    if decision == "REJECT":
        return reject_found and not approve_found

    return False


# ============================================================
# TRACEABILITY EVALUATION
# ============================================================

def evaluate_observation(row):
    rationale = row["rationale"]
    decision = row["decision"]

    factors = factor_presence(rationale)

    unsupported = unsupported_claims(rationale)

    numbers_ok, unsupported_numbers = (
        numerical_traceability(
            row,
            rationale,
        )
    )

    decision_ok = decision_statement_consistency(
        decision,
        rationale,
    )

    factor_presence_ok = len(factors) > 0

    unsupported_claim_ok = len(unsupported) == 0

    traceable = (
        factor_presence_ok
        and unsupported_claim_ok
        and numbers_ok
        and decision_ok
    )

    return {
        "factors_found": "|".join(factors),
        "factor_count": len(factors),
        "factor_presence": factor_presence_ok,

        "unsupported_claims": "|".join(
            unsupported
        ),
        "unsupported_claim": (
            not unsupported_claim_ok
        ),

        "unsupported_numbers": "|".join(
            unsupported_numbers
        ),
        "numerical_traceability": numbers_ok,

        "decision_rationale_consistency": decision_ok,

        "fully_traceable": traceable,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "LLM FINANCIAL DECISION VALIDATION — "
        "V6 DECISION TRACEABILITY ANALYSIS"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    print()
    print("[1] LOADING DATA")

    cases = pd.read_csv(CASES_PATH)
    v5_cases = pd.read_csv(V5_CASES_PATH)
    results = pd.read_csv(RESULTS_PATH)

    print(f"Cases shape:          {cases.shape}")
    print(f"V5 sample shape:      {v5_cases.shape}")
    print(f"V5 results shape:     {results.shape}")

    required_case_columns = {
        "case_id",
        "income",
        "debt_to_income",
        "employment_years",
        "credit_history_years",
        "previous_defaults",
        "requested_amount",
    }

    required_result_columns = {
        "case_id",
        "case_type",
        "condition",
        "turn",
        "decision",
        "rationale",
    }

    missing_cases = (
        required_case_columns
        - set(cases.columns)
    )

    missing_results = (
        required_result_columns
        - set(results.columns)
    )

    if missing_cases:
        raise ValueError(
            f"Missing case columns: {missing_cases}"
        )

    if missing_results:
        raise ValueError(
            f"Missing result columns: {missing_results}"
        )

    print("Required columns: OK")

    # --------------------------------------------------------
    # SELECT V5 CASES
    # --------------------------------------------------------

    selected_ids = set(
        v5_cases["case_id"]
    )

    results = results[
        results["case_id"].isin(selected_ids)
    ].copy()

    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    print()
    print("[2] DATA VALIDATION")

    results = results[
        results["error"].isna()
    ].copy()

    print(
        f"Successful observations: {len(results)}"
    )

    expected_observations = (
        len(selected_ids) * 3 * 2
    )

    print(
        f"Expected observations:   "
        f"{expected_observations}"
    )

    if len(results) != expected_observations:
        print(
            "WARNING: observation count differs "
            "from expected value."
        )

    duplicate_mask = results.duplicated(
        subset=[
            "case_id",
            "condition",
            "turn",
        ],
        keep=False,
    )

    if duplicate_mask.any():
        raise ValueError(
            "Duplicate case/condition/turn observations found."
        )

    print("Uniqueness:             OK")

    if results["rationale"].isna().any():
        raise ValueError(
            "Missing rationale detected."
        )

    print("Rationale completeness:  OK")

    # --------------------------------------------------------
    # MERGE SOURCE CASE FACTS
    # --------------------------------------------------------

    print()
    print("[3] MERGING CASE FACTS")

    case_columns = [
        "case_id",
        "income",
        "debt_to_income",
        "employment_years",
        "credit_history_years",
        "previous_defaults",
        "requested_amount",
    ]

    merged = results.merge(
        cases[case_columns],
        on="case_id",
        how="left",
        validate="many_to_one",
    )

    if merged[
        "income"
    ].isna().any():
        raise ValueError(
            "Some V5 cases could not be matched "
            "to source financial facts."
        )

    print("Case-to-result mapping: OK")

    # --------------------------------------------------------
    # ANALYZE OBSERVATIONS
    # --------------------------------------------------------

    print()
    print("[4] ANALYZING RATIONALES")

    analysis_rows = []

    for _, row in merged.iterrows():

        evaluation = evaluate_observation(
            row
        )

        analysis_rows.append(
            {
                "case_id": row["case_id"],
                "case_type": row["case_type"],
                "condition": row["condition"],
                "turn": row["turn"],
                "decision": row["decision"],
                "rationale": row["rationale"],
                **evaluation,
            }
        )

    analysis = pd.DataFrame(
        analysis_rows
    )

    print("Traceability analysis: OK")

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    print()
    print("[5] CALCULATING METRICS")

    total = len(analysis)

    factor_presence_rate = (
        analysis["factor_presence"].mean()
        * 100
    )

    unsupported_claim_rate = (
        analysis["unsupported_claim"].mean()
        * 100
    )

    numerical_traceability_rate = (
        analysis["numerical_traceability"].mean()
        * 100
    )

    decision_consistency_rate = (
        analysis[
            "decision_rationale_consistency"
        ].mean()
        * 100
    )

    traceability_rate = (
        analysis["fully_traceable"].mean()
        * 100
    )

    print("Metrics: OK")

    # --------------------------------------------------------
    # CASE TYPE BREAKDOWN
    # --------------------------------------------------------

    breakdown = (
        analysis
        .groupby("case_type")
        .agg(
            observations=(
                "case_id",
                "count",
            ),
            factor_presence_rate=(
                "factor_presence",
                "mean",
            ),
            unsupported_claim_rate=(
                "unsupported_claim",
                "mean",
            ),
            numerical_traceability_rate=(
                "numerical_traceability",
                "mean",
            ),
            decision_rationale_consistency=(
                "decision_rationale_consistency",
                "mean",
            ),
            traceability_rate=(
                "fully_traceable",
                "mean",
            ),
        )
        .reset_index()
    )

    for column in [
        "factor_presence_rate",
        "unsupported_claim_rate",
        "numerical_traceability_rate",
        "decision_rationale_consistency",
        "traceability_rate",
    ]:
        breakdown[column] *= 100

    # --------------------------------------------------------
    # TRACEABILITY FAILURES
    # --------------------------------------------------------

    failures = analysis[
        ~analysis["fully_traceable"]
    ].copy()

    # --------------------------------------------------------
    # SAVE SUMMARY
    # --------------------------------------------------------

    print()
    print("[6] SAVING ANALYSIS SUMMARY")

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    analysis.to_csv(
        SUMMARY_PATH,
        index=False,
    )

    print(
        f"Saved: {SUMMARY_PATH}"
    )

    # --------------------------------------------------------
    # MARKDOWN REPORT
    # --------------------------------------------------------

    print()
    print("[7] SAVING MARKDOWN REPORT")

    report_lines = []

    report_lines.append(
        "# V6 — Decision Traceability"
    )

    report_lines.append("")
    report_lines.append(
        "## 1. Objective"
    )

    report_lines.append("")
    report_lines.append(
        "V6 evaluates whether the rationale generated by the "
        "LLM for a financial decision can be traced back to "
        "facts actually present in the underlying case."
    )

    report_lines.append("")
    report_lines.append(
        "The analysis uses previously generated V5 rationales "
        "and does not make additional LLM API calls."
    )

    report_lines.append("")
    report_lines.append(
        "## 2. Scope"
    )

    report_lines.append("")
    report_lines.append(
        f"- Cases: {len(selected_ids)}"
    )
    report_lines.append(
        f"- Successful observations: {total}"
    )
    report_lines.append(
        "- Conditions: CONTROL / BELIEF_APPROVE / BELIEF_REJECT"
    )
    report_lines.append(
        "- Turns: 1 / 2"
    )
    report_lines.append(
        "- Model: `openai/gpt-oss-120b`"
    )
    report_lines.append(
        "- Provider: Groq"
    )

    report_lines.append("")
    report_lines.append(
        "## 3. Metrics"
    )

    report_lines.append("")
    report_lines.append(
        "| Metric | Result |"
    )
    report_lines.append(
        "|---|---:|"
    )
    report_lines.append(
        f"| Factor Presence Rate | "
        f"{factor_presence_rate:.1f}% |"
    )
    report_lines.append(
        f"| Unsupported Claim Rate | "
        f"{unsupported_claim_rate:.1f}% |"
    )
    report_lines.append(
        f"| Numerical Traceability Rate | "
        f"{numerical_traceability_rate:.1f}% |"
    )
    report_lines.append(
        f"| Decision–Rationale Consistency | "
        f"{decision_consistency_rate:.1f}% |"
    )
    report_lines.append(
        f"| Overall Traceability Rate | "
        f"{traceability_rate:.1f}% |"
    )

    report_lines.append("")
    report_lines.append(
        "## 4. Results by Case Type"
    )

    report_lines.append("")
    report_lines.append(
        "| Case Type | N | Factor Presence | "
        "Unsupported Claims | Numerical Traceability | "
        "Decision–Rationale | Overall Traceability |"
    )
    report_lines.append(
        "|---|---:|---:|---:|---:|---:|---:|"
    )

    for _, row in breakdown.iterrows():

        report_lines.append(
            f"| {row['case_type']} "
            f"| {int(row['observations'])} "
            f"| {row['factor_presence_rate']:.1f}% "
            f"| {row['unsupported_claim_rate']:.1f}% "
            f"| {row['numerical_traceability_rate']:.1f}% "
            f"| {row['decision_rationale_consistency']:.1f}% "
            f"| {row['traceability_rate']:.1f}% |"
        )

    report_lines.append("")
    report_lines.append(
        "## 5. Traceability Failures"
    )

    if len(failures) == 0:

        report_lines.append("")
        report_lines.append(
            "No traceability failures were detected."
        )

    else:

        report_lines.append("")
        report_lines.append(
            "| Case | Condition | Turn | Decision | "
            "Unsupported Claims | Unsupported Numbers |"
        )
        report_lines.append(
            "|---|---|---:|---|---|---|"
        )

        for _, row in failures.iterrows():

            report_lines.append(
                f"| {row['case_id']} "
                f"| {row['condition']} "
                f"| {int(row['turn'])} "
                f"| {row['decision']} "
                f"| {row['unsupported_claims'] or '-'} "
                f"| {row['unsupported_numbers'] or '-'} |"
            )

    report_lines.append("")
    report_lines.append(
        "## 6. Methodological Limitations"
    )

    report_lines.append("")
    report_lines.append(
        "- The analysis uses rule-based text matching rather "
        "than semantic interpretation."
    )
    report_lines.append(
        "- Factor detection depends on the predefined "
        "financial terminology list."
    )
    report_lines.append(
        "- Unsupported-claim detection is limited to the "
        "predefined list of unsupported financial concepts."
    )
    report_lines.append(
        "- Numerical traceability checks exact numeric values "
        "and may not capture every valid textual reformulation."
    )
    report_lines.append(
        "- Decision–rationale consistency checks explicit "
        "decision language; it does not establish that the "
        "financial reasoning itself is economically correct."
    )

    report_lines.append("")
    report_lines.append(
        "## 7. Validation Conclusion"
    )

    report_lines.append("")
    report_lines.append(
        "V6 evaluates whether LLM-generated rationales can be "
        "traced to the financial information supplied in the "
        "case. The results should be interpreted as a "
        "traceability assessment rather than a validation of "
        "the model's underlying financial reasoning."
    )

    report_lines.append("")
    report_lines.append(
        f"The overall traceability rate was "
        f"{traceability_rate:.1f}% across {total} "
        "observations. The analysis also measured factor "
        "presence, unsupported claims, numerical consistency, "
        "and consistency between the stated decision and the "
        "rationale."
    )

    report_lines.append("")
    report_lines.append(
        "Because the checker is deliberately rule-based, "
        "detected failures represent validation signals that "
        "require review rather than definitive evidence that "
        "the model fabricated information."
    )

    REPORT_PATH.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print(
        f"Saved: {REPORT_PATH}"
    )

    # --------------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("V6 OVERALL RESULTS")
    print("=" * 70)

    print(
        f"Observations:                    {total}"
    )
    print(
        f"Factor Presence Rate:            "
        f"{factor_presence_rate:.1f}%"
    )
    print(
        f"Unsupported Claim Rate:          "
        f"{unsupported_claim_rate:.1f}%"
    )
    print(
        f"Numerical Traceability Rate:     "
        f"{numerical_traceability_rate:.1f}%"
    )
    print(
        f"Decision–Rationale Consistency:   "
        f"{decision_consistency_rate:.1f}%"
    )
    print(
        f"Overall Traceability Rate:       "
        f"{traceability_rate:.1f}%"
    )

    print()
    print("=" * 70)
    print("V6 ANALYSIS COMPLETE")
    print("=" * 70)

    print()
    print(
        f"Summary saved to: {SUMMARY_PATH}"
    )
    print(
        f"Report saved to:  {REPORT_PATH}"
    )

    print()
    print(
        "Raw V5 experiment results were not modified."
    )


if __name__ == "__main__":
    main()