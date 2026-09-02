"""Build the customer growth mart, models, decision tables, and HTML report."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import pandas as pd

from src.analytics import add_value_and_actions, build_customer_mart, cohort_retention, fit_churn_model, segment_rfm


def build(raw_dir: Path, processed_dir: Path, output_dir: Path) -> dict[str, float]:
    customers = pd.read_csv(raw_dir / "customers.csv")
    orders = pd.read_csv(raw_dir / "orders.csv")
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    mart = segment_rfm(build_customer_mart(customers, orders))
    scored, coefficients, metrics = fit_churn_model(mart)
    scored = add_value_and_actions(scored)
    cohorts = cohort_retention(orders)

    scored.to_csv(processed_dir / "customer_360.csv", index=False)
    coefficients.to_csv(processed_dir / "model_coefficients.csv", index=False)
    cohorts.to_csv(processed_dir / "cohort_retention.csv", index=False)
    contact = scored[(scored["recommended_action"] == "priority retention test") & (scored["email_opt_in"] == 1)].sort_values(
        ["projected_12m_margin", "churn_probability"], ascending=False
    )
    contact[["customer_id", "rfm_segment", "churn_probability", "projected_12m_margin", "recommended_action"]].to_csv(processed_dir / "retention_test_audience.csv", index=False)

    with sqlite3.connect(processed_dir / "customer_growth.db") as connection:
        customers.to_sql("customers", connection, if_exists="replace", index=False)
        orders.to_sql("orders", connection, if_exists="replace", index=False)
        scored.to_sql("customer_360", connection, if_exists="replace", index=False)
        cohorts.to_sql("cohort_retention", connection, if_exists="replace", index=False)
        connection.executescript(Path("sql/schema.sql").read_text())

    summary = {
        "customers": int(len(customers)),
        "orders": int(len(orders)),
        "six_month_churn_rate": round(float(scored["churned_6m"].mean()), 4),
        "test_auc": round(float(metrics["test_auc"]), 3),
        "top_20pct_churn_capture": round(float(metrics["top_20pct_capture"]), 3),
        "priority_retention_audience": int(len(contact)),
        "projected_12m_margin": round(float(scored["projected_12m_margin"].sum()), 2),
    }
    (output_dir / "model_metrics.json").write_text(json.dumps(metrics, indent=2))
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    segments = scored.groupby("rfm_segment", as_index=False).agg(customers=("customer_id", "nunique"), margin=("projected_12m_margin", "sum"), churn_probability=("churn_probability", "mean")).sort_values("margin", ascending=False)
    max_margin = max(float(segments["margin"].max()), 1.0)
    bars = "".join(
        f'<div class="bar-row"><span>{r.rfm_segment.title()}</span><div class="bar" style="width:{max(4, r.margin/max_margin*100):.1f}%"></div><b>€{r.margin:,.0f}</b></div>'
        for r in segments.itertuples(index=False)
    )
    actions = scored.groupby("recommended_action", as_index=False).agg(customers=("customer_id", "count"), margin=("projected_12m_margin", "sum"), risk=("churn_probability", "mean")).sort_values("margin", ascending=False)
    action_rows = "".join(f"<tr><td>{r.recommended_action.title()}</td><td>{r.customers:,}</td><td>€{r.margin:,.0f}</td><td>{r.risk:.1%}</td></tr>" for r in actions.itertuples(index=False))
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Customer Growth Executive View</title><style>body{{font-family:Inter,Arial;background:#f7f5ff;color:#243b53;margin:0}}main{{max-width:1120px;margin:auto;padding:40px}}.sub{{color:#627d98}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:28px 0}}.card,section{{background:white;border-radius:12px;padding:22px;box-shadow:0 5px 20px #bcccdc55}}section{{margin:18px 0}}.label{{font-size:12px;text-transform:uppercase;color:#627d98}}.value{{font-size:28px;font-weight:700;margin-top:8px}}.bar-row{{display:grid;grid-template-columns:160px 1fr 110px;align-items:center;gap:14px;margin:14px 0}}.bar{{height:18px;background:linear-gradient(90deg,#6741d9,#b197fc);border-radius:6px}}table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;border-bottom:1px solid #d9e2ec;text-align:left}}th{{font-size:12px;color:#627d98;text-transform:uppercase}}.note{{font-size:12px;color:#829ab1}}@media(max-width:800px){{.cards{{grid-template-columns:1fr 1fr}}}}</style></head><body><main><h1>Customer growth & retention</h1><p class="sub">RFM · value · six-month churn risk · synthetic decision-support case study</p><div class="cards"><div class="card"><div class="label">Customers</div><div class="value">{summary['customers']:,}</div></div><div class="card"><div class="label">6m churn rate</div><div class="value">{summary['six_month_churn_rate']:.1%}</div></div><div class="card"><div class="label">Holdout AUC</div><div class="value">{summary['test_auc']:.3f}</div></div><div class="card"><div class="label">Top-20% capture</div><div class="value">{summary['top_20pct_churn_capture']:.1%}</div></div></div><section><h2>Projected 12-month margin by RFM segment</h2>{bars}<p class="note">A transparent planning proxy discounted by modeled churn probability; not an accounting valuation.</p></section><section><h2>Recommended measurement tracks</h2><table><thead><tr><th>Action</th><th>Customers</th><th>Projected margin</th><th>Avg. churn risk</th></tr></thead><tbody>{action_rows}</tbody></table><p class="note">Only opted-in synthetic customers enter retention test audiences. Protected attributes are not generated or used.</p></section></main></body></html>"""
    (output_dir / "executive_dashboard.html").write_text(html)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    print(json.dumps(build(args.raw_dir, args.processed_dir, args.output_dir), indent=2))


if __name__ == "__main__":
    main()

