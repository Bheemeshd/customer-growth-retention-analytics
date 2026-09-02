import unittest

from src.analytics import add_value_and_actions, build_customer_mart, cohort_retention, fit_churn_model, segment_rfm
from src.generate_data import generate


class CustomerGrowthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.customers, cls.orders = generate(seed=11, n_customers=2_000)
        cls.mart = segment_rfm(build_customer_mart(cls.customers, cls.orders))

    def test_generator_and_customer_mart(self):
        self.assertEqual(self.customers["customer_id"].nunique(), len(self.customers))
        self.assertFalse(self.orders["order_id"].duplicated().any())
        self.assertEqual(len(self.mart), len(self.customers))
        self.assertTrue(self.mart["churned_6m"].isin([0, 1]).all())

    def test_rfm_scores_and_segments(self):
        for field in ["r_score", "f_score", "m_score"]:
            self.assertTrue(self.mart[field].between(1, 5).all())
        self.assertFalse(self.mart["rfm_segment"].isna().any())

    def test_model_is_valid_and_better_than_random(self):
        scored, coefficients, metrics = fit_churn_model(self.mart, iterations=900)
        self.assertTrue(scored["churn_probability"].between(0, 1).all())
        self.assertGreater(metrics["test_auc"], 0.65)
        self.assertEqual(len(coefficients), 8)

    def test_value_actions_respect_opt_in_for_priority(self):
        scored, _, _ = fit_churn_model(self.mart, iterations=900)
        result = add_value_and_actions(scored)
        priority = result[result["recommended_action"] == "priority retention test"]
        self.assertTrue((priority["email_opt_in"] == 1).all())
        self.assertTrue((result["projected_12m_margin"] >= 0).all())

    def test_cohort_retention_bounds(self):
        result = cohort_retention(self.orders)
        self.assertTrue(result["retention_rate"].between(0, 1).all())
        self.assertTrue((result["active_customers"] <= result["cohort_size"]).all())


if __name__ == "__main__":
    unittest.main()

