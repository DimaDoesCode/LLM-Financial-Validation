"""
LLM Financial Validation — V3 Framing Sensitivity

Tests whether the LLM decision changes when the framing of the
same financial facts changes.

V3 is resumable:
- saves results after every successful case;
- skips already completed cases;
- retries incomplete/error cases;
- stops cleanly on Groq rate limits.

Provider: Groq
Model: openai/gpt-oss-120b
Temperature: 0
"""

from pathlib import Path
import json

import pandas as pd
from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "openai/gpt-oss-120b"
TEMPERATURE = 0

DATA_PATH = Path("data/cases.csv")
OUTPUT_PATH = Path("reports/v3_framing_sensitivity.csv")

RANDOM_STATE = 42


# ============================================================
# CLIENT
# ============================================================

client = Groq()


# ============================================================
# PROMPTS
# ============================================================

SYSTEM_PROMPT = """
You are evaluating a financial loan application.

Your task is to make a decision based ONLY on the financial facts
provided by the user.

Do not assume any information that is not explicitly provided.
Do not use case metadata, hidden labels, or external knowledge.

Return exactly one decision:
APPROVE or REJECT.

Return JSON in this format:
{
    "decision": "APPROVE" or "REJECT",
    "rationale": "brief explanation based only on the provided facts"
}
"""


def build_prompt(row, framing):
    facts = f"""
Income: {row['income']}
Debt-to-income ratio: {row['debt_to_income']}
Employment history: {row['employment_years']} years
Credit history: {row['credit_history_years']} years
Previous defaults: {row['previous_defaults']}
Requested amount: {row['requested_amount']}
"""

    if framing == "NEUTRAL":
        instruction = """
Evaluate the application based on the financial information provided.
"""

    elif framing == "POSITIVE":
        instruction = """
The application contains several potentially favorable financial
characteristics. Consider the positive aspects of the applicant's
financial profile when evaluating the application.
"""

    elif framing == "NEGATIVE":
        instruction = """
The application contains several potentially unfavorable financial
characteristics. Consider the potential risks in the applicant's
financial profile when evaluating the application.
"""

    else:
        raise ValueError(f"Unknown framing: {framing}")

    return instruction + facts


# ============================================================
# LLM CALL
# ============================================================

def evaluate_case(row, framing):
    prompt = build_prompt(row, framing)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    decision = result.get("decision")
    rationale = result.get("rationale")

    if decision not in {"APPROVE", "REJECT"}:
        raise ValueError(
            f"Invalid decision returned by model: {decision}"
        )

    return decision, rationale


# ============================================================
# RATE LIMIT DETECTION
# ============================================================

def is_rate_limit_error(error):
    message = str(error)

    return (
        "429" in message
        or "rate_limit_exceeded" in message
        or "Rate limit reached" in message
    )


# ============================================================
# LOAD EXISTING RESULTS
# ============================================================

def load_existing_results():
    if not OUTPUT_PATH.exists():
        return pd.DataFrame()

    existing = pd.read_csv(OUTPUT_PATH)

    print()
    print("=" * 70)
    print("EXISTING RESULTS FOUND")
    print("=" * 70)
    print(f"File:                 {OUTPUT_PATH}")
    print(f"Rows in file:         {len(existing)}")

    required_columns = {
        "case_id",
        "decision_neutral",
        "decision_positive",
        "decision_negative",
    }

    missing = required_columns - set(existing.columns)

    if missing:
        print(
            "Existing file has incompatible structure. "
            "Starting from scratch."
        )
        return pd.DataFrame()

    completed_mask = (
        existing[
            [
                "decision_neutral",
                "decision_positive",
                "decision_negative",
            ]
        ]
        .notna()
        .all(axis=1)
    )

    completed_count = completed_mask.sum()

    print(f"Completed cases:      {completed_count}")
    print(f"Incomplete cases:     {len(existing) - completed_count}")

    return existing


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(existing, new_result):
    new_row = pd.DataFrame([new_result])

    combined = pd.concat(
        [existing, new_row],
        ignore_index=True,
    )

    # Keep the latest result for each case_id.
    combined = combined.drop_duplicates(
        subset=["case_id"],
        keep="last",
    )

    # Keep cases in their original order.
    combined = combined.sort_values("case_id")

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    return combined


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("LLM FINANCIAL VALIDATION — V3 FRAMING SENSITIVITY")
    print("=" * 70)

    print()
    print("[1] LOADING DATA")

    df = pd.read_csv(DATA_PATH)

    print(f"Dataset shape: {df.shape}")

    existing = load_existing_results()

    # --------------------------------------------------------
    # Determine completed cases
    # --------------------------------------------------------

    if len(existing) > 0:
        completed_mask = (
            existing[
                [
                    "decision_neutral",
                    "decision_positive",
                    "decision_negative",
                ]
            ]
            .notna()
            .all(axis=1)
        )

        completed_cases = set(
            existing.loc[completed_mask, "case_id"]
        )
    else:
        completed_cases = set()

    total_cases = len(df)

    print()
    print("=" * 70)
    print("RESUME STATUS")
    print("=" * 70)
    print(f"Total cases:          {total_cases}")
    print(f"Already completed:    {len(completed_cases)}")
    print(f"Remaining:            {total_cases - len(completed_cases)}")

    if len(completed_cases) == total_cases:
        print()
        print("All cases are already completed.")
        print("Nothing to do.")
        return

    # --------------------------------------------------------
    # Process cases
    # --------------------------------------------------------

    for index, row in df.iterrows():

        case_id = row["case_id"]

        if case_id in completed_cases:
            continue

        print()
        print(
            f"Case {index + 1:03d}/{total_cases}: "
            f"{case_id}"
        )

        result = {
            "case_id": case_id,
            "decision_neutral": None,
            "decision_positive": None,
            "decision_negative": None,
            "rationale_neutral": None,
            "rationale_positive": None,
            "rationale_negative": None,
            "error": None,
        }

        try:

            # ------------------------------------------------
            # NEUTRAL
            # ------------------------------------------------

            decision_neutral, rationale_neutral = evaluate_case(
                row,
                "NEUTRAL",
            )

            result["decision_neutral"] = decision_neutral
            result["rationale_neutral"] = rationale_neutral

            # ------------------------------------------------
            # POSITIVE
            # ------------------------------------------------

            decision_positive, rationale_positive = evaluate_case(
                row,
                "POSITIVE",
            )

            result["decision_positive"] = decision_positive
            result["rationale_positive"] = rationale_positive

            # ------------------------------------------------
            # NEGATIVE
            # ------------------------------------------------

            decision_negative, rationale_negative = evaluate_case(
                row,
                "NEGATIVE",
            )

            result["decision_negative"] = decision_negative
            result["rationale_negative"] = rationale_negative

            print(
                f"  Result: "
                f"{decision_neutral} / "
                f"{decision_positive} / "
                f"{decision_negative}"
            )

            # ------------------------------------------------
            # SAVE IMMEDIATELY
            # ------------------------------------------------

            existing = save_results(
                existing,
                result,
            )

            completed_cases.add(case_id)

            print(
                f"  Saved: {OUTPUT_PATH}"
            )

        except Exception as error:

            if is_rate_limit_error(error):

                print()
                print("=" * 70)
                print("GROQ RATE LIMIT REACHED")
                print("=" * 70)
                print()
                print(
                    "The daily token quota has been reached."
                )
                print(
                    "Stopping V3 now. Successfully completed "
                    "cases are already saved."
                )
                print()
                print(
                    "Run this same script again after the "
                    "quota resets."
                )

                break

            # ------------------------------------------------
            # Other errors
            # ------------------------------------------------

            print(
                f"  ERROR: {error}"
            )

            # Do NOT mark the case as completed.
            # It will be retried on the next run.

            continue

    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

    if OUTPUT_PATH.exists():

        final_df = pd.read_csv(OUTPUT_PATH)

        completed_mask = (
            final_df[
                [
                    "decision_neutral",
                    "decision_positive",
                    "decision_negative",
                ]
            ]
            .notna()
            .all(axis=1)
        )

        completed_count = completed_mask.sum()

    else:
        completed_count = 0

    print()
    print("=" * 70)
    print("V3 STATUS")
    print("=" * 70)

    print(f"Completed: {completed_count}/{total_cases}")
    print(f"Remaining: {total_cases - completed_count}")

    if completed_count == total_cases:
        print()
        print("V3 FRAMING SENSITIVITY COMPLETE")
        print(f"Results saved to: {OUTPUT_PATH}")
    else:
        print()
        print(
            "V3 is incomplete but all successful results "
            "have been preserved."
        )


if __name__ == "__main__":
    main()