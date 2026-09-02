DROP VIEW IF EXISTS vw_segment_health;
DROP VIEW IF EXISTS vw_acquisition_quality;

CREATE VIEW vw_segment_health AS
SELECT
    rfm_segment,
    COUNT(*) AS customers,
    ROUND(AVG(churn_probability), 4) AS average_churn_probability,
    ROUND(SUM(projected_12m_margin), 2) AS projected_12m_margin,
    ROUND(AVG(clv_to_cac), 2) AS average_clv_to_cac
FROM customer_360
GROUP BY rfm_segment;

CREATE VIEW vw_acquisition_quality AS
SELECT
    acquisition_channel,
    COUNT(*) AS customers,
    ROUND(AVG(acquisition_cost), 2) AS average_cac,
    ROUND(SUM(gross_margin), 2) AS observed_margin,
    ROUND(SUM(projected_12m_margin), 2) AS projected_12m_margin,
    ROUND(AVG(churned_6m), 4) AS six_month_churn_rate,
    ROUND(AVG(clv_to_cac), 2) AS average_clv_to_cac
FROM customer_360
GROUP BY acquisition_channel;

