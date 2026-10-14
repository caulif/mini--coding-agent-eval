"""python -m evalcourse.run --split dev --repeats 3"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile
import time
from .agent import run_agent
from .grading import grade
from .report import summarize, markdown
from .judge import evaluate, configuration

ROOT = Path(__file__).resolve().parents[1]


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_tasks(split):
    tasks = json.loads((ROOT / "tasks.json").read_text(encoding="utf-8"))
    if len({t["id"] for t in tasks}) != len(tasks):
        raise ValueError("Duplicate task id")
    return [task for task in tasks if task["split"] == split]


def trial(task, version, repeat, prompt, directory, turns, call_agent=run_agent, with_judge=False):
    started = time.perf_counter()
    with (directory / "trace.jsonl").open("x", encoding="utf-8") as trace:
        def emit(kind, **fields):
            trace.write(json.dumps({"kind": kind, "seconds": time.perf_counter() - started, **fields}, ensure_ascii=False) + "\n")
            trace.flush()
        with tempfile.TemporaryDirectory(prefix="eval-work-") as workspace:
            root = Path(workspace)
            (root / "solution.py").write_text(task["source"], encoding="utf-8")
            # Only the public projection crosses the agent interface.
            public = {key: task[key] for key in ("prompt", "public")}
            try:
                run = call_agent(public, root, prompt, turns, emit)
            except Exception as error:
                # Exception messages may contain provider response bodies; record type only.
                run = {"status": "agent_error", "error_type": type(error).__name__, "tokens": None}
                emit("agent_error", error_type=type(error).__name__)
            seconds = time.perf_counter() - started
            source = (root / "solution.py").read_text(encoding="utf-8")
            (directory / "solution.py").write_text(source, encoding="utf-8")
            result = grade(source, task)
            emit("grade", result=result)
    row = {"task": task["id"], "slice": task["slice"], "version": version, "repeat": repeat,
           **run, "seconds": seconds, "functional_pass": result["passed"],
           "passed": result["passed"] and run["status"] == "done", "grade": result}
    if with_judge:
        events = [json.loads(line) for line in (directory / "trace.jsonl").read_text(encoding="utf-8").splitlines()]
        row["judge"] = evaluate(row, events)
    (directory / "result.json").write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["dev", "holdout"], default="dev")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--turns", type=int, default=6)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--tasks", nargs="+", help="Select task IDs within the chosen split")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--judge", action="store_true", help="Also grade verification claims with one LLM call")
    args = parser.parse_args()
    if not (1 <= args.repeats <= 20 and 1 <= args.turns <= 20):
        parser.error("repeats and turns must be between 1 and 20")
    for key in ("EVAL_MODEL", "EVAL_API_KEY"):
        if not os.environ.get(key):
            parser.error(f"Set {key}; use python -m unittest discover -s tests for offline checks")
    tasks = load_tasks(args.split)
    if args.tasks:
        if not set(args.tasks) <= {task["id"] for task in tasks}:
            parser.error("Unknown task ID for this split")
        tasks = [task for task in tasks if task["id"] in args.tasks]
    prompts = {v: (ROOT / "prompts" / f"{v}.txt").read_text(encoding="utf-8") for v in ("A", "B")}
    out = args.out or ROOT / "runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out.mkdir(parents=True, exist_ok=False)
    (out / "tasks.snapshot.json").write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    schedule, rng = [], random.Random(args.seed)
    for task in tasks:
        for repeat in range(args.repeats):
            versions = ["A", "B"]
            rng.shuffle(versions)
            schedule.extend((task["id"], v, repeat) for v in versions)
    manifest = {"status": "running", "model": os.environ["EVAL_MODEL"], "temperature": 0,
        "max_tokens_per_response": 2048, "turns": args.turns, "repeats": args.repeats, "split": args.split,
        "seed": args.seed, "schedule": schedule, "prompts": prompts,
        "task_sha256": digest(json.dumps(tasks, sort_keys=True)),
        "code_sha256": {p.name: digest(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "evalcourse").glob("*.py"))}}
    manifest["judge"] = configuration() if args.judge else None
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    rows, by_id = [], {task["id"]: task for task in tasks}
    with (out / "results.jsonl").open("x", encoding="utf-8") as stream:
        for index, (task_id, version, repeat) in enumerate(schedule):
            directory = out / f"{index:03d}-{task_id}-{version}-{repeat}"
            directory.mkdir()
            row = trial(by_id[task_id], version, repeat, prompts[version], directory, args.turns, with_judge=args.judge)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
            rows.append(row)
            print(task_id, version, repeat, row["status"], row["passed"], flush=True)
    report = summarize(rows)
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out / "report.md").write_text(markdown(report), encoding="utf-8")
    manifest["status"] = "complete"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out / "report.md")


if __name__ == "__main__":
    main()
