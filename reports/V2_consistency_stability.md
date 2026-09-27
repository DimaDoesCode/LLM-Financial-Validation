# V2 Consistency & Stability

## Objective

Evaluate whether the LLM produces consistent financial decisions when the same underlying financial facts are presented in equivalent formulations.

**Model:** `openai/gpt-oss-120b`
**Provider:** Groq
**Dataset:** 100 synthetic financial cases
**Variants per case:** 3
**Temperature:** 0

The validation changes only the presentation of the same financial information. No reference decision is used in the consistency metric.

---

## Results

| Metric                    |    Result |
| ------------------------- | --------: |
| Cases evaluated           |       100 |
| Decision Consistency Rate | **90.0%** |
| Decision Flip Rate        | **10.0%** |

### Consistency by Case Type

| Case Type     | Consistency |
| ------------- | ----------: |
| CLEAR_APPROVE |  **100.0%** |
| CLEAR_REJECT  |   **96.7%** |
| BORDERLINE    |   **70.0%** |
| CONFLICTING   |   **85.0%** |

---

## Decision Flips

10 of 100 cases produced different decisions across equivalent formulations.

The flips were concentrated in ambiguous cases:

* `BORDERLINE`: 6 cases
* `CONFLICTING`: 3 cases
* `CLEAR_REJECT`: 1 case
* `CLEAR_APPROVE`: 0 cases

Examples include:

`CASE_0079`
`APPROVE → REJECT → APPROVE`

`CASE_0075`
`REJECT → APPROVE → APPROVE`

`CASE_0091`
`APPROVE → REJECT → REJECT`

---

## Validation Finding

**Finding V2-01 — Decision instability under equivalent presentation**

The LLM was highly consistent on clear cases but showed materially lower consistency on borderline and conflicting cases.

Some cases produced different decisions even though the underlying financial facts remained unchanged and `temperature=0`.

This indicates that decision stability can depend on the presentation of information, particularly when the financial factors are ambiguous or competing.

---

## Conclusion

V2 establishes a measurable baseline for consistency.

The observed 10% decision flip rate provides evidence that equivalent presentation of the same financial information can produce different decisions in a subset of cases.

**V2 is considered complete.**

The next validation dimension is **V3 — Framing Sensitivity**.
