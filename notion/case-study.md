# Customer Growth Analytics: Segmentation, Value & Retention

**Role simulated:** CRM / Marketing Data Analyst  
**Tools:** SQL, Python, pandas, NumPy, SQLite, Streamlit  
**Data:** 100% synthetic, seeded, and public-safe  
**Status:** Reproducible portfolio case study

## The 30-second story

The CRM team wanted to reduce blanket discounting without turning a churn score into an automated decision. I built a customer 360 mart for 8,000 synthetic customers and 60,564 orders, combined RFM and cohort behavior with a transparent logistic model, achieved 0.722 held-out AUC, and identified 1,141 opted-in customers for a randomized retention test based on margin at risk—not risk alone.

## Problem framing

Three questions were being mixed together: *Who is valuable? Who may lapse? Who will respond to an intervention?* RFM and projected margin address the first; churn prediction addresses the second; only a controlled campaign can answer the third. I designed the data product to keep those questions separate.

## My approach

1. Generated public-safe acquisition and order histories with returns and margin.
2. Defined an observation cutoff and a future six-month churn window to prevent label leakage.
3. Built a customer mart with behavioral, economic, RFM, and outcome fields.
4. Created quarterly cohort retention and acquisition-quality views in SQL.
5. Implemented an inspectable NumPy logistic regression and evaluated it on a held-out 30% sample.
6. Combined risk with annualized margin at risk, then required email opt-in for priority test eligibility.
7. Delivered an interactive dashboard, portable executive view, model card, tests, and CI.

## Key results

| Result | Value |
|---|---:|
| Customers / orders | 8,000 / 60,564 |
| Observed six-month churn | 42.2% |
| Held-out AUC | 0.722 |
| Churners captured in top score quintile | 31.9% |
| Opted-in priority test audience | 1,141 |
| Risk-adjusted projected 12-month margin | €689,568 |

## Recommendation

Run a randomized, margin-measured retention test inside the priority audience, with a holdout and contact-frequency guardrails. Evaluate incremental margin—not redemption rate—before scaling. Continue loyalty/referral nurture for high-value low-risk customers and use low-cost reactivation tests for lower-value high-risk groups.

## Responsible analytics choices

- No demographic or protected attributes are generated or modeled.
- Consent is an activation gate, not a predictive feature.
- The model ranks risk; it does not estimate treatment effect.
- The output recommends experiments rather than automatic discounts.
- A model card documents intended use, validation, and required production controls.

## What I would improve with real data

- time-based validation and probability calibration
- category-specific churn horizons and survival analysis
- product, service, and contact-history features with leakage controls
- subgroup performance, stability, and drift monitoring
- true contribution-margin CLV and uncertainty ranges
- uplift modeling only after sufficient randomized treatment data exists

## Interview prompts

- Why is AUC not enough to approve a retention campaign?
- How did you prevent future information leaking into the features?
- Why prioritize margin at risk rather than churn probability alone?
- How would you measure whether the retention action worked?

## Links to add after publishing

- GitHub repository: **[add URL]**
- Live dashboard/demo: **[add URL]**
- Portfolio home: **[add URL]**

