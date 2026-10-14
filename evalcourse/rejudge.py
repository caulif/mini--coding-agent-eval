"""Regrade a complete saved batch without rerunning agents or changing source records."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from .judge import configuration, evaluate
from .report import summarize, markdown


def rejudge(source, out, call=None):
    source, out = Path(source).resolve(), Path(out).resolve()
    if out == source or source in out.parents:
        raise ValueError("Use a new output directory outside the source batch")
    def read(name):
        return json.loads((source / name).read_text(encoding="utf-8"))
    manifest = read("manifest.json")
    if manifest["status"] != "complete":
        raise ValueError("Source batch is incomplete")
    rows = [json.loads(line) for line in (source / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    schedule = manifest["schedule"]
    identities = [(r["task"], r["version"], r["repeat"]) for r in rows]
    if identities != [tuple(item) for item in schedule]:
        raise ValueError("Results do not match the complete schedule")
    summarize(rows)  # Validate pairing and duplicate identities before any paid calls.
    inputs, hashes = [], {}
    for index, (task, version, repeat) in enumerate(schedule):
        if not isinstance(task, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", task) or version not in ("A", "B") or type(repeat) is not int or repeat < 0:
            raise ValueError("Invalid trial identity")
        directory = f"{index:03d}-{task}-{version}-{repeat}"
        if read(f"{directory}/result.json") != rows[index]:
            raise ValueError("Trial result differs from batch row")
        path = source / directory / "trace.jsonl"
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        # Validate evidence shape before creating output or making a request.
        for event in events:
            if event.get("kind") == "tool":
                for key in ("name", "arguments", "result"):
                    if key not in event:
                        raise ValueError("Incomplete tool evidence")
        inputs.append(events)
        hashes[f"{directory}/trace.jsonl"] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ("manifest.json", "results.jsonl"):
        hashes[name] = hashlib.sha256((source / name).read_bytes()).hexdigest()
    meta = {"status": "running", "kind": "posthoc_judge", "source": str(source),
            "source_sha256": hashes, "schedule": schedule, "judge": configuration(),
            "code_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob("*.py")}}
    out.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    save("manifest.json", meta)
    with (out / "results.jsonl").open("x", encoding="utf-8") as stream:
        for row, events in zip(rows, inputs):
            row["judge"] = evaluate(row, events, call)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
    report = summarize(rows)
    save("report.json", report)
    (out / "report.md").write_text(markdown(report), encoding="utf-8")
    meta["status"] = "complete"
    save("manifest.json", meta)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if not os.environ.get("EVAL_API_KEY") or not (os.environ.get("EVAL_JUDGE_MODEL") or os.environ.get("EVAL_MODEL")):
        parser.error("Set EVAL_API_KEY and EVAL_JUDGE_MODEL (or EVAL_MODEL)")
    rejudge(args.source, args.out)
    print(args.out / "report.md")


if __name__ == "__main__":
    main()
