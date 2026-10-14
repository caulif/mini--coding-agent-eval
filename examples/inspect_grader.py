"""python -m examples.inspect_grader: evaluate real task assets without a model."""
import json
from evalcourse.grading import grade
from evalcourse.run import ROOT, load_tasks

task = load_tasks("dev")[0]  # The same knapsack task used by the experiment.
reference = json.loads((ROOT / "tests/oracles.json").read_text(encoding="utf-8"))[task["id"]]
bad_repair = "def solve(v): return max([0]+[price for weight,price in v['items'] if weight <= v['capacity']])"
for label, source in [("starter", task["source"]), ("reference", reference), ("one-item-only", bad_repair)]:
    result = grade(source, task)
    print(label, {key: value["passed"] for key, value in result.items() if isinstance(value, dict)})
