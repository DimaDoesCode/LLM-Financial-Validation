"""
LLM Financial Validation — V5 Case Selection

Selects a compact, reproducible V5 test sample from the existing
validation dataset.

Sampling strategy:
- 20 cases total
- 5 cases per case type
- 2 risk-informed cases where possible
- 3 random cases
- previous instability from V2/V3/V4 is used as a priority signal
- fixed random seed for reproducibility

No LLM/API calls are made by this script.
"""

from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = Path("data/cases.csv")

V3_PATH = Path("reports/v3_framing_sensitivity.csv")
V4_PATH = Path("reports/v4_user_position_mirroring.csv")

OUTPUT_PATH = Path("data/v5_cases.csv")

RANDOM_STATE = 42

CASES_PER_TYPE = 5
PRIORITY_PER_TYPE = 2

CASE_TYPES = [
    "CLEAR_APPROVE",
    "CLEAR_REJECT",
    "BORDERLINE",
    "CONFLICTING",
]


# ============================================================
# HELPERS
# ============================================================

def check_columns(df, required, name):
    missing = set(required) - set(df.columns)

    if missing:
        raise ValueError(
            f"{name} is missing required columns: {sorted(missing)}"
        )


def add_v3_instability(df, v3):
    """
    Add V3 instability flag.

    A case is considered V3-unstable if the three framing
    decisions are not identical.
    """

    v3_required = {
        "case_id",
        "decision_neutral",
        "decision_positive",
        "decision_negative",
    }

    check_columns(v3, v3_required, "V3 results")

    v3 = v3.copy()

    v3["v3_flip"] = (
        v3[
            [
                "decision_neutral",
                "decision_positive",
                "decision_negative",
            ]
        ]
        .nunique(axis=1)
        > 1
    )

    return df.merge(
        v3[["case_id", "v3_flip"]],
        on="case_id",
        how="left",
    )


def add_v4_instability(df, v4):
    """
    Add V4 instability flag.

    A case is considered V4-unstable if the three user-position
    conditions produce different decisions.
    """

    v4_required = {
        "case_id",
        "decision_neutral",
        "decision_user_positive",
        "decision_user_negative",
    }

    check_columns(v4, v4_required, "V4 results")

    v4 = v4.copy()

    v4["v4_flip"] = (
        v4[
            [
                "decision_neutral",
                "decision_user_positive",
                "decision_user_negative",
            ]
        ]
        .nunique(axis=1)
        > 1
    )

    return df.merge(
        v4[["case_id", "v4_flip"]],
        on="case_id",
        how="left",
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("LLM FINANCIAL VALIDATION — V5 CASE SELECTION")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    print()
    print("[1] LOADING DATA")

    cases = pd.read_csv(DATA_PATH)
    v3 = pd.read_csv(V3_PATH)
    v4 = pd.read_csv(V4_PATH)

    print(f"Cases shape: {cases.shape}")
    print(f"V3 results:  {v3.shape}")
    print(f"V4 results:  {v4.shape}")

    check_columns(
        cases,
        {"case_id", "case_type"},
        "cases.csv",
    )

    # --------------------------------------------------------
    # ADD INSTABILITY SIGNALS
    # --------------------------------------------------------

    print()
    print("[2] BUILDING RISK SIGNALS")

    df = cases.copy()

    df = add_v3_instability(df, v3)
    df = add_v4_instability(df, v4)

    df["v3_flip"] = df["v3_flip"].fillna(False)
    df["v4_flip"] = df["v4_flip"].fillna(False)

    # Combined instability signal.
    df["instability_score"] = (
        df["v3_flip"].astype(int)
        + df["v4_flip"].astype(int)
    )

    print(
        f"V3 unstable cases: "
        f"{df['v3_flip'].sum()}"
    )

    print(
        f"V4 unstable cases: "
        f"{df['v4_flip'].sum()}"
    )

    # --------------------------------------------------------
    # VALIDATE CASE TYPES
    # --------------------------------------------------------

    print()
    print("[3] CASE TYPE DISTRIBUTION")

    print(
        df["case_type"]
        .value_counts()
        .reindex(CASE_TYPES)
        .fillna(0)
        .astype(int)
        .to_string()
    )

    for case_type in CASE_TYPES:

        count = (df["case_type"] == case_type).sum()

        if count < CASES_PER_TYPE:
            raise ValueError(
                f"Not enough cases for {case_type}: "
                f"{count} available, "
                f"{CASES_PER_TYPE} required."
            )

    # --------------------------------------------------------
    # SELECT CASES
    # --------------------------------------------------------

    print()
    print("[4] SELECTING V5 SAMPLE")

    selected_parts = []

    for case_type in CASE_TYPES:

        group = df[
            df["case_type"] == case_type
        ].copy()

        # ----------------------------------------------------
        # Priority cases
        # ----------------------------------------------------

        priority = group[
            group["instability_score"] > 0
        ].copy()

        priority = priority.sort_values(
            by=[
                "instability_score",
                "case_id",
            ],
            ascending=[False, True],
        )

        priority_count = min(
            PRIORITY_PER_TYPE,
            len(priority),
        )

        selected_priority = priority.head(
            priority_count
        ).copy()

        # ----------------------------------------------------
        # Random remainder
        # ----------------------------------------------------

        selected_ids = set(
            selected_priority["case_id"]
        )

        remaining = group[
            ~group["case_id"].isin(selected_ids)
        ]

        random_count = (
            CASES_PER_TYPE
            - len(selected_priority)
        )

        selected_random = remaining.sample(
            n=random_count,
            random_state=RANDOM_STATE,
        ).copy()

        # ----------------------------------------------------
        # Combine
        # ----------------------------------------------------

        selected = pd.concat(
            [
                selected_priority,
                selected_random,
            ],
            ignore_index=True,
        )

        selected["v5_priority"] = "RANDOM"

        selected.loc[
            selected["case_id"].isin(
                selected_priority["case_id"]
            ),
            "v5_priority",
        ] = "HIGH"

        selected_parts.append(selected)

        print()
        print(f"{case_type}:")
        print(
            selected[
                [
                    "case_id",
                    "v3_flip",
                    "v4_flip",
                    "instability_score",
                    "v5_priority",
                ]
            ]
            .sort_values(
                ["v5_priority", "case_id"],
                ascending=[True, True],
            )
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # FINAL DATASET
    # --------------------------------------------------------

    selected_df = pd.concat(
        selected_parts,
        ignore_index=True,
    )

    selected_df = selected_df.sort_values(
        ["case_type", "case_id"]
    ).reset_index(drop=True)

    # Keep only the information needed by V5.
    output = selected_df[
        [
            "case_id",
            "case_type",
            "v5_priority",
            "v3_flip",
            "v4_flip",
            "instability_score",
        ]
    ].copy()

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    print()
    print("[5] SAVING V5 CASE LIST")

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"Saved: {OUTPUT_PATH}")

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("V5 SAMPLE SUMMARY")
    print("=" * 70)

    print(f"Total selected: {len(output)}")
    print()

    print(
        output["case_type"]
        .value_counts()
        .reindex(CASE_TYPES)
        .to_string()
    )

    print()
    print(
        "Priority cases: "
        f"{(output['v5_priority'] == 'HIGH').sum()}"
    )

    print(
        "Random cases:   "
        f"{(output['v5_priority'] == 'RANDOM').sum()}"
    )

    print()
    print("V5 CASE SELECTION COMPLETE")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()