# LLM Financial Decision Validation

# V1–V6 Validation Summary and Overall Conclusions

## 1. Executive Summary

This project evaluated an LLM-based financial decision system from a broader validation perspective than model accuracy alone.

The validation object was defined as:

**Human ↔ LLM ↔ Decision**

The objective was to assess not only whether the LLM produced reasonable financial decisions, but also whether those decisions were stable, robust to framing, resistant to user-position influence, reproducible in dialogue, and sufficiently traceable to the underlying financial facts.

The validation was performed using 100 synthetic financial cases and the `openai/gpt-oss-120b` model accessed through the Groq API.

Six complementary validation stages were performed:

1. **V1 — Decision Correctness**
2. **V2 — Consistency & Stability**
3. **V3 — Framing Sensitivity**
4. **V4 — User-Position Mirroring**
5. **V5 — User Belief Reinforcement**
6. **V6 — Decision Traceability**

The results demonstrate that the system cannot be adequately characterized by a single accuracy metric.

The model showed generally stable behavior in many straightforward cases, but measurable weaknesses were identified in borderline and conflicting situations, under directional framing, during explicit user-position interaction, and in the traceability of generated rationales.

The experiments therefore provide evidence of several distinct validation risks within the tested configuration.

---

# 2. Validation Scope

| Parameter         | Value                         |
| ----------------- | ----------------------------- |
| Model             | `openai/gpt-oss-120b`         |
| Provider          | Groq                          |
| Primary dataset   | 100 synthetic financial cases |
| Temperature       | 0                             |
| Decision space    | `APPROVE / REJECT`            |
| Validation stages | V1–V6                         |
| Validation object | Human ↔ LLM ↔ Decision        |

The experiments were deliberately designed as a compact validation framework rather than an exhaustive evaluation program.

The purpose was to identify important observable failure modes using a limited number of reproducible experiments.

---

# 3. Validation Matrix

| Validation                     | Risk / Question                                                              |               Main Metric |     Result |
| ------------------------------ | ---------------------------------------------------------------------------- | ------------------------: | ---------: |
| **V1 Decision Correctness**    | Does the LLM make the correct financial decision?                            |                  Accuracy |  **86.0%** |
|                                |                                                                              |       False Approval Rate | **15.38%** |
|                                |                                                                              |      False Rejection Rate | **13.11%** |
| **V2 Consistency & Stability** | Does the decision remain stable under equivalent formulations?               |          Consistency Rate |  **90.0%** |
|                                |                                                                              |        Decision Flip Rate |  **10.0%** |
| **V3 Framing Sensitivity**     | Does directional framing influence the decision?                             |  Framing Consistency Rate |  **87.0%** |
|                                |                                                                              |         Framing Flip Rate |  **13.0%** |
| **V4 User-Position Mirroring** | Does the decision move toward the user's explicitly expressed position?      |            Alignment Rate |   **4.0%** |
|                                |                                                                              |        Decision Flip Rate |   **5.0%** |
| **V5 Belief Reinforcement**    | Does the model reinforce an initially expressed user belief during dialogue? |            Alignment Rate |   **5.0%** |
| **V6 Decision Traceability**   | Can the decision be traced to the financial facts through the rationale?     | Overall Traceability Rate |  **15.8%** |

---

# 4. V1 — Decision Correctness

V1 established the baseline decision performance of the system.

The model achieved:

* Accuracy: **86.0%**
* False Approval Rate: **15.38%**
* False Rejection Rate: **13.11%**

The most important weakness was observed in `CONFLICTING` cases, where accuracy was approximately **50%**.

This indicates that overall accuracy can conceal substantially weaker behavior in cases where financial signals point in different directions.

### Validation finding

**Decision correctness is acceptable as a baseline but is not uniform across case types.**

In particular, conflicting financial evidence represents a materially more difficult decision environment for the tested model.

---

# 5. V2 — Consistency & Stability

V2 tested whether equivalent presentations of the same financial information produced the same decision.

Results:

* Consistency Rate: **90.0%**
* Decision Flip Rate: **10.0%**

The largest instability was observed in `BORDERLINE` cases, where consistency was approximately **70%**.

### Validation finding

The model is generally stable under equivalent formulations, but decision stability decreases substantially near decision boundaries.

This suggests that a single deterministic output should not automatically be interpreted as evidence of robust decision behavior.

---

# 6. V3 — Framing Sensitivity

V3 presented identical financial facts under three framing conditions:

* `NEUTRAL`
* `POSITIVE`
* `NEGATIVE`

Results:

* Framing Consistency Rate: **87.0%**
* Framing Flip Rate: **13.0%**

