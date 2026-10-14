import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from evalcourse.agent import run_agent
from evalcourse.client import complete
from evalcourse.grading import check, grade
from evalcourse.judge import calibrate, judge
from evalcourse.report import summarize
from evalcourse.run import ROOT, load_tasks, trial, main

ORACLES = json.loads((ROOT / "tests/oracles.json").read_text(encoding="utf-8"))


class EvaluationTests(unittest.TestCase):
    def test_all_task_baselines_and_oracles(self):
        for task in load_tasks("dev") + load_tasks("holdout"):
            with self.subTest(task=task["id"]):
                baseline = grade(task["source"], task)
                self.assertFalse(baseline["target"]["passed"])
                # A real broken algorithm may also fail broad contract checks.
                self.assertTrue(grade(ORACLES[task["id"]], task)["passed"])
                self.assertTrue(check(ORACLES[task["id"]], task["public"])["passed"])

    def test_partial_fix_and_syntax_error_fail(self):
        task = load_tasks("dev")[0]
        self.assertFalse(grade("def solve(value): return max([0]+[v for w,v in value['items'] if w <= value['capacity']])", task)["passed"])
        self.assertEqual(check("this is not python!", task["public"])["status"], "candidate_error")

    def test_timeout_and_empty_checks(self):
        with self.assertRaises(ValueError):
            check("", [])
        self.assertEqual(check("while True: pass", [{"input": 1, "expected": 1}])["status"], "test_timeout")

    def test_candidate_does_not_inherit_api_key(self):
        with patch.dict(os.environ, {"EVAL_API_KEY": "test-secret"}):
            result = check("import os\ndef solve(x): return os.environ.get('EVAL_API_KEY')", [{"input": None, "expected": None}])
        self.assertTrue(result["passed"])

    def test_fresh_trials_public_projection_and_budget(self):
        task = load_tasks("dev")[0]
        observed = []
        def fake(public, root, prompt, turns, emit):
            self.assertEqual(set(public), {"prompt", "public"})
            observed.append((root / "solution.py").read_text(encoding="utf-8"))
            (root / "solution.py").write_text(ORACLES[task["id"]], encoding="utf-8")
            return {"status": "budget", "tokens": 4}
        with tempfile.TemporaryDirectory() as directory:
            for repeat in range(2):
                dest = Path(directory) / str(repeat)
                dest.mkdir()
                row = trial(task, "A", repeat, "prompt", dest, 2, fake)
                self.assertTrue(row["functional_pass"])
                self.assertFalse(row["passed"])
        self.assertEqual(observed, [task["source"], task["source"]])

    def test_error_retained_and_message_redacted(self):
        def broken(*args):
            raise RuntimeError("test-secret")
        with tempfile.TemporaryDirectory() as directory:
            row = trial(load_tasks("dev")[0], "B", 0, "prompt", Path(directory), 2, broken)
            self.assertEqual(row["status"], "agent_error")
            self.assertNotIn("test-secret", (Path(directory) / "trace.jsonl").read_text())

    def rows(self):
        return [{"task": task, "slice": "test", "version": v, "repeat": r,
                 "passed": v == "B", "status": "done", "seconds": 1, "tokens": 10}
                for task in ("one", "two") for v in ("A", "B") for r in range(3)]

    def test_report_pairing_and_denominator(self):
        rows = self.rows()
        rows[1].update(status="agent_error", tokens=None)
        report = summarize(rows)
        self.assertEqual(report["versions"]["A"]["trials"], 6)
        self.assertIsNone(report["versions"]["A"]["total_tokens"])
        self.assertEqual(report["delta"], 1)
        self.assertEqual(report["task_bootstrap_95"], [1, 1])
        for bad in (rows[:-1], rows + rows[:1]):
            with self.assertRaises(ValueError):
                summarize(bad)

    def test_judge_and_failure_recall(self):
        score = calibrate([True, False, False], [True, True, False])
        self.assertEqual(score["failure_recall"], 0.5)
        self.assertIsNone(calibrate([True], [True])["failure_recall"])
        with self.assertRaises(ValueError):
            judge("done", [], lambda *a: {"choices": [{"message": {"content": '{"passed":"yes","reason":"x"}'}}]})

    def test_http_tool_loop_and_cli(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append(payload)
                count = sum(m["role"] == "assistant" for m in payload["messages"])
                # Scripted protocol fixture, NOT an intelligent agent or A/B finding.
                calls = [
                    {"id": "r", "type": "function", "function": {"name": "read", "arguments": "{}"}},
                    {"id": "w", "type": "function", "function": {"name": "write", "arguments": json.dumps({"content": ORACLES["knapsack"]})}},
                    {"id": "t", "type": "function", "function": {"name": "test", "arguments": "{}"}},
                ]
                message = {"role": "assistant", "content": "done" if count >= 3 else None}
                if count < 3:
                    message["tool_calls"] = [calls[count]]
                if payload["messages"][0]["content"].startswith("Judge only"):
                    message = {"role": "assistant", "content": json.dumps({"passed": True, "reason": "No unsupported verification claim."})}
                body = json.dumps({"model": payload["model"], "choices": [{"finish_reason": "stop", "message": message}], "usage": {"total_tokens": 12}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ, {"EVAL_BASE_URL": f"http://127.0.0.1:{server.server_port}/v1", "EVAL_API_KEY": "fixture", "EVAL_MODEL": "fixture"}):
                with tempfile.TemporaryDirectory() as directory:
                    dest = Path(directory)
                    row = trial(load_tasks("dev")[0], "A", 0, "system-A", dest, 5)
                    self.assertTrue(row["passed"])
                    self.assertEqual(row["tools"], 3)
                    self.assertEqual(row["tokens"], 48)
                    self.assertTrue(all(p["messages"][0]["content"] == "system-A" for p in requests))
                    out = dest / "batch"
                    with patch("sys.argv", ["run", "--repeats", "1", "--judge", "--out", str(out)]), patch("evalcourse.run.load_tasks", return_value=load_tasks("dev")[:1]):
                        main()
                    manifest = json.loads((out / "manifest.json").read_text())
                    self.assertEqual(manifest["status"], "complete")
                    self.assertEqual(len(manifest["schedule"]), 2)
                    self.assertTrue((out / "report.md").exists())
                    self.assertEqual(json.loads((out / "tasks.snapshot.json").read_text(encoding="utf-8")), load_tasks("dev")[:1])
                    self.assertEqual(manifest["judge"]["criterion"], "verification_claims")
                    report = json.loads((out / "report.json").read_text())
                    self.assertEqual(report["versions"]["A"]["judge"]["scored"], 1)
                    self.assertEqual(report["versions"]["A"]["total_tokens"], 48)
                    from evalcourse.rejudge import main as rejudge_main
                    review = dest / "review"
                    with patch.dict(os.environ, {"EVAL_JUDGE_MODEL": "review-model"}), patch("sys.argv", ["rejudge", str(out), "--out", str(review)]):
                        rejudge_main()
                    self.assertEqual(requests[-1]["model"], "review-model")
                    self.assertNotIn("tools", requests[-1])
                    self.assertEqual(json.loads((review / "manifest.json").read_text())["status"], "complete")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_endpoint_policy(self):
        for base in ("http://example.com/v1", "https://user:password@example.com/v1", "https://example.com/v1?key=secret"):
            with patch.dict(os.environ, {"EVAL_BASE_URL": base}):
                with self.assertRaises(ValueError):
                    complete([])

    def test_truncated_output_is_not_completion(self):
        def truncated(*args):
            return {"choices": [{"finish_reason": "length", "message": {"role": "assistant", "content": "partial"}}]}
        with tempfile.TemporaryDirectory() as directory:
            result = run_agent({"prompt": "task"}, Path(directory), "system", 2, lambda *a, **k: None, truncated)
            self.assertEqual(result["status"], "output_limit")
            self.assertIsNone(result["tokens"])


if __name__ == "__main__":
    unittest.main()
