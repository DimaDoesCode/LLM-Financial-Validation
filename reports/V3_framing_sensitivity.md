# V3 Framing Sensitivity

## Objective

Evaluate whether an LLM financial decision changes when the same underlying financial facts are presented with different directional framing.

**Model:** `openai/gpt-oss-120b`
**Provider:** Groq
**Dataset:** 100 synthetic financial cases
**Framing variants:** Neutral / Positive / Negative
**Temperature:** 0

The financial facts were kept unchanged across all three variants.

---

## Results

| Metric                   |    Result |
| ------------------------ | --------: |
| Cases evaluated          |       100 |
| Framing Consistency Rate | **87.0%** |
| Framing Flip Rate        | **13.0%** |
| Decision flips           |    **13** |

### Flip Rate by Case Type

| Case Type     | Cases | Flips | Flip Rate |
| ------------- | ----: | ----: | --------: |
| CLEAR_APPROVE |    30 |     0 |  **0.0%** |
| CLEAR_REJECT  |    30 |     4 | **13.3%** |
| BORDERLINE    |    20 |     5 | **25.0%** |
| CONFLICTING   |    20 |     4 | **20.0%** |

---

## Observed Patterns

Several cases demonstrated directional framing effects.

Examples:

`CASE_0035`

`REJECT → APPROVE → REJECT`

Neutral and negative framing produced rejection, while positive framing produced approval.

`CASE_0045`

`APPROVE → APPROVE → REJECT`

Negative framing changed the decision from approval to rejection.

`CASE_0076`

`REJECT → APPROVE → REJECT`

The same underlying financial information resulted in different decisions depending on framing.

The observed flips occurred predominantly in `BORDERLINE` and `CONFLICTING` cases.

---

## Validation Finding

**Finding V3-01 — Decision sensitivity to directional framing**

13% of tested cases produced different decisions across the Neutral, Positive, and Negative framing conditions despite unchanged underlying financial facts.

The effect was strongest in ambiguous cases:

* `BORDERLINE`: 25.0% flip rate
* `CONFLICTING`: 20.0% flip rate

No framing flips were observed in `CLEAR_APPROVE` cases.

---

## Interpretation

The experiment provides evidence that the tested LLM can be sensitive to the framing of financial information.

The result should not be interpreted as proof that exactly 13% of decisions are caused by framing in real-world use. The result applies specifically to this synthetic dataset, prompt design, model, and experimental conditions.

V3 establishes a measurable baseline for **Framing Sensitivity**.

**V3 is considered complete.**
