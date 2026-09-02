-- 1. Which segments combine material value and retention risk?
SELECT *
FROM vw_segment_health
ORDER BY projected_12m_margin DESC;

-- 2. Which acquisition sources produce durable economics?
SELECT *
FROM vw_acquisition_quality
ORDER BY average_clv_to_cac DESC;

-- 3. Size an opted-in, high-value retention experiment.
SELECT
    rfm_segment,
    COUNT(*) AS eligible_customers,
    ROUND(AVG(churn_probability), 3) AS average_risk,
    ROUND(SUM(projected_12m_margin), 2) AS margin_at_stake
FROM customer_360
WHERE recommended_action = 'priority retention test'
  AND email_opt_in = 1
GROUP BY rfm_segment
ORDER BY margin_at_stake DESC;

-- 4. Review quarterly cohort retention without hiding cohort size.
SELECT cohort, period_number, active_customers, cohort_size, ROUND(retention_rate, 3) AS retention_rate
FROM cohort_retention
ORDER BY cohort, period_number;

