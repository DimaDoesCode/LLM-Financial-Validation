import pandas as pd

df = pd.read_csv("reports/v1_decision_correctness.csv")

errors = df[
    df["llm_decision"] != df["reference_decision"]
]

print("=" * 70)
print("V1 DECISION CORRECTNESS — ERROR ANALYSIS")
print("=" * 70)

print(f"\nTotal errors: {len(errors)}")

print("\nERRORS BY CASE TYPE:")
print(errors["case_type"].value_counts())

print("\nDETAILED ERRORS:")
for _, row in errors.iterrows():
    print("-" * 70)
    print(f"Case:       {row['case_id']}")
    print(f"Type:       {row['case_type']}")
    print(f"Reference:  {row['reference_decision']}")
    print(f"LLM:        {row['llm_decision']}")
    print(f"Rationale:  {row['rationale']}")