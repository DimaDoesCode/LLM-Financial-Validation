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
RANDOM_STATE = 42

DATA_PATH = Path("data/cases.csv")
OUTPUT_PATH = Path("reports/v1_decision_correctness.csv")


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


def build_case_prompt(row):
    return f"""
Evaluate the following financial application.

Income: {row["income"]}
Debt-to-income ratio: {row["debt_to_income"]}
Employment years: {row["employment_years"]}
Credit history years: {row["credit_history_years"]}
Previous defaults: {row["previous_defaults"]}
Requested amount: {row["requested_amount"]}

Provide your decision and brief rationale.
""".strip()


# ============================================================
# LLM CALL
# ============================================================

def evaluate_case(client, row):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_case_prompt(row)},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw_output = response.choices[0].message.content.strip()

    result = json.loads(raw_output)

    decision = result.get("decision")
    rationale = result.get("rationale")

    if decision not in {"APPROVE", "REJECT"}:
        raise ValueError(f"Invalid decision: {decision}")

    return decision, rationale, raw_output


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("LLM FINANCIAL VALIDATION — V1 DECISION CORRECTNESS")
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
        "case_type",
        "reference_decision",
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
    print()

    # --------------------------------------------------------
    # 3. EVALUATION
    # --------------------------------------------------------

    print("[3] EVALUATING CASES")
    print()

    results = []

    for i, row in df.iterrows():

        print(f"Case {i + 1:03d}/{len(df)}: {row['case_id']}", end=" ... ")

        try:
            decision, rationale, raw_output = evaluate_case(client, row)

            print(decision)

            results.append({
                "case_id": row["case_id"],
                "case_type": row["case_type"],
                "reference_decision": row["reference_decision"],
                "llm_decision": decision,
                "rationale": rationale,
                "raw_output": raw_output,
                "error": None,
            })

        except Exception as e:

            print(f"ERROR: {e}")

            results.append({
                "case_id": row["case_id"],
                "case_type": row["case_type"],
                "reference_decision": row["reference_decision"],
                "llm_decision": None,
                "rationale": None,
                "raw_output": None,
                "error": str(e),
            })

        # Small pause to avoid unnecessary burst traffic
        time.sleep(0.1)

    results_df = pd.DataFrame(results)

    # --------------------------------------------------------
    # 4. METRICS
    # --------------------------------------------------------

    print()
    print("[4] VALIDATION RESULTS")
    print()

    valid = results_df["llm_decision"].notna()

    evaluated = results_df[valid]

    if len(evaluated) == 0:
        raise RuntimeError("No valid LLM decisions were produced.")

    accuracy = (
        evaluated["llm_decision"]
        == evaluated["reference_decision"]
    ).mean()

    false_approval = (
        (evaluated["llm_decision"] == "APPROVE")
        & (evaluated["reference_decision"] == "REJECT")
    ).sum()

    false_rejection = (
        (evaluated["llm_decision"] == "REJECT")
        & (evaluated["reference_decision"] == "APPROVE")
    ).sum()

    reject_count = (
        evaluated["reference_decision"] == "REJECT"
    ).sum()

    approve_count = (
        evaluated["reference_decision"] == "APPROVE"
    ).sum()

    false_approval_rate = (
        false_approval / reject_count
        if reject_count > 0 else 0
    )

    false_rejection_rate = (
        false_rejection / approve_count
        if approve_count > 0 else 0
    )

    print(f"Evaluated cases:       {len(evaluated)}")
    print(f"Errors:                {len(results_df) - len(evaluated)}")
    print()
    print(f"Accuracy:              {accuracy:.4f}")
    print(f"False Approval Rate:   {false_approval_rate:.4f}")
    print(f"False Rejection Rate:  {false_rejection_rate:.4f}")

    print()
    print("LLM DECISIONS:")
    print(evaluated["llm_decision"].value_counts())

    print()
    print("ACCURACY BY CASE TYPE:")

    for case_type, group in evaluated.groupby("case_type"):

        group_accuracy = (
            group["llm_decision"]
            == group["reference_decision"]
        ).mean()

        print(f"  {case_type:15s}: {group_accuracy:.4f}")

    # --------------------------------------------------------
    # 5. SAVE RESULTS
    # --------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(
        OUTPUT_PATH,
        index=False
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