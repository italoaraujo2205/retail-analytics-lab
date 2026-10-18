import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from retail_lab.analysis import cohorts
from retail_lab.experiment import analyze
from retail_lab.generate import generate_experiment
from retail_lab.quality import DataQualityError


class AnalysisExperimentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.experiment = generate_experiment(Path(self.tmp.name))

    def test_more_conversion_can_have_lower_profit(self):
        result = analyze(self.experiment, bootstrap_samples=200)
        self.assertGreater(result["conversion_difference_pp"], 0)
        self.assertLess(result["ci_95"][1], 0)
        self.assertEqual(sum(g["n"] for g in result["groups"].values()), len(self.experiment))
        # Independent business-denominator assertion: includes all randomized customers.
        for name in ["control", "discount"]:
            group = self.experiment[self.experiment.variant == name]
            expected = group.contribution.sum() / len(group)
            self.assertAlmostEqual(result["groups"][name]["mean_contribution"], expected)

    def test_duplicate_randomized_customer_is_rejected(self):
        frame = pd.concat([self.experiment, self.experiment.iloc[:1]], ignore_index=True)
        with self.assertRaisesRegex(DataQualityError, "one row"):
            analyze(frame)

    def test_sample_ratio_mismatch_is_rejected(self):
        frame = self.experiment.copy()
        frame["variant"] = ["control"] * 15000 + ["discount"] * 1000
        with self.assertRaisesRegex(DataQualityError, "Sample ratio mismatch"):
            analyze(frame)

    def test_nonconverter_cannot_have_purchase_outcome(self):
        frame = self.experiment.copy()
        index = frame.index[frame.converted == 0][0]
        frame.loc[index, ["net_revenue", "contribution"]] = 1
        with self.assertRaisesRegex(DataQualityError, "Non-converter"):
            analyze(frame)

    def test_future_retention_is_missing_not_zero(self):
        orders = pd.DataFrame({"customer_id": [1, 1, 2], "order_date": ["2025-11-05", "2025-12-02", "2025-12-03"], "status": ["delivered"] * 3})
        result = cohorts(orders)
        november = result[(result.cohort == "2025-11") & (result.age_month == 1)]
        december = result[(result.cohort == "2025-12") & (result.age_month == 1)]
        self.assertEqual(november.retention.iloc[0], 1.0)
        self.assertTrue(np.isnan(december.retention.iloc[0]))

    def test_partial_month_is_not_counted_as_complete(self):
        orders = pd.DataFrame({"customer_id": [1, 1], "order_date": ["2025-11-05", "2025-12-02"], "status": ["delivered", "delivered"]})
        result = cohorts(orders, observed_through="2025-12-15")
        self.assertTrue(result.loc[(result.cohort == "2025-11") & (result.age_month == 1), "retention"].isna().all())


if __name__ == "__main__":
    unittest.main()
