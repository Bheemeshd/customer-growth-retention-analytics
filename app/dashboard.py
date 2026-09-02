"""Interactive customer growth dashboard."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"

st.set_page_config(page_title="Customer Growth Analytics", page_icon="🌱", layout="wide")
st.title("Customer growth, value & retention")
st.caption("Synthetic data · model-assisted decision support · values shown in EUR")

customers = pd.read_csv(DATA / "customer_360.csv")
cohorts = pd.read_csv(DATA / "cohort_retention.csv")

segments = st.multiselect("RFM segment", sorted(customers["rfm_segment"].unique()), default=sorted(customers["rfm_segment"].unique()))
view = customers[customers["rfm_segment"].isin(segments)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Customers", f"{len(view):,}")
c2.metric("6m churn rate", f"{view['churned_6m'].mean():.1%}")
c3.metric("Projected 12m margin", f"€{view['projected_12m_margin'].sum():,.0f}")
c4.metric("Priority test audience", f"{(view['recommended_action'] == 'priority retention test').sum():,}")

left, right = st.columns(2)
with left:
    st.subheader("Value and risk by segment")
    segment_view = view.groupby("rfm_segment", as_index=False).agg(customers=("customer_id", "count"), projected_margin=("projected_12m_margin", "sum"), churn_risk=("churn_probability", "mean"))
    st.plotly_chart(px.scatter(segment_view, x="churn_risk", y="projected_margin", size="customers", color="rfm_segment", hover_name="rfm_segment"), use_container_width=True)
with right:
    st.subheader("Risk distribution")
    st.plotly_chart(px.histogram(view, x="churn_probability", color="rfm_segment", nbins=25, barmode="overlay"), use_container_width=True)

st.subheader("Quarterly cohort retention")
heatmap = cohorts.pivot(index="cohort", columns="period_number", values="retention_rate")
st.plotly_chart(px.imshow(heatmap, text_auto=".0%", aspect="auto", color_continuous_scale="Purples", labels={"color": "Retention"}), use_container_width=True)

st.subheader("Action framework")
actions = view.groupby("recommended_action", as_index=False).agg(customers=("customer_id", "count"), projected_margin=("projected_12m_margin", "sum"), average_risk=("churn_probability", "mean"))
st.dataframe(actions, use_container_width=True, hide_index=True)
st.info("The model prioritizes tests; it does not prescribe treatment. Only opted-in synthetic customers enter retention audiences, and no protected attributes are used.")

