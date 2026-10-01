# LLM Financial Decision Validation

A compact validation framework for an **LLM-based financial decision system**.

The project evaluates not only whether an LLM makes correct financial decisions, but also how those decisions behave under changes in formulation, framing, user interaction, conversational context, and explanation requirements.

The core validation object is:

**Human ↔ LLM ↔ Decision**

---

## Objective

The goal is to demonstrate a practical approach to validating an LLM used in a financial decision-making context.

Instead of treating the LLM as a simple text-generation component, the framework evaluates observable risks at several levels:

* decision correctness;
* consistency and stability;
* framing sensitivity;
* user-position influence;
* belief reinforcement in dialogue;
* decision traceability.

The project is deliberately kept compact. The objective is **reproducible validation**, not an exhaustive catalogue of LLM risks.

---

## Model and Environment

| Parameter       | Value                         |
| --------------- | ----------------------------- |
| Model           | `openai/gpt-oss-120b`         |
| Provider        | Groq                          |
| Temperature     | `0`                           |
| Primary dataset | 100 synthetic financial cases |
| Decision space  | `APPROVE / REJECT`            |

The experiments use synthetic financial data and are intended for validation methodology development rather than real-world credit decisions.

---

## Validation Framework

Six validation stages were implemented.

| Stage  | Validation              | Main question                                                      |                         Result |
| ------ | ----------------------- | ------------------------------------------------------------------ | -----------------------------: |
| **V1** | Decision Correctness    | Does the LLM make the correct decision?                            |             **86.0% accuracy** |
| **V2** | Consistency & Stability | Does the decision remain stable under equivalent formulations?     |          **90.0% consistency** |
| **V3** | Framing Sensitivity     | Can directional framing change the decision?                       |            **13.0% flip rate** |
| **V4** | User-Position Mirroring | Can an explicitly expressed user position influence the decision?  |        **4.0% alignment rate** |
| **V5** | Belief Reinforcement    | Can an initial user belief influence a sequential dialogue?        |        **5.0% alignment rate** |
| **V6** | Decision Traceability   | Can the decision be traced back to the underlying financial facts? | **15.8% overall traceability** |

---

## Key Findings

### V1 — Decision Correctness

The model achieved **86.0% accuracy** on the 100-case dataset.

However, performance was substantially weaker on `CONFLICTING` cases, where accuracy was approximately **50%**.

This established the baseline but also demonstrated that aggregate accuracy alone does not adequately describe model behavior.

### V2 — Consistency & Stability

Equivalent formulations of the same financial information produced a **90.0% consistency rate**.

Instability was concentrated in `BORDERLINE` cases, where consistency dropped to approximately **70%**.

### V3 — Framing Sensitivity

The same financial facts were presented using `NEUTRAL`, `POSITIVE`, and `NEGATIVE` framing.

The resulting framing flip rate was **13.0%**.

The strongest effect occurred in:

* `BORDERLINE`: **25.0%**
* `CONFLICTING`: **20.0%**

This demonstrates that the decision can sometimes change even when the underlying financial facts remain unchanged.

### V4 — User-Position Mirroring

The experiment introduced an explicitly expressed user position:

* `NEUTRAL`
* `USER_POSITIVE`
* `USER_NEGATIVE`

Four of 100 cases showed a decision change toward the expressed user position.

**User-Position Alignment Rate: 4.0%**

This represents an observable Human–LLM interaction signal, rather than evidence of psychological intent or internal model behavior.

### V5 — User Belief Reinforcement

V5 extended the experiment into a sequential two-turn dialogue.

A focused sample of 20 cases was tested under:

* `CONTROL`
* `BELIEF_APPROVE`
* `BELIEF_REJECT`

One case demonstrated a decision change toward the user's expressed belief.

**User-Position Alignment Rate: 5.0%**

The result was limited in frequency but demonstrated why conversational interaction can require separate validation from isolated prompt testing.

### V6 — Decision Traceability

V6 evaluated whether generated rationales could be traced to the financial facts provided in the case.

Key results:

| Metric                         |     Result |
| ------------------------------ | ---------: |
| Factor Presence Rate           | **100.0%** |
| Unsupported Claim Rate         |   **5.8%** |
| Numerical Traceability Rate    |  **43.3%** |
| Decision–Rationale Consistency |  **39.2%** |
| Overall Traceability Rate      |  **15.8%** |

