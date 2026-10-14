"""Offline record audit: python -m examples.verify_experiment [BATCH]. No model calls."""
import argparse
import json
from pathlib import Path
import re
from evalcourse.report import summarize, markdown
from evalcourse.run import ROOT, digest


def verify(source):
    source = Path(source)
    def read(name):
        return json.loads((source / name).read_text(encoding="utf-8"))
    manifest = read("manifest.json")
    if manifest["status"] != "complete":
        raise ValueError("Batch is incomplete")
    rows = [json.loads(s) for s in (source / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    if [[r["task"], r["version"], r["repeat"]] for r in rows] != manifest["schedule"]:
        raise ValueError("Rows do not match the planned schedule")
    tasks = read("tasks.snapshot.json")
    if digest(json.dumps(tasks, sort_keys=True)) != manifest["task_sha256"]:
        raise ValueError("Task snapshot hash mismatch")
    task_ids = {t["id"] for t in tasks}
    for i, row in enumerate(rows):
        task, version, repeat = row["task"], row["version"], row["repeat"]
        if task not in task_ids or not re.fullmatch(r"[A-Za-z0-9_-]+", task) or version not in ("A", "B") or type(repeat) is not int or repeat < 0:
            raise ValueError("Invalid trial identity")
        directory = f"{i:03d}-{task}-{version}-{repeat}"
        if read(f"{directory}/result.json") != row:
            raise ValueError("Trial result differs from batch row")
        if not (source / directory / "solution.py").is_file():
            raise ValueError("Missing candidate source")
        events = [json.loads(s) for s in (source / directory / "trace.jsonl").read_text(encoding="utf-8").splitlines()]
        grades = [e["result"] for e in events if e.get("kind") == "grade"]
        if grades != [row["grade"]] or row["functional_pass"] != row["grade"]["passed"]:
            raise ValueError("Grade evidence differs from result")
        if row["passed"] != (row["functional_pass"] and row["status"] == "done"):
            raise ValueError("Incorrect delivery verdict")
    report = summarize(rows)
    def compare(saved, current):
        # New diagnostic fields may be added without rewriting historical reports.
        if isinstance(saved, dict):
            return isinstance(current, dict) and all(k in current and compare(v, current[k]) for k, v in saved.items())
        return saved == current
    if not compare(read("report.json"), report):
        raise ValueError("Saved report does not match recomputed metrics")
    changed = [name for name, expected in manifest["code_sha256"].items()
               if not (ROOT / "evalcourse" / name).is_file()
               or digest((ROOT / "evalcourse" / name).read_text(encoding="utf-8")) != expected]
    changed_prompts = [v for v, text in manifest["prompts"].items()
                       if v not in ("A", "B") or (ROOT / "prompts" / f"{v}.txt").read_text(encoding="utf-8") != text]
    return report, changed, changed_prompts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=ROOT / "experiments/quixbugs-holdout-3")
    args = parser.parse_args()
    report, changed, prompts = verify(args.source)
    print("PASS: schedule, task snapshot, trial records, grade evidence and saved metrics agree.")
    print("Current code differs from recorded hashes:", ", ".join(changed) or "none")
    print("Current prompts differ from recorded texts:", ", ".join(prompts) or "none")
    print("Record consistency only; candidate code is not executed, and historical model outputs are not regenerated.")
    print(markdown(report))


if __name__ == "__main__":
    main()
