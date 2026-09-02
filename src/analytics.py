"""Customer mart, segmentation, CLV proxy, and transparent churn model."""

from __future__ import annotations

import numpy as np
import pandas as pd


OBSERVATION_END = pd.Timestamp("2025-06-30")
OUTCOME_END = pd.Timestamp("2025-12-31")
FEATURES = ["recency_days", "frequency", "monetary", "avg_order_value", "margin_rate", "tenure_days", "acquisition_cost"]


def build_customer_mart(customers: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    orders = orders.copy()
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    pre = orders[orders["order_date"] <= OBSERVATION_END]
    future = orders[(orders["order_date"] > OBSERVATION_END) & (orders["order_date"] <= OUTCOME_END)]
    agg = pre.groupby("customer_id", as_index=False).agg(
        last_order_date=("order_date", "max"),
        frequency=("order_id", "nunique"),
        monetary=("net_revenue", "sum"),
        gross_margin=("gross_margin", "sum"),
        avg_order_value=("net_revenue", "mean"),
        return_rate=("returned", "mean"),
    )
    outcome = future.groupby("customer_id", as_index=False).agg(
        future_orders=("order_id", "nunique"), future_revenue=("net_revenue", "sum")
    )
    mart = customers.merge(agg, on="customer_id", how="left").merge(outcome, on="customer_id", how="left")
    mart[["frequency", "monetary", "gross_margin", "avg_order_value", "return_rate", "future_orders", "future_revenue"]] = mart[
        ["frequency", "monetary", "gross_margin", "avg_order_value", "return_rate", "future_orders", "future_revenue"]
    ].fillna(0)
    mart["last_order_date"] = pd.to_datetime(mart["last_order_date"])
    mart["signup_date"] = pd.to_datetime(mart["signup_date"])
    mart["recency_days"] = (OBSERVATION_END - mart["last_order_date"]).dt.days.clip(lower=0)
    mart["tenure_days"] = (OBSERVATION_END - mart["signup_date"]).dt.days.clip(lower=1)
    mart["margin_rate"] = (mart["gross_margin"] / mart["monetary"].replace(0, np.nan)).fillna(0)
    mart["churned_6m"] = (mart["future_orders"] == 0).astype(int)
    return mart


def segment_rfm(mart: pd.DataFrame) -> pd.DataFrame:
    result = mart.copy()
    result["r_score"] = pd.qcut(result["recency_days"].rank(method="first", ascending=False), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    result["f_score"] = pd.qcut(result["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    result["m_score"] = pd.qcut(result["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    conditions = [
        (result["r_score"] >= 4) & (result["f_score"] >= 4),
        result["f_score"] >= 4,
        (result["r_score"] >= 4) & (result["f_score"] <= 2),
        (result["r_score"] <= 2) & (result["f_score"] >= 3),
        (result["r_score"] <= 2) & (result["f_score"] <= 2),
    ]
    result["rfm_segment"] = np.select(conditions, ["champions", "loyal", "new/promising", "at risk", "hibernating"], default="potential loyalist")
    return result


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(values, -30, 30)))


def _auc(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    positives = y_true == 1
    n_pos, n_neg = int(positives.sum()), int((~positives).sum())
    if n_pos == 0 or n_neg == 0:
        return 0.5
    ranks = pd.Series(probabilities).rank(method="average").to_numpy()
    return float((ranks[positives].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def fit_churn_model(mart: pd.DataFrame, seed: int = 123, iterations: int = 1_500, learning_rate: float = 0.08) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    """Fit an auditable NumPy logistic regression and score every customer."""
    x = mart[FEATURES].astype(float).to_numpy()
    y = mart["churned_6m"].astype(float).to_numpy()
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale == 0] = 1.0
    z = (x - mean) / scale
    z = np.column_stack([np.ones(len(z)), z])
    rng = np.random.default_rng(seed)
    test = rng.random(len(z)) < 0.30
    train = ~test
    weights = np.zeros(z.shape[1])
    for _ in range(iterations):
        prediction = _sigmoid(z[train] @ weights)
        gradient = z[train].T @ (prediction - y[train]) / train.sum()
        weights -= learning_rate * gradient
    probability = _sigmoid(z @ weights)
    scored = mart.copy()
    scored["churn_probability"] = probability
    scored["sample"] = np.where(test, "test", "train")
    threshold = float(np.quantile(probability[test], 0.80))
    test_targeted = test & (probability >= threshold)
    capture = float(y[test_targeted].sum() / max(y[test].sum(), 1))
    precision = float(y[test_targeted].mean()) if test_targeted.any() else 0.0
    metrics = {
        "test_auc": _auc(y[test], probability[test]),
        "test_churn_rate": float(y[test].mean()),
        "top_20pct_capture": capture,
        "top_20pct_precision": precision,
        "score_threshold": threshold,
        "test_customers": int(test.sum()),
    }
    coefficients = pd.DataFrame(
        {
            "feature": ["intercept"] + FEATURES,
            "standardized_coefficient": weights,
            "direction": np.where(weights > 0, "increases churn score", "decreases churn score"),
        }
    )
    return scored, coefficients, metrics


def add_value_and_actions(scored: pd.DataFrame) -> pd.DataFrame:
    result = scored.copy()
    observation_years = (result["tenure_days"].clip(lower=180) / 365.25).clip(upper=1.5)
    annual_orders = result["frequency"] / observation_years
    result["annual_margin_run_rate"] = annual_orders * result["avg_order_value"] * result["margin_rate"]
    result["projected_12m_margin"] = result["annual_margin_run_rate"] * (1 - result["churn_probability"])
    result["margin_at_risk"] = result["annual_margin_run_rate"] * result["churn_probability"]
    result["clv_to_cac"] = result["projected_12m_margin"] / result["acquisition_cost"].replace(0, np.nan)
    high_value = result["annual_margin_run_rate"] >= result["annual_margin_run_rate"].quantile(0.70)
    high_risk = result["churn_probability"] >= result["churn_probability"].quantile(0.70)
    priority = result["margin_at_risk"] >= result["margin_at_risk"].quantile(0.80)
    result["recommended_action"] = np.select(
        [priority & (result["email_opt_in"] == 1), high_value & ~high_risk, ~high_value & high_risk & (result["email_opt_in"] == 1)],
        ["priority retention test", "loyalty / referral nurture", "low-cost reactivation test"],
        default="business-as-usual measurement",
    )
    return result


def cohort_retention(orders: pd.DataFrame) -> pd.DataFrame:
    frame = orders.copy()
    frame["order_date"] = pd.to_datetime(frame["order_date"])
    frame = frame[frame["order_date"] <= OBSERVATION_END]
    first = frame.groupby("customer_id")["order_date"].transform("min")
    frame["cohort"] = first.dt.to_period("Q").astype(str)
    frame["period_number"] = ((frame["order_date"].dt.year - first.dt.year) * 12 + frame["order_date"].dt.month - first.dt.month) // 3
    active = frame.groupby(["cohort", "period_number"])["customer_id"].nunique().rename("active_customers").reset_index()
    size = active[active["period_number"] == 0][["cohort", "active_customers"]].rename(columns={"active_customers": "cohort_size"})
    result = active.merge(size, on="cohort", how="left")
    result["retention_rate"] = result["active_customers"] / result["cohort_size"]
    return result