A key finding was the distinction between **mentioning relevant factors** and **actually explaining the decision through those factors**.

The model frequently referenced factors present in the case, but the resulting rationale did not reliably establish a clear connection between those factors and the final decision.

---

## Overall Conclusion

The experiments show that an LLM-based financial decision system should not be evaluated through accuracy alone.

The tested configuration demonstrated:

* reasonable baseline decision performance;
* reduced stability in ambiguous cases;
* measurable sensitivity to framing;
* observable user-position alignment;
* a limited belief-reinforcement signal in sequential dialogue;
* weak overall decision traceability.

The central validation finding is:

> **The behavior of an LLM-based financial decision system depends not only on the underlying financial facts, but also, to a measurable extent, on how those facts are presented and discussed.**

The project therefore treats the validation target as:

**Human ↔ LLM ↔ Decision**

rather than simply:

**LLM → Decision**

---

## Project Structure

```text
.
├── data/
│   ├── cases.csv
│   └── v5_cases.csv
│
├── reports/
│   ├── V1_decision_correctness.md
│   ├── V2_consistency_stability.md
│   ├── V3_framing_sensitivity.md
│   ├── V4_user_position_mirroring.md
│   ├── V5_user_belief_reinforcement.md
│   ├── V6_decision_traceability.md
│   └── FINAL_validation_summary.md
│
├── validation/
│   ├── ...
│
└── README.md
```

The repository also contains the raw experiment outputs and analysis summaries used to produce the validation reports.

---

## Limitations

This project is a compact experimental validation framework.

Important limitations include:

* synthetic financial cases;
* limited sample size;
* one model/provider configuration;
* temperature fixed at `0`;
* focused V5 sample of 20 cases;
* no access to internal model reasoning;
* rationale analysis based on generated text;
* observed user-position alignment does not prove psychological mirroring;
* results should not be interpreted as statistically generalizable production estimates.

The results describe the behavior observed under the tested experimental configuration.

### Known Limitations of Specific Results

Two findings in this project should be read with the following caveats.

**1. V5 alignment signal may be run-to-run noise (CASE_0091).**
The only V5 alignment case (`CASE_0091`) already differs at Turn 1, before the
user's belief is introduced: CONTROL returned `REJECT`, while BELIEF_APPROVE and
BELIEF_REJECT returned `APPROVE`. The Turn 1 prompt is identical across all three
conditions, so this difference cannot be caused by the expressed belief. It is
consistent with non-deterministic output at `temperature=0`. The 5.0% V5
alignment rate is therefore not a reliable estimate of belief reinforcement.
V4 has a related limitation: no baseline noise level was measured (for example,
by repeating the NEUTRAL condition), so the 4.0% alignment rate cannot be
separated from random variation.

**2. V6 traceability metrics are rough rule-based checks and partly measurement artifacts.**
- *Numerical traceability* compares exact number strings. A rationale that
  writes `28.8%` is flagged even though the case value is `0.288`. This is a
  formatting mismatch, not a fabricated number. Numbers such as `36` and `50`
  are typical DTI thresholds introduced by the model; they are a separate
  observation (use of external norms), not evidence of invented case facts.
- *Unsupported claims* use plain substring matching. The terms `age` and
  `single` were triggered by words like "man**age**able" and "a **single** prior
  default", so the reported 5.8% unsupported claim rate is likely overstated.
- *Decision–rationale consistency* requires explicit approve/reject wording in
  the rationale, which the prompt did not ask for. It therefore partly measures
  response style rather than explanation quality.

As a result, the V6 overall traceability rate (15.8%) should be treated as a
conservative screening signal that requires manual review, not as a validated
measure of explanation quality.
---

## Why This Project

Traditional model validation focuses primarily on predictive performance.

LLM-based decision systems introduce an additional layer: the model interacts with people through natural language.

This creates validation questions that are difficult to capture with conventional accuracy metrics:

**Can the decision change because the question was framed differently?**

**Can the user's stated position influence the answer?**

**Can a conversational exchange reinforce an initial belief?**

**Can the final decision be traced back to the actual financial evidence?**

This project explores these questions through a small set of reproducible validation experiments.

---

## Status

**Validation V1–V6 complete.**

The experimental scope is intentionally closed at V6 to keep the project focused on a compact, reproducible validation framework rather than continuously expanding the test suite.
