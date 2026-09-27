# V1 Decision Correctness

## Objective

Evaluate whether the LLM produces financial approval/rejection decisions consistent with the deterministic reference decisions on a controlled synthetic dataset.

**Model:** `openai/gpt-oss-120b`
**Provider:** Groq
**Dataset:** 100 synthetic financial cases
**Temperature:** 0
**Evaluation:** single-turn, fact-only interaction

The validation does not provide the LLM with `reference_decision`, `risk_score`, `risk_band`, or `case_type`.

---

## Results

| Metric               |     Result |
| -------------------- | ---------: |
| Cases evaluated      |        100 |
| Errors               |          0 |
| Decision Accuracy    |  **86.0%** |
| False Approval Rate  | **15.38%** |
| False Rejection Rate | **13.11%** |

### Accuracy by Case Type

| Case Type     |   Accuracy |
| ------------- | ---------: |
| CLEAR_APPROVE | **100.0%** |
| CLEAR_REJECT  |  **96.7%** |
| BORDERLINE    |  **85.0%** |
| CONFLICTING   |  **50.0%** |

---

## Error Analysis

The model produced 14 decisions different from the deterministic reference decision.

Errors were concentrated in:

* `CONFLICTING`: 10 / 20 cases
* `BORDERLINE`: 3 / 20 cases
* `CLEAR_REJECT`: 1 / 30 cases
* `CLEAR_APPROVE`: 0 / 30 cases

The disagreements in conflicting cases were systematic rather than random.

The model tended to give greater weight to individual dominant factors, particularly:

* high debt-to-income ratio;
* low debt-to-income ratio;
* previous defaults;
* employment stability;
* credit history length.

For example, high DTI frequently led to rejection despite strong positive factors, while strong repayment-capacity indicators could lead to approval despite a previous default.

This indicates that the LLM applies its own interpretation of competing financial factors rather than reproducing the deterministic reference rule exactly.

---

## Validation Finding

**Finding V1-01 — Decision divergence in ambiguous cases**

The LLM reproduced the reference decision well for clear cases but showed substantially lower agreement for borderline and conflicting cases.

This demonstrates that overall accuracy alone is insufficient for evaluating an LLM-based financial decision system. Performance should also be examined across case types and under conditions where financial factors conflict.

The observed disagreement should not be interpreted as proof that the LLM's decisions are objectively incorrect: the reference decision is a deterministic validation rule created for this synthetic test.

---

## Conclusion

V1 establishes a baseline for subsequent validation.

The system demonstrates high agreement with the reference decisions on clear cases, while conflicting and borderline cases represent the main source of divergence.

**V1 is considered complete.**

The next validation dimension is **V2 — Consistency & Stability**.
