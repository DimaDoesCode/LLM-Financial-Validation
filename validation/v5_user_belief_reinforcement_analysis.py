"""
LLM Financial Validation — V5 User Belief Reinforcement Analysis

Analyzes the completed V5 sequential-dialogue experiment.

The experiment tests whether an explicitly expressed user belief
influences the LLM's subsequent financial decision.

No new LLM/API calls are performed.

Input:
    reports/v5_user_belief_reinforcement.csv

Outputs:
    reports/v5_user_belief_analysis.csv
    reports/V5_user_belief_reinforcement.md
"""

from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_PATH = Path(
    "reports/v5_user_belief_reinforcement.csv"
)

SUMMARY_PATH = Path(
    "reports/v5_user_belief_analysis.csv"
)

REPORT_PATH = Path(
    "reports/V5_user_belief_reinforcement.md"
)

CONDITIONS = [
    "CONTROL",
    "BELIEF_APPROVE",
    "BELIEF_REJECT",
]

EXPECTED_CASE_TYPES = [
    "CLEAR_APPROVE",
    "CLEAR_REJECT",
    "BORDERLINE",
    "CONFLICTING",
]


# ============================================================
# LOAD DATA
# ============================================================

def load_results():

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    required_columns = {
        "case_id",
        "case_type",
        "condition",
        "turn",
        "decision",
        "rationale",
        "error",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    print("=" * 70)
    print("LLM FINANCIAL VALIDATION — V5 USER BELIEF REINFORCEMENT ANALYSIS")
    print("=" * 70)

    print()
    print("[1] LOADING RESULTS")
    print(f"Results shape: {df.shape}")

    return df


# ============================================================
# VALIDATE COMPLETENESS
# ============================================================

def validate_results(df):

    successful = df[
        df["error"].fillna("").astype(str).str.strip() == ""
    ].copy()

    successful["turn"] = pd.to_numeric(
        successful["turn"],
        errors="coerce",
    )

    invalid_turns = successful[
        ~successful["turn"].isin([1, 2])
    ]

    if len(invalid_turns) > 0:
        raise ValueError(
            "Invalid turn values found."
        )

    expected_rows = 20 * 3 * 2

    if len(successful) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} successful observations, "
            f"found {len(successful)}."
        )

    duplicate_keys = successful.duplicated(
        subset=["case_id", "condition", "turn"],
        keep=False,
    )

    if duplicate_keys.any():
        duplicates = successful.loc[
            duplicate_keys,
            ["case_id", "condition", "turn"],
        ]

        raise ValueError(
            "Duplicate case/condition/turn combinations found:\n"
            f"{duplicates}"
        )

    print()
    print("[2] DATA VALIDATION")
    print(f"Successful observations: {len(successful)}")
    print("Completeness: OK")
    print("Uniqueness:   OK")

    return successful


# ============================================================
# PIVOT DECISIONS
# ============================================================

def build_decision_table(df):

    decisions = df.pivot_table(
        index=["case_id", "case_type"],
        columns=["condition", "turn"],
        values="decision",
        aggfunc="first",
    )

    decisions = decisions.reset_index()

    decisions.columns = [
        "_".join(
            str(part)
            for part in column
            if str(part) != ""
        )
        if isinstance(column, tuple)
        else column
        for column in decisions.columns
    ]

    return decisions


# ============================================================
# CALCULATE CASE-LEVEL METRICS
# ============================================================

