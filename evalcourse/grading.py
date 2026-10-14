"""Execute a candidate against evaluator-owned checks in a fresh directory."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

# The candidate is Python code, not a safe expression. A subprocess is NOT a sandbox.
CHECKER = '''import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("candidate", "solution.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
results = []
for case in json.loads(sys.stdin.read()):
    try:
        actual = module.solve(case["input"])
        results.append({"passed": actual == case["expected"], "actual": repr(actual)[:300]})
    except Exception as error:
        results.append({"passed": False, "error": type(error).__name__})
with open("verdict.json", "w", encoding="utf-8") as file:
    json.dump(results, file)
'''


def check(source, cases):
    if not cases:
        raise ValueError("An empty test set cannot establish success")
    with tempfile.TemporaryDirectory(prefix="eval-grade-") as directory:
        root = Path(directory)
        (root / "solution.py").write_text(source, encoding="utf-8")
        env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "PATH", "TEMP", "TMP") if key in os.environ}
        try:
            # -I ignores Python startup customization and the parent's PYTHONPATH.
            process = subprocess.run([sys.executable, "-I", "-c", CHECKER], cwd=root,
                                     input=json.dumps(cases), text=True, encoding="utf-8",
                                     capture_output=True, timeout=3, env=env)
        except subprocess.TimeoutExpired:
            return {"passed": False, "status": "test_timeout", "checks": []}
        if process.returncode:
            return {"passed": False, "status": "candidate_error", "checks": []}
        try:
            rows = json.loads((root / "verdict.json").read_text(encoding="utf-8"))
            if len(rows) != len(cases) or any(type(row["passed"]) is not bool for row in rows):
                raise ValueError("Invalid verdict")
        except (OSError, ValueError, KeyError, TypeError):
            return {"passed": False, "status": "invalid_verdict", "checks": []}
        return {"passed": all(row["passed"] for row in rows), "status": "graded", "checks": rows}


def grade(source, task):
    target = check(source, task["target"])
    regression = check(source, task["regression"])
    return {"passed": target["passed"] and regression["passed"],
            "target": target, "regression": regression}
