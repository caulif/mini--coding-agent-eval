"""Public offline reproduction and termination accounting."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from examples.verify_experiment import verify
from evalcourse.report import markdown, summarize
from evalcourse.run import ROOT


class PublicWorkflowTests(unittest.TestCase):
    def test_original_records_reproduce_and_classify_every_stop(self):
        report, _, _ = verify(ROOT / "experiments/quixbugs-holdout-3")
        b = report["versions"]["B"]
        self.assertEqual(b["successes"], 13)
        self.assertEqual(b["termination_counts"], {"done": 13, "output_limit": 1, "agent_error": 1})
        self.assertIsNone(b["total_tokens"])
        self.assertIn("| B | output_limit | 1 |", markdown(report))

    def test_audit_rejects_missing_attempt_and_altered_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "batch"
            shutil.copytree(ROOT / "experiments/quixbugs-holdout-3", source)
            results = source / "results.jsonl"
            original = results.read_text(encoding="utf-8")
            results.write_text("\n".join(original.splitlines()[:-1]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "schedule"):
                verify(source)
            results.write_text(original, encoding="utf-8")
            report_path = source / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["versions"]["B"]["successes"] = 15
            report_path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "metrics"):
                verify(source)

    def test_done_is_not_necessarily_success_and_unknown_states_are_retained(self):
        rows = [{"task": "one", "version": v, "repeat": i, "slice": "s",
                 "status": status, "passed": False, "seconds": 1, "tokens": 2}
                for v in ("A", "B") for i, status in enumerate(("done", "budget", "filtered", "future_status"))]
        report = summarize(rows)
        self.assertEqual(sum(report["versions"]["A"]["termination_counts"].values()), 4)
        self.assertEqual(report["versions"]["A"]["successes"], 0)
        self.assertIn("future_status", markdown(report))