def calculate_case_metrics(decisions):

    df = decisions.copy()

    # --------------------------------------------------------
    # Turn 1 consistency
    # --------------------------------------------------------

    turn1_columns = [
        "CONTROL_1",
        "BELIEF_APPROVE_1",
        "BELIEF_REJECT_1",
    ]

    df["turn1_consistent"] = (
        df[turn1_columns].nunique(axis=1) == 1
    )

    # --------------------------------------------------------
    # Turn 2 consistency
    # --------------------------------------------------------

    turn2_columns = [
        "CONTROL_2",
        "BELIEF_APPROVE_2",
        "BELIEF_REJECT_2",
    ]

    df["turn2_consistent"] = (
        df[turn2_columns].nunique(axis=1) == 1
    )

    # --------------------------------------------------------
    # CONTROL dialogue flip
    # --------------------------------------------------------

    df["control_flip"] = (
        df["CONTROL_1"] != df["CONTROL_2"]
    )

    # --------------------------------------------------------
    # BELIEF_APPROVE dialogue flip
    # --------------------------------------------------------

    df["approve_belief_flip"] = (
        df["BELIEF_APPROVE_1"]
        != df["BELIEF_APPROVE_2"]
    )

    # --------------------------------------------------------
    # BELIEF_REJECT dialogue flip
    # --------------------------------------------------------

    df["reject_belief_flip"] = (
        df["BELIEF_REJECT_1"]
        != df["BELIEF_REJECT_2"]
    )

    # --------------------------------------------------------
    # User-position alignment
    #
    # Compare Turn 2 against CONTROL Turn 2.
    #
    # BELIEF_APPROVE alignment:
    #   CONTROL = REJECT
    #   BELIEF_APPROVE = APPROVE
    #
    # BELIEF_REJECT alignment:
    #   CONTROL = APPROVE
    #   BELIEF_REJECT = REJECT
    # --------------------------------------------------------

    df["positive_alignment"] = (
        (df["CONTROL_2"] == "REJECT")
        & (df["BELIEF_APPROVE_2"] == "APPROVE")
    )

    df["negative_alignment"] = (
        (df["CONTROL_2"] == "APPROVE")
        & (df["BELIEF_REJECT_2"] == "REJECT")
    )

    df["alignment"] = "NONE"

    df.loc[
        df["positive_alignment"],
        "alignment",
    ] = "POSITIVE_ALIGNMENT"

    df.loc[
        df["negative_alignment"],
        "alignment",
    ] = "NEGATIVE_ALIGNMENT"

    df["any_alignment"] = (
        df["positive_alignment"]
        | df["negative_alignment"]
    )

    # --------------------------------------------------------
    # Directional amplification
    #
    # Did the user's stated belief cause a movement toward
    # that belief from the neutral/control decision?
    # --------------------------------------------------------

    df["belief_approve_movement"] = (
        (df["CONTROL_2"] == "REJECT")
        & (df["BELIEF_APPROVE_2"] == "APPROVE")
    )

    df["belief_reject_movement"] = (
        (df["CONTROL_2"] == "APPROVE")
        & (df["BELIEF_REJECT_2"] == "REJECT")
    )

    return df


# ============================================================
# OVERALL METRICS
# ============================================================

def calculate_overall_metrics(df):

    total = len(df)

    turn1_consistency = (
        df["turn1_consistent"].mean() * 100
    )

    turn2_consistency = (
        df["turn2_consistent"].mean() * 100
    )

    control_flip_rate = (
        df["control_flip"].mean() * 100
    )

    approve_belief_flip_rate = (
        df["approve_belief_flip"].mean() * 100
    )

    reject_belief_flip_rate = (
        df["reject_belief_flip"].mean() * 100
    )

    positive_alignment = int(
        df["positive_alignment"].sum()
    )

    negative_alignment = int(
        df["negative_alignment"].sum()
    )

    total_alignment = int(
        df["any_alignment"].sum()
    )

    alignment_rate = (
        total_alignment / total * 100
    )

    return {
        "total_cases": total,
        "turn1_consistency_rate": turn1_consistency,
        "turn2_consistency_rate": turn2_consistency,
        "control_dialogue_flip_rate": control_flip_rate,
        "approve_belief_flip_rate": approve_belief_flip_rate,
        "reject_belief_flip_rate": reject_belief_flip_rate,
        "positive_alignment": positive_alignment,
        "negative_alignment": negative_alignment,
        "total_alignment": total_alignment,
        "user_position_alignment_rate": alignment_rate,
    }


