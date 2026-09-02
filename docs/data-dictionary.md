# Data dictionary

All records are synthetic and generated with seed 77.

## `customers.csv`

| Field | Meaning |
|---|---|
| `customer_id` | Synthetic non-identifying primary key |
| `signup_date` | Simulated acquisition date |
| `acquisition_channel` | Organic, paid search/social, affiliate, or referral |
| `region` | Synthetic commercial region |
| `email_opt_in` | Activation permission flag; not a model feature |
| `acquisition_cost` | Simulated customer acquisition cost in EUR |

## `orders.csv`

| Field | Meaning |
|---|---|
| `order_id`, `customer_id` | Order primary key and customer foreign key |
| `order_date` | Simulated transaction date |
| `gross_revenue` | Revenue before returns |
| `returned` | Simulated return flag |
| `net_revenue` | Zero for returned orders; otherwise gross revenue |
| `gross_margin` | Simulated order-level margin contribution |

## `customer_360.csv`

| Field group | Fields and meaning |
|---|---|
| Behavior | `recency_days`, `frequency`, `monetary`, `avg_order_value`, `return_rate` at 2025-06-30 |
| Outcome | `future_orders`, `future_revenue`, `churned_6m` during 2025 H2 |
| RFM | `r_score`, `f_score`, `m_score`, `rfm_segment` |
| Model | `churn_probability`, `sample` |
| Economics | `annual_margin_run_rate`, `projected_12m_margin`, `margin_at_risk`, `clv_to_cac` |
| Activation | `recommended_action`; priority audiences also require `email_opt_in = 1` |

