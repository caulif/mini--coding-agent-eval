import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from evalcourse.judge import evaluate, judge
from evalcourse.report import summarize, markdown
from evalcourse.rejudge import rejudge
from evalcourse.run import trial, load_tasks


def response(content='{"passed": false, "reason": "No recorded test supports the claim."}', finish="stop"):
    return {"model": "judge-fixture", "choices": [{"finish_reason": finish,
            "message": {"role": "assistant", "content": content}}], "usage": {"total_tokens": 7}}


class JudgeTests(unittest.TestCase):
    def test_mini_agent_message_adapter(self):
        from examples.mini_agent_judge import judge_messages
        messages = [
            {"role":"user", "content":"Fix it"},
            {"role":"assistant", "tool_calls":[{"id":"t", "function":{"name":"bash", "arguments":'{"command":"python -m unittest"}'}}]},
            {"role":"tool", "tool_call_id":"t", "content":"FAILED"},
            {"role":"assistant", "content":"All tests passed"}]
        result=judge_messages(messages, completed=True, call=lambda _: response())
        self.assertFalse(result["passed"])
        self.assertEqual(result["evidence"]["tools"][0]["name"],"bash")
        self.assertEqual(judge_messages(messages, completed=False)["status"],"skipped")
        with self.assertRaises(ValueError): judge_messages(messages[:2], completed=True)

    def test_strict_verdict_and_finish(self):
        for content in ('[]', 'null', '{"passed":"false","reason":"x"}', '{"passed":true,"reason":" "}', 'not json', '{"passed":true,"reason":"x","tokens":0}'):
            with self.subTest(content=content), self.assertRaises((ValueError, TypeError)):
                judge("done", [], lambda _: response(content))
        for finish in ("length", "content_filter", None):
            with self.assertRaises(ValueError):
                judge("done", [], lambda _: response(finish=finish))

    def test_evidence_order_blinding_and_cost(self):
        events = [{"kind": "tool", "name": n, "arguments": "{}", "result": r}
                  for n, r in (("test", {"passed": False}), ("write", "written"), ("test", {"passed": True}))]
        events.append({"kind": "grade", "result": {"passed": True, "hidden": "not agent evidence"}})
        seen = []
        def call(messages):
            seen.append(messages)
            return response('{"passed":true,"reason":"Record 3 verifies the latest edit."}')
        row = {"status": "done", "final": "Public tests passed.", "version": "B", "tokens": 100}
        score = evaluate(row, events, call)
        evidence = json.loads(seen[0][1]["content"])
        self.assertEqual(list(evidence), ["final", "tools"])
        self.assertEqual([e["name"] for e in evidence["tools"]], ["test", "write", "test"])
        self.assertNotIn("hidden", json.dumps(evidence))
        self.assertEqual(score["tokens"], 7)
        self.assertEqual(row["tokens"], 100)
        self.assertEqual(score["status"], "ok")

    def test_skip_and_errors_never_pass(self):
        for row in ({"status": "budget", "final": "partial"}, {"status": "done", "final": " "}):
            self.assertEqual(evaluate(row, [], lambda _: self.fail("Should not call judge"))["status"], "skipped")
        row = {"status": "done", "final": "done"}
        result = evaluate(row, [], lambda _: response('[]'))
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["passed"])
        self.assertEqual(result["tokens"], 7)
        def broken(_):
            raise RuntimeError("secret-provider-body")
        result = evaluate(row, [], broken)
        self.assertNotIn("secret-provider-body", json.dumps(result))
        self.assertIsNone(result["tokens"])

    def test_trial_keeps_function_and_judge_separate(self):
        task = load_tasks("dev")[0]
        def agent(public, root, prompt, turns, emit):
            (root / "solution.py").write_text(json.loads((Path(__file__).parent / "oracles.json").read_text(encoding="utf-8"))[task["id"]], encoding="utf-8")
            return {"status": "done", "final": "All tests passed", "tokens": 20}
        with tempfile.TemporaryDirectory() as directory, patch("evalcourse.judge.complete", return_value=response()), patch.dict(os.environ, {"EVAL_MODEL": "fixture"}):
            row = trial(task, "A", 0, "prompt", Path(directory), 2, agent, with_judge=True)
            self.assertTrue(row["passed"])
            self.assertFalse(row["judge"]["passed"])
            self.assertEqual(row["tokens"], 20)
            self.assertEqual(json.loads((Path(directory)/"result.json").read_text())["judge"]["tokens"], 7)

    def test_report_denominators_and_old_rows(self):
        rows = [{"task": "one", "slice": "s", "version": v, "repeat": i, "status": "done",
                 "passed": True, "seconds": 1, "tokens": 10} for v in ("A", "B") for i in range(4)]
        for offset in (0, 4):
            rows[offset]["judge"] = {"status": "ok", "passed": False, "tokens": 7, "seconds": 2}
            rows[offset+1]["judge"] = {"status": "error", "passed": None, "tokens": None}
            rows[offset+2]["judge"] = {"status": "skipped", "passed": None, "tokens": 0}
        report = summarize(rows)
        j = report["versions"]["A"]["judge"]
        self.assertEqual((j["scored"], j["passed"], j["errors"], j["skipped"], j["not_requested"]), (1, 0, 1, 1, 1))
        self.assertIsNone(j["tokens"])
        self.assertEqual(report["versions"]["A"]["total_tokens"], 40)
        self.assertIn("0/1", markdown(report))

    def test_rejudge_preserves_source_and_rejects_incomplete_input(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"EVAL_MODEL": "fixture"}):
            root=Path(directory); source=root/"source"; source.mkdir()
            rows=[]; schedule=[]
            for index,v in enumerate(("A","B")):
                row={"task":"one","version":v,"repeat":0,"slice":"s","status":"done","final":"done","passed":True,"seconds":1,"tokens":2}
                rows.append(row); schedule.append(["one",v,0])
                trial_dir=source/f"{index:03d}-one-{v}-0"; trial_dir.mkdir()
                (trial_dir/"result.json").write_text(json.dumps(row))
                (trial_dir/"trace.jsonl").write_text(json.dumps({"kind":"grade","result":True})+'\n')
            (source/"manifest.json").write_text(json.dumps({"status":"complete","schedule":schedule}))
            (source/"results.jsonl").write_text('\n'.join(map(json.dumps,rows)))
            before={p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()}
            out=root/"review"
            report=rejudge(source,out,lambda _:response())
            self.assertEqual(report["versions"]["A"]["judge"]["scored"],1)
            self.assertEqual(before,{p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()})
            self.assertEqual(json.loads((out/"manifest.json").read_text())["kind"],"posthoc_judge")
            with self.assertRaises(FileExistsError): rejudge(source,out,lambda _:self.fail("No paid calls"))
            with self.assertRaises(ValueError): rejudge(source,source/"child")
            (source/"results.jsonl").write_text(json.dumps(rows[0]))
            with self.assertRaises(ValueError): rejudge(source,root/"bad",lambda _:self.fail("No paid calls"))
            self.assertFalse((root/"bad").exists())
