import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import workflow


class WorkflowTests(unittest.TestCase):
    def evaluate(self, candidate, opportunity, today="2026-10-22"):
        return workflow.evaluate_opportunity(candidate, opportunity, date.fromisoformat(today))

    def test_unknown_country_needs_verification(self):
        result = self.evaluate({"age": 22, "country": "", "interests": []}, {"eligibility": {"countries": ["US"]}})
        self.assertEqual(result["eligibility_status"], "Needs verification")
        self.assertTrue(any("country" in r.lower() for r in result["eligibility_reasons"]))

    def test_country_mismatch_is_not_eligible(self):
        result = self.evaluate({"age": 22, "country": "CA", "interests": []}, {"eligibility": {"countries": ["US"]}})
        self.assertEqual(result["eligibility_status"], "Not eligible")

    def test_missing_age_is_not_assumed_eligible(self):
        result = self.evaluate({"country": "US", "interests": []}, {"eligibility": {"min_age": 18}})
        self.assertEqual(result["eligibility_status"], "Needs verification")

    def test_expired_deadline_is_detected(self):
        result = self.evaluate({"age": 22, "country": "US", "interests": []}, {"deadline": "2026-10-21"})
        self.assertTrue(result["expired"])
        self.assertEqual(result["urgency"], "Expired")

    def test_duplicate_urls_keep_first_normalized_record(self):
        records = workflow.deduplicate_by_url([
            {"name": "First", "url": "https://example.org/opportunity/"},
            {"name": "Duplicate", "url": "https://example.org/opportunity"},
        ])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["name"], "First")

    def test_missing_country_requirement_is_not_assumed_known(self):
        result = self.evaluate({"age": 22, "country": "US", "interests": []}, {"eligibility": {"min_age": 18}})
        self.assertEqual(result["eligibility_status"], "Needs verification")
        self.assertTrue(any("country eligibility is not specified" in r.lower() for r in result["eligibility_reasons"]))

    def test_report_ranks_and_normalizes_inputs(self):
        report = workflow.build_report(
            {"age": 21, "country": "US", "interests": ["robotics"]},
            [{"title": "Robotics Lab", "type": "internship", "url": "https://example.org/robotics", "deadline": "2026-11-10", "interests": ["robotics"], "eligibility": {"countries": ["US"]}}],
            today=date(2026, 10, 22),
        )
        self.assertEqual(report["opportunities"][0]["name"], "Robotics Lab")
        self.assertEqual(report["opportunities"][0]["interest_score"], 1)
        self.assertEqual(report["opportunities"][0]["eligibility_status"], "Potential match")


if __name__ == "__main__":
    unittest.main()
