# LLM Financial Decision Validation

## Validation Matrix

### 1. Validation Objective

The objective of the validation framework is to evaluate an LLM-based financial decision system from both a decision-quality and a human–LLM interaction perspective.

The validation object is defined as:

**Human ↔ LLM ↔ Decision**

The framework therefore evaluates not only whether the system produces an appropriate financial decision, but also whether the decision is stable under changes in wording, framing, and the user's explicitly expressed position.

The current validation scope consists of four experimental areas:

1. Decision Correctness
2. Consistency & Stability
3. Framing Sensitivity
4. User-Position Mirroring

The experiments use the same synthetic financial case set and the same model configuration unless explicitly stated otherwise.

---

## 2. Validation Matrix

| ID | Validation Area         | Risk Addressed                                                                             | Experimental Approach                                                      | Primary Metric               | Result | Status    |
| -- | ----------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | ---------------------------- | -----: | --------- |
| V1 | Decision Correctness    | The system may produce an incorrect financial decision                                     | Compare model decisions with expected decisions across 100 synthetic cases | Accuracy                     |  86.0% | Completed |
| V2 | Consistency & Stability | The decision may change when equivalent financial information is expressed differently     | Evaluate equivalent formulations of the same financial cases               | Consistency Rate             |  90.0% | Completed |
| V3 | Framing Sensitivity     | Decision may be affected by positive or negative framing despite identical financial facts | Compare Neutral, Positive and Negative framing conditions                  | Framing Consistency Rate     |  87.0% | Completed |
| V4 | User-Position Mirroring | Decision may move toward the user's explicitly stated preference                           | Compare Neutral, User-Positive and User-Negative conditions                | User-Position Alignment Rate |   4.0% | Completed |

---

## 3. Coverage by Risk

### 3.1 Decision Correctness

**Coverage: Direct**

V1 establishes a baseline for decision quality.

The model achieved an accuracy of **86.0%** on the tested synthetic dataset. The experiment also measured false approval and false rejection rates and identified weaker performance on `CONFLICTING` cases.

This establishes that the validation framework must consider not only aggregate correctness but also the structure of errors across different case types.

---

### 3.2 Output Consistency

**Coverage: Direct**

V2 evaluates whether equivalent financial information produces the same decision when the wording is changed.

The observed consistency rate was **90.0%**, corresponding to a **10.0% decision flip rate**.

The strongest instability was observed in `BORDERLINE` cases.

This indicates that decision correctness alone is insufficient for evaluating an LLM financial decision system: the same underlying case can produce different decisions under alternative formulations.

---

### 3.3 Framing Sensitivity

**Coverage: Direct**

V3 evaluates whether the decision changes when identical financial facts are presented using different framing.

The experiment produced a **87.0% framing consistency rate** and a **13.0% framing flip rate**.

The effect was concentrated in less clear cases, particularly `BORDERLINE` and `CONFLICTING` cases.

This provides a direct test of whether conversational framing can influence the resulting financial decision.

---

### 3.4 User-Position Alignment

**Coverage: Direct**

V4 evaluates whether the system changes its decision in the direction of an explicitly stated user preference.

The experiment produced:

* **95.0%** three-way decision consistency
* **5.0%** overall decision flip rate
* **4.0%** user-position alignment rate

Four of the five cases with decision changes were classified as changes toward the explicitly expressed user position.

The experiment therefore detected an observable user-position alignment signal in the tested setup.

This result should not be interpreted as evidence of an internal psychological mechanism or user-intent recognition. The experiment measures an observable relationship between the expressed user position and the resulting decision.

---

## 4. Uncovered or Partially Covered Risks

The current matrix does not attempt to cover every possible risk of an LLM-based financial decision system.

The following areas remain outside or only partially inside the current validation scope.

| Risk / Property                           | Coverage                | Reason                                                                                                        |
| ----------------------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------- |
| Explanation consistency                   | Partial                 | Rationales were collected, but the primary validation target was the decision rather than explanation quality |
| Factual robustness                        | Partial                 | The experiments use controlled synthetic financial cases and do not independently test factual perturbations  |
| Explicit manipulation resistance          | Not covered             | No dedicated adversarial or manipulation-oriented prompt test was performed                                   |
| Multi-turn conversational drift           | Not covered             | Current experiments are based on controlled single-turn conditions                                            |
| Long-term conversational influence        | Not covered             | No repeated interaction or longitudinal experiment was performed                                              |
| Generalization to real-world applications | Not covered             | The dataset consists of synthetic financial cases                                                             |
| Generalization across models/providers    | Not covered             | Experiments use one model/provider configuration                                                              |
| Internal reasoning / causal mechanism     | Not measurable directly | Observable outputs do not establish the internal mechanism producing them                                     |

These gaps are documented as **scope limitations**, not as failures of the validation framework.

---

## 5. Scope Assessment

The current validation matrix covers four distinct and complementary behavioral dimensions:

### Decision quality

Can the system produce the expected financial decision?

### Behavioral stability

Does the decision remain stable when equivalent information is expressed differently?

### Framing sensitivity

Can the presentation of identical financial facts influence the decision?

### Human–LLM interaction

Does an explicitly expressed user position correlate with a change in the resulting decision?

Together, these dimensions extend the validation target beyond conventional model-performance metrics.

The framework therefore evaluates both:

**LLM → Decision**

and

**Human → LLM → Decision**

This distinction is central to the project.

---

## 6. Experimental Phase Decision

The current experiments provide measurable results for all four primary validation areas defined for the project.

Additional validation areas can be identified, including adversarial manipulation, multi-turn conversational drift, explanation robustness, and cross-model generalization.

However, adding these tests would substantially expand the experimental scope without being necessary to demonstrate the core validation concept of the current project.

### Decision

**The experimental phase is considered complete for V1.0.**

No additional API-based validation experiments are required at this stage.

The next phase is to consolidate the V1–V4 results into the final **Validation Framework / Validation Report**, including:

* validation objectives;
* experimental methodology;
* results;
* risk interpretation;
* limitations;
* validation conclusions;
* recommendations for future validation.

The framework deliberately defines its coverage and limitations rather than attempting to provide exhaustive validation of every possible LLM risk.