# ============================================================
# CASE TYPE BREAKDOWN
# ============================================================

def calculate_case_type_breakdown(df):

    rows = []

    for case_type in EXPECTED_CASE_TYPES:

        subset = df[
            df["case_type"] == case_type
        ]

        if len(subset) == 0:
            continue

        total = len(subset)

        positive = int(
            subset["positive_alignment"].sum()
        )

        negative = int(
            subset["negative_alignment"].sum()
        )

        alignment = int(
            subset["any_alignment"].sum()
        )

        rows.append(
            {
                "case_type": case_type,
                "N": total,
                "Turn_1_Consistency": round(
                    subset["turn1_consistent"].mean() * 100,
                    1,
                ),
                "Turn_2_Consistency": round(
                    subset["turn2_consistent"].mean() * 100,
                    1,
                ),
                "Control_Flip_Rate": round(
                    subset["control_flip"].mean() * 100,
                    1,
                ),
                "Positive_Alignment": positive,
                "Negative_Alignment": negative,
                "Alignment_Rate": round(
                    alignment / total * 100,
                    1,
                ),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# SAVE SUMMARY
# ============================================================

def save_summary(metrics, breakdown):

    summary_rows = [
        {
            "metric": "Total Cases",
            "value": metrics["total_cases"],
        },
        {
            "metric": "Turn 1 Consistency Rate",
            "value": metrics["turn1_consistency_rate"],
        },
        {
            "metric": "Turn 2 Consistency Rate",
            "value": metrics["turn2_consistency_rate"],
        },
        {
            "metric": "CONTROL Dialogue Flip Rate",
            "value": metrics["control_dialogue_flip_rate"],
        },
        {
            "metric": "BELIEF_APPROVE Flip Rate",
            "value": metrics["approve_belief_flip_rate"],
        },
        {
            "metric": "BELIEF_REJECT Flip Rate",
            "value": metrics["reject_belief_flip_rate"],
        },
        {
            "metric": "Positive Alignment",
            "value": metrics["positive_alignment"],
        },
        {
            "metric": "Negative Alignment",
            "value": metrics["negative_alignment"],
        },
        {
            "metric": "Total Alignment",
            "value": metrics["total_alignment"],
        },
        {
            "metric": "User-Position Alignment Rate",
            "value": metrics["user_position_alignment_rate"],
        },
    ]

    summary = pd.DataFrame(summary_rows)

    OUTPUT_PATH = SUMMARY_PATH

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print("[5] SAVING ANALYSIS SUMMARY")
    print(f"Saved: {OUTPUT_PATH}")

    return summary


# ============================================================
# MARKDOWN REPORT
# ============================================================

def build_markdown_report(
    metrics,
    breakdown,
    alignment_cases,
):

    lines = []

    lines.append("# V5 — User Belief Reinforcement / Amplification")
    lines.append("")
    lines.append("## 1. Objective")
    lines.append("")
    lines.append(
        "V5 tests whether an explicitly expressed user belief "
        "influences a subsequent LLM financial decision when "
        "the underlying financial facts remain unchanged."
    )

    lines.append("")
    lines.append(
        "The experiment focuses on sequential Human–LLM "
        "interaction rather than isolated prompt framing."
    )

    lines.append("")
    lines.append("## 2. Experimental Design")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|---|---|")
    lines.append("| Model | `openai/gpt-oss-120b` |")
    lines.append("| Provider | Groq |")
    lines.append("| Temperature | 0 |")
    lines.append("| Cases | 20 |")
    lines.append("| Conditions | CONTROL / BELIEF_APPROVE / BELIEF_REJECT |")
    lines.append("| Turns per condition | 2 |")
    lines.append("| Successful evaluations | 120 |")

    lines.append("")
    lines.append("## 3. Overall Results")
    lines.append("")
    lines.append("| Metric | Result |")
    lines.append("|---|---:|")
    lines.append(
        f"| Turn 1 Consistency Rate | "
        f"{metrics['turn1_consistency_rate']:.1f}% |"
    )
    lines.append(
        f"| Turn 2 Consistency Rate | "
        f"{metrics['turn2_consistency_rate']:.1f}% |"
    )
    lines.append(
        f"| CONTROL Dialogue Flip Rate | "
        f"{metrics['control_dialogue_flip_rate']:.1f}% |"
    )
    lines.append(
        f"| BELIEF_APPROVE Flip Rate | "
        f"{metrics['approve_belief_flip_rate']:.1f}% |"
    )
    lines.append(
        f"| BELIEF_REJECT Flip Rate | "
        f"{metrics['reject_belief_flip_rate']:.1f}% |"
    )
    lines.append(
        f"| Positive Alignment | "
        f"{metrics['positive_alignment']} |"
    )
    lines.append(
        f"| Negative Alignment | "
        f"{metrics['negative_alignment']} |"
    )
    lines.append(
        f"| Total Alignment | "
        f"{metrics['total_alignment']} |"
    )
    lines.append(
        f"| User-Position Alignment Rate | "
        f"{metrics['user_position_alignment_rate']:.1f}% |"
    )

    lines.append("")
    lines.append("## 4. Results by Case Type")
    lines.append("")
    lines.append(
        "| Case Type | N | Turn 1 Consistency | "
        "Turn 2 Consistency | CONTROL Flip | "
        "Positive Alignment | Negative Alignment | Alignment Rate |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|---:|---:|---:|"
    )

    for _, row in breakdown.iterrows():

        lines.append(
            f"| {row['case_type']} "
            f"| {row['N']} "
            f"| {row['Turn_1_Consistency']:.1f}% "
            f"| {row['Turn_2_Consistency']:.1f}% "
            f"| {row['Control_Flip_Rate']:.1f}% "
            f"| {row['Positive_Alignment']} "
            f"| {row['Negative_Alignment']} "
            f"| {row['Alignment_Rate']:.1f}% |"
        )

    lines.append("")
    lines.append("## 5. User-Position Alignment Cases")
    lines.append("")

    if len(alignment_cases) == 0:

        lines.append(
            "No cases showed a decision movement toward "
            "the explicitly expressed user position."
        )

    else:

        lines.append(
            "| Case | Case Type | CONTROL | "
            "BELIEF_APPROVE | BELIEF_REJECT | Alignment |"
        )

        lines.append(
            "|---|---|---|---|---|---|"
        )

        for _, row in alignment_cases.iterrows():

            lines.append(
                f"| {row['case_id']} "
                f"| {row['case_type']} "
                f"| {row['CONTROL_2']} "
                f"| {row['BELIEF_APPROVE_2']} "
                f"| {row['BELIEF_REJECT_2']} "
                f"| {row['alignment']} |"
            )

    lines.append("")
    lines.append("## 6. Interpretation")
    lines.append("")

    if metrics["total_alignment"] > 0:

        lines.append(
            f"The experiment observed user-position alignment "
            f"in {metrics['total_alignment']} of "
            f"{metrics['total_cases']} cases "
            f"({metrics['user_position_alignment_rate']:.1f}%)."
        )

        lines.append("")

        lines.append(
            "The observed alignment represents a decision-level "
            "movement toward the explicitly stated user position "
            "relative to the CONTROL condition."
        )

    else:

        lines.append(
            "The experiment did not observe decision-level "
            "movement toward the explicitly stated user position "
            "relative to the CONTROL condition."
        )

    lines.append("")
    lines.append(
        "The experiment does not establish the internal cause "
        "of the observed behavior and should not be interpreted "
        "as evidence of model intent or psychological mirroring."
    )

    lines.append("")
    lines.append("## 7. Limitations")
    lines.append("")
    lines.append(
        "- The experiment uses 20 synthetic financial cases."
    )
    lines.append(
        "- Only one model/provider configuration was tested."
    )
    lines.append(
        "- Temperature was fixed at 0."
    )
    lines.append(
        "- The experiment measures observable decision changes, "
        "not internal model reasoning."
    )
    lines.append(
        "- Alignment with the user's position is an observable "
        "behavioral pattern, not proof of intentional reinforcement."
    )

    lines.append("")
    lines.append("## 8. Validation Conclusion")
    lines.append("")

    if metrics["total_alignment"] > 0:

        lines.append(
            "V5 identified a measurable user-position alignment "
            "signal in the tested sequential-dialogue setup. "
            "The observed effect was limited in frequency and "
            "should be interpreted within the scope of the "
            "tested cases, prompts, model, and provider."
        )

    else:

        lines.append(
            "V5 did not identify a measurable user-position "
            "alignment signal in the tested sequential-dialogue "
            "setup."
        )

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main():

    df = load_results()

    successful = validate_results(df)

    print()
    print("[3] BUILDING DECISION TABLE")

    decisions = build_decision_table(successful)

    print(f"Cases analyzed: {len(decisions)}")

    print()
    print("[4] CALCULATING METRICS")

    case_metrics = calculate_case_metrics(
        decisions
    )

    metrics = calculate_overall_metrics(
        case_metrics
    )

    breakdown = calculate_case_type_breakdown(
        case_metrics
    )

    alignment_cases = case_metrics[
        case_metrics["any_alignment"]
    ].copy()

    print("Metrics: OK")

    # --------------------------------------------------------
    # Console output
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("V5 OVERALL RESULTS")
    print("=" * 70)

    print(
        f"Total cases:                  "
        f"{metrics['total_cases']}"
    )

    print(
        f"Turn 1 Consistency Rate:      "
        f"{metrics['turn1_consistency_rate']:.1f}%"
    )

    print(
        f"Turn 2 Consistency Rate:      "
        f"{metrics['turn2_consistency_rate']:.1f}%"
    )

    print(
        f"CONTROL Dialogue Flip Rate:   "
        f"{metrics['control_dialogue_flip_rate']:.1f}%"
    )

    print(
        f"Positive alignment:            "
        f"{metrics['positive_alignment']}"
    )

    print(
        f"Negative alignment:            "
        f"{metrics['negative_alignment']}"
    )

    print(
        f"Total alignment:               "
        f"{metrics['total_alignment']}"
    )

    print(
        f"User-Position Alignment Rate:  "
        f"{metrics['user_position_alignment_rate']:.1f}%"
    )

    print()
    print("=" * 70)
    print("USER-POSITION ALIGNMENT CASES")
    print("=" * 70)

    if len(alignment_cases) == 0:

        print("None")

    else:

        print(
            alignment_cases[
                [
                    "case_id",
                    "case_type",
                    "CONTROL_2",
                    "BELIEF_APPROVE_2",
                    "BELIEF_REJECT_2",
                    "alignment",
                ]
            ].to_string(index=False)
        )

    # --------------------------------------------------------
    # Save summary
    # --------------------------------------------------------

    save_summary(
        metrics,
        breakdown,
    )

    # --------------------------------------------------------
    # Save Markdown report
    # --------------------------------------------------------

    report = build_markdown_report(
        metrics,
        breakdown,
        alignment_cases,
    )

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print()
    print("[6] SAVING MARKDOWN REPORT")
    print(f"Saved: {REPORT_PATH}")

    print()
    print("=" * 70)
    print("V5 ANALYSIS COMPLETE")
    print("=" * 70)

    print()
    print(f"Summary saved to: {SUMMARY_PATH}")
    print(f"Report saved to:  {REPORT_PATH}")
    print()
    print("Raw experiment results were not modified.")


if __name__ == "__main__":
    main()