"""Paired task-level comparison. Keep errors in the planned denominator."""
import random
import statistics as stats
from collections import Counter


def judge_summary(rows):
    judgments = [r.get("judge", {"status": "not_requested"}) for r in rows]
    scored = [j for j in judgments if j["status"] == "ok"]
    tokens = [j.get("tokens", 0) for j in judgments]
    return {"scored": len(scored), "passed": sum(j["passed"] for j in scored),
            "pass_rate": stats.mean(j["passed"] for j in scored) if scored else None,
            "errors": sum(j["status"] == "error" for j in judgments),
            "skipped": sum(j["status"] == "skipped" for j in judgments),
            "not_requested": sum(j["status"] == "not_requested" for j in judgments),
            "seconds": sum(j.get("seconds", 0) for j in judgments),
            "tokens": sum(tokens) if all(t is not None for t in tokens) else None}


def summarize(rows):
    versions = {}
    rates = {}
    for version in ("A", "B"):
        selected = [row for row in rows if row["version"] == version]
        if not selected:
            raise ValueError("Both versions are required")
        grouped = {}
        for row in selected:
            grouped.setdefault(row["task"], []).append(row)
        rates[version] = {key: stats.mean(r["passed"] for r in group) for key, group in grouped.items()}
        versions[version] = {"trials": len(selected), "successes": sum(r["passed"] for r in selected),
            "success_rate": stats.mean(r["passed"] for r in selected),
            "any_success": stats.mean(any(r["passed"] for r in group) for group in grouped.values()),
            "all_success": stats.mean(all(r["passed"] for r in group) for group in grouped.values()),
            "agent_errors": sum(r["status"] == "agent_error" for r in selected),
            "budget_stops": sum(r["status"] == "budget" for r in selected),
            "functional_successes": sum(r.get("functional_pass", r["passed"]) for r in selected),
            "mean_tools": stats.mean(r["tools"] for r in selected) if all("tools" in r for r in selected) else None,
            "mean_seconds": stats.mean(r["seconds"] for r in selected),
            "total_tokens": sum(r["tokens"] for r in selected) if all(r["tokens"] is not None for r in selected) else None,
            "slices": {tag: stats.mean(r["passed"] for r in selected if r["slice"] == tag) for tag in sorted({r["slice"] for r in selected})}}
        versions[version]["judge"] = judge_summary(selected)
        versions[version]["termination_counts"] = dict(sorted(Counter(r["status"] for r in selected).items()))
    ids = sorted(rates["A"])
    if ids != sorted(rates["B"]):
        raise ValueError("Task sets differ")
    identities = [(r["task"], r["version"], r["repeat"]) for r in rows]
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate trial")
    repeats = {tuple(sorted(r["repeat"] for r in rows if r["task"] == key and r["version"] == v)) for key in ids for v in ("A", "B")}
    if len(repeats) != 1:
        raise ValueError("Unequal repeat sets")
    differences = {key: rates["B"][key] - rates["A"][key] for key in ids}
    rng = random.Random(0)
    samples = sorted(stats.mean(rng.choice(list(differences.values())) for _ in ids) for _ in range(2000))
    return {"versions": versions, "repeats": len(next(iter(repeats))), "per_task_delta": differences,
            "delta": stats.mean(differences.values()), "task_bootstrap_95": [samples[50], samples[1949]],
            "warning": "Tiny convenience sample: descriptive evidence, not a general capability claim. Bootstrap resamples tasks; it does not fully model within-task stochasticity."}


def markdown(report):
    lines = ["# Prompt A/B report", "", "| Version | Passed / trials | Rate | Any / all | Mean seconds | Tokens | Agent exceptions |", "|---|---:|---:|---:|---:|---:|---:|"]
    for name, v in report["versions"].items():
        lines.append(f'| {name} | {v["successes"]}/{v["trials"]} | {v["success_rate"]:.1%} | {v["any_success"]:.1%} / {v["all_success"]:.1%} | {v["mean_seconds"]:.2f} | {v["total_tokens"]} | {v["agent_errors"]} |')
    lines += ["", f'Repeats per task: {report["repeats"]}', f'B − A: {report["delta"]:+.1%}', f'Task bootstrap interval: {report["task_bootstrap_95"]}', "", report["warning"], "", "## Per-task changes"]
    lines += [f"- {key}: {value:+.1%}" for key, value in report["per_task_delta"].items()]
    lines += ["", "## Verification claims (separate from task success)", "",
              "| Version | Passed / scored | Errors | Skipped | Not requested | Judge seconds | Judge tokens |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for name, v in report["versions"].items():
        j = v.get("judge")
        if j:
            lines.append(f'| {name} | {j["passed"]}/{j["scored"]} | {j["errors"]} | {j["skipped"]} | {j["not_requested"]} | {j["seconds"]:.2f} | {j["tokens"]} |')
    lines += ["", "Only valid judge verdicts enter the scored denominator. Errors/skips are not passes; inspect coverage and calibration before comparing rates."]
    lines += ["", "## Agent termination states", "", "| Version | State | Count |", "|---|---|---:|"]
    for name, v in report["versions"].items():
        for status, count in v.get("termination_counts", {}).items():
            lines.append(f"| {name} | {status} | {count} |")
    lines += ["", "done = normal completion (not necessarily functional success); budget = turn limit; output_limit = response token limit; agent_error = request/execution exception; filtered = provider content filter. Unknown token totals remain None."]
    return "\n".join(lines) + "\n"