The observed flip rates were:

| Case Type       | Flip Rate |
| --------------- | --------: |
| `CLEAR_APPROVE` |      0.0% |
| `CLEAR_REJECT`  |     13.3% |
| `BORDERLINE`    |     25.0% |
| `CONFLICTING`   |     20.0% |

Examples included patterns such as:

`REJECT → APPROVE → REJECT`

and:

`APPROVE → APPROVE → REJECT`

The underlying financial facts were unchanged.

### Validation finding

The experiment demonstrated measurable **framing sensitivity**.

The effect was concentrated particularly in borderline and conflicting cases, indicating that the wording surrounding identical financial information can influence the resulting decision.

---

# 7. V4 — User-Position Mirroring

V4 extended framing sensitivity from general directional framing to explicit user positioning.

The same financial facts were presented under:

* `NEUTRAL`
* `USER_POSITIVE`
* `USER_NEGATIVE`

Results:

* 3-way Consistency Rate: **95.0%**
* Decision Flip Rate: **5.0%**
* Positive alignment: **1 case**
* Negative alignment: **3 cases**
* Total alignment cases: **4**
* User-Position Alignment Rate: **4.0%**

Four cases showed a decision change toward the explicitly expressed user position.

### Validation finding

The experiment identified an observable **user-position alignment signal**.

The observed rate was relatively low, and the experiment does not establish that the model possesses a psychological tendency or intent to mirror the user.

However, from a validation perspective, the important observation is operational:

> **The same financial facts can produce different decisions depending on the position explicitly expressed by the user.**

This represents a relevant Human–LLM Interaction Risk for a financial decision system.

---

# 8. V5 — User Belief Reinforcement

V5 investigated a more realistic conversational scenario.

Instead of changing only the framing of a single request, the experiment introduced a two-turn dialogue in which the user initially expressed either:

* a belief that the applicant should be approved, or
* a belief that the applicant should be rejected.

A `CONTROL` dialogue without an expressed user belief was used as the reference condition.

The experiment used:

* 20 selected cases
* 3 dialogue conditions
* 2 turns per condition
* 120 successful model observations

Results:

* Turn 1 Consistency Rate: **95.0%**
* Turn 2 Consistency Rate: **95.0%**
* Control Dialogue Flip Rate: **0.0%**
* Positive alignment: **1**
* Negative alignment: **0**
* Total alignment cases: **1**
* User-Position Alignment Rate: **5.0%**

One case demonstrated a decision shift toward the user's expressed approval position.

### Validation finding

The experiment identified a limited but observable **belief reinforcement / user-position alignment pattern** in sequential dialogue.

The result should not be interpreted as evidence that the model systematically reinforces user beliefs.

However, the finding demonstrates why interaction-level validation is necessary: a model may appear stable when evaluated through isolated prompts while showing different behavior when placed into a conversational context.

---

# 9. V6 — Decision Traceability

V6 examined whether the model's generated rationale could be traced back to the financial information contained in the case.

Results:

| Metric                         |     Result |
| ------------------------------ | ---------: |
| Factor Presence Rate           | **100.0%** |
| Unsupported Claim Rate         |   **5.8%** |
| Numerical Traceability Rate    |  **43.3%** |
| Decision–Rationale Consistency |  **39.2%** |
| Overall Traceability Rate      |  **15.8%** |

The results reveal an important distinction.

The model frequently referred to factors that were actually present in the case, resulting in a **100% Factor Presence Rate**.

However, this did not translate into strong decision traceability.

Only **39.2%** of observations satisfied the defined Decision–Rationale Consistency criterion, and the overall traceability rate was **15.8%**.

### Validation finding

The model's rationale frequently contains relevant financial factors, but the rationale does not reliably establish a clear connection between those factors and the final decision.

Therefore:

> **Presence of relevant factors should not be treated as equivalent to decision explainability or traceability.**

This is particularly important in a financial decision context, where an explanation should provide a sufficiently clear basis for understanding how the available evidence supports the resulting decision.

---

# 10. Cross-Validation Findings

The six validation stages reveal several related but distinct risk dimensions.

## 10.1 Decision correctness is not sufficient

The V1 result of **86.0% accuracy** provides useful baseline information, but it does not describe:

* decision stability;
* sensitivity to framing;
* user influence;
* conversational effects;
* rationale traceability.

A model can therefore achieve reasonable accuracy while still exhibiting important validation weaknesses.

---

## 10.2 Risk increases near ambiguous decisions

Across V2, V3, and V4, instability was particularly visible in:

* `BORDERLINE`
* `CONFLICTING`

cases.

This suggests that interaction-related risks are not uniformly distributed across the decision space.

Clear cases tend to remain stable.

Ambiguous cases are more susceptible to changes in formulation and conversational context.

---

## 10.3 Human–LLM interaction is itself a validation dimension

V3–V5 demonstrate that the validation object cannot be limited to:

**LLM → Decision**

A more realistic representation is:

**Human ↔ LLM ↔ Decision**

The user's wording, framing, expressed position, and conversational context can become part of the effective input to the decision system.

This creates a distinct class of risks that would not necessarily be detected by conventional model-performance testing.

---

## 10.4 Rationale quality is different from decision quality

V6 demonstrates that a model can:

1. identify relevant financial factors;
2. produce a plausible-looking rationale;
3. and still fail to provide a sufficiently traceable explanation for the actual decision.

This distinction is important for financial applications because a plausible explanation is not necessarily a faithful or decision-traceable explanation.

---

# 11. Overall Validation Assessment

Based on the experiments performed, the tested configuration should **not be characterized solely by its 86.0% decision accuracy**.

The validation identified the following observable risks:

| Risk                       | Evidence | Assessment                                |
| -------------------------- | -------- | ----------------------------------------- |
| Decision errors            | V1       | Present                                   |
| Decision instability       | V2       | Present, concentrated in borderline cases |
| Framing sensitivity        | V3       | Present                                   |
| User-position influence    | V4       | Observable                                |
| Belief reinforcement       | V5       | Limited observable signal                 |
| Weak decision traceability | V6       | Material finding                          |

The strongest findings are not necessarily the largest numerical rates.

Of particular importance are:

* **25.0% framing flip rate in borderline cases**
* **4.0% explicit user-position alignment rate**
* **5.0% user-position alignment rate in the V5 dialogue sample**
* **39.2% Decision–Rationale Consistency**
* **15.8% Overall Traceability Rate**

These findings indicate that the system's behavior depends not only on the financial facts themselves, but also, to a measurable extent, on how those facts are presented and discussed.

---

# 12. Overall Validation Conclusion

The validation provides evidence that the tested LLM can perform financial decision classification with reasonable baseline accuracy, but its behavior is not fully invariant to formulation, framing, user interaction, or conversational context.

The principal validation conclusion is therefore:

> **The tested LLM configuration demonstrates usable baseline decision capability, but also exhibits measurable interaction sensitivity and limited decision traceability that should be considered material validation risks in a financial decision system.**

The experiments do not establish that the model is intentionally biased toward users, that it possesses psychological tendencies, or that the observed effects generalize to other models or production environments.

Instead, they establish a set of **observable behavioral properties under controlled experimental conditions**.

From a model-validation perspective, this distinction is important.

The relevant question is not whether the LLM can be described as "aligned" or "unreliable" in general.

The relevant question is:

> **Under what conditions can the system's financial decision change, and can that change be detected and explained?**

The V1–V6 framework demonstrates a practical approach to answering that question.

---

# 13. Scope and Limitations

The conclusions are subject to the following limitations:

* The dataset contains 100 synthetic financial cases.
* V5 uses a focused sample of 20 cases.
* The experiments evaluate one model/provider configuration.
* The model was accessed through the Groq API.
* Temperature was fixed at 0.
* The experiments do not measure internal model reasoning.
* Rationale analysis evaluates generated text rather than hidden model processes.
* User-position alignment is an observable behavioral pattern, not proof of psychological mirroring.
* The results are not sufficient to establish statistical generalization to production populations.
* The validation framework evaluates the tested configuration and prompt design, not the model in isolation from its surrounding system.

---

# 14. Final Project Conclusion

This project demonstrates a compact validation framework for an LLM-based financial decision system that extends beyond conventional accuracy testing.

The framework evaluates three connected layers:

**Financial facts → LLM → Decision**

while explicitly incorporating:

**Human ↔ LLM interaction**

The resulting validation framework covers six complementary dimensions:

**Correctness → Stability → Framing → User Influence → Dialogue → Traceability**

The experiments demonstrate that these dimensions can reveal materially different properties of the same model.

Consequently, for LLM-based financial decision systems, **model validation should not be reduced to accuracy, benchmark performance, or isolated prompt-response testing**.

A robust validation process should also examine how decisions behave under controlled changes in formulation, framing, user position, conversational context, and explanation requirements.

This project stops at V6 deliberately.

The objective was not to build an exhaustive catalogue of LLM risks, but to demonstrate a compact, reproducible validation methodology capable of identifying meaningful risks in an LLM-based financial decision system.
