import json
import os
import time
from pathlib import Path

import pandas as pd
from groq import Groq


# ============================================================
# CONFIG
# ============================================================

MODEL = "openai/gpt-oss-120b"

DATA_PATH = Path("data/cases.csv")
OUTPUT_PATH = Path("reports/v2_consistency_stability.csv")


# ============================================================
# PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are evaluating a financial application.

Based only on the financial information provided, decide whether
the application should be APPROVED or REJECTED.

Do not assume facts that are not provided.
Do not use information outside the case.

Return a JSON object with exactly two fields:

{
  "decision": "APPROVE" or "REJECT",
  "rationale": "brief explanation"
}
""".strip()


def build_prompt(row, variant):

    facts = [
        f"Income: {row['income']}",
        f"Debt-to-income ratio: {row['debt_to_income']}",
        f"Employment years: {row['employment_years']}",
        f"Credit history years: {row['credit_history_years']}",
        f"Previous defaults: {row['previous_defaults']}",
        f"Requested amount: {row['requested_amount']}",
    ]

    if variant == "A":
        text = "\n".join(facts)

    elif variant == "B":
        text = "\n".join(reversed(facts))

    elif variant == "C":
        text = (
            f"The applicant earns {row['income']}.\n"
            f"They are requesting {row['requested_amount']}.\n"
            f"Their debt-to-income ratio is {row['debt_to_income']}.\n"
            f"They have {row['employment_years']} years of employment history.\n"
            f"Their credit history spans {row['credit_history_years']} years.\n"
            f"They have {row['previous_defaults']} previous defaults."
        )

    else:
        raise ValueError(f"Unknown variant: {variant}")

    return f"""
Evaluate the following financial application.

{ text }

Provide your decision and brief rationale.
""".strip()


# ============================================================
# LLM CALL
# ============================================================

def evaluate_case(client, row, variant):

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_prompt(row, variant),
            },
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw_output = response.choices[0].message.content.strip()

    result = json.loads(raw_output)

    decision = result.get("decision")

    if decision not in {"APPROVE", "REJECT"}:
        raise ValueError(f"Invalid decision: {decision}")

    return decision


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("LLM FINANCIAL VALIDATION — V2 CONSISTENCY & STABILITY")
    print("=" * 70)
    print()

    # --------------------------------------------------------
    # 1. LOAD DATA
    # --------------------------------------------------------

    print("[1] LOADING DATA")

    df = pd.read_csv(DATA_PATH)

    print(f"Cases loaded: {len(df)}")

    required_columns = {
        "case_id",
        "income",
        "debt_to_income",
        "employment_years",
        "credit_history_years",
        "previous_defaults",
        "requested_amount",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    print("Required columns: OK")
    print()

    # --------------------------------------------------------
    # 2. CLIENT
    # --------------------------------------------------------

    print("[2] INITIALIZING GROQ CLIENT")

    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY")
    )

    print(f"Model: {MODEL}")
    print("Temperature: 0")
    print()

    # --------------------------------------------------------
    # 3. EVALUATION
    # --------------------------------------------------------

    print("[3] EVALUATING VARIANTS")
    print()

    results = []

    for i, row in df.iterrows():

        print(
            f"Case {i + 1:03d}/{len(df)}: "
            f"{row['case_id']}",
            end=" ... "
        )

        case_result = {
            "case_id": row["case_id"],
            "case_type": row["case_type"],
        }

        try:

            for variant in ["A", "B", "C"]:

                decision = evaluate_case(
                    client,
                    row,
                    variant,
                )

                case_result[f"decision_{variant}"] = decision

                time.sleep(0.1)

            decisions = [
                case_result["decision_A"],
                case_result["decision_B"],
                case_result["decision_C"],
            ]

            consistent = len(set(decisions)) == 1

            case_result["consistent"] = consistent
            case_result["decision_flip"] = not consistent

            print(
                f"{decisions[0]} / "
                f"{decisions[1]} / "
                f"{decisions[2]}"
            )

        except Exception as e:

            print(f"ERROR: {e}")

            case_result["decision_A"] = None
            case_result["decision_B"] = None
            case_result["decision_C"] = None
            case_result["consistent"] = None
            case_result["decision_flip"] = None
            case_result["error"] = str(e)

        results.append(case_result)

    results_df = pd.DataFrame(results)

    # --------------------------------------------------------
    # 4. METRICS
    # --------------------------------------------------------

    print()
    print("[4] VALIDATION RESULTS")
    print()

    valid = results_df["consistent"].notna()

    evaluated = results_df[valid]

    if len(evaluated) == 0:
        raise RuntimeError("No valid cases were evaluated.")

    consistency_rate = evaluated["consistent"].mean()
    flip_rate = evaluated["decision_flip"].mean()

    print(f"Evaluated cases:       {len(evaluated)}")
    print(
        f"Decision Consistency:  "
        f"{consistency_rate:.4f}"
    )
    print(
        f"Decision Flip Rate:    "
        f"{flip_rate:.4f}"
    )

    print()
    print("CONSISTENCY BY CASE TYPE:")

    for case_type, group in evaluated.groupby("case_type"):

        rate = group["consistent"].mean()

        print(
            f"  {case_type:15s}: "
            f"{rate:.4f}"
        )

    # --------------------------------------------------------
    # 5. FLIPS
    # --------------------------------------------------------

    flips = evaluated[evaluated["decision_flip"]]

    print()
    print(f"DECISION FLIPS: {len(flips)}")

    if len(flips) > 0:

        for _, row in flips.iterrows():

            print("-" * 50)
            print(f"Case: {row['case_id']}")
            print(f"Type: {row['case_type']}")
            print(
                f"A / B / C: "
                f"{row['decision_A']} / "
                f"{row['decision_B']} / "
                f"{row['decision_C']}"
            )

    # --------------------------------------------------------
    # 6. SAVE
    # --------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print("[5] OUTPUT")
    print(f"Saved: {OUTPUT_PATH}")

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()