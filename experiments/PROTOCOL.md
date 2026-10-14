# QuixBugs prompt experiment protocol

**English translation** | [Original Chinese protocol](PROTOCOL.zh-CN.md)

The original protocol was set on 2026-10-14 before the model pilot. This English translation was added afterward; it does not retroactively establish a new preregistration. The twenty-four older `deepseek-dev-3` records remain separate.

## Question and hypothesis

Does B's instruction to reproduce, verify, add useful boundary cases, and report honestly improve small algorithm repairs with identical tools? Possible outcomes include higher success, more verification, no benefit, or increased cost. B is not required to win.

## Fixed design

- Three development tasks, one attempt per version each, checking interfaces, budgets, and failures; excluded from the final denominator.
- Five final tasks, three attempts per A/B version, thirty total: `--seed 0 --turns 6 --repeats 3 --judge`.
- Requested model `deepseek/deepseek-v4.1-flash`, temperature zero, 2048 tokens per response. Actual response model names are retained in traces.
- Identical read/write/test tools, including `test(cases=...)`. B changes instructions only, not tools, model, or budget.
- Fresh directory and initial source every attempt. Pair by task/repeat, randomize A/B order, and interleave. The seed does not control provider generation randomness.
- Primary metric: independent functional acceptance plus normal completion. Also report functional results, termination, calls, tokens, and time.
- Predefined auxiliary grader: verification claims, separate from primary success. Freeze the rubric and retain raw responses, rationale, and status. Errors/skips are not passes. Without independent human-label calibration, these findings are diagnostic.
- Retain all planned attempts, including errors. Record environment failures; any repaired full rerun gets a new directory, without replacing failures or selecting favorable attempts.
- Final maximum: 180 agent requests plus thirty judge requests. Development maximum: 36 plus six. Thirty-second request timeout; no automatic retries.

## Interpretation rules

Report per-task A/B successes, B−A, costs, judge coverage, and trace examples. Repeats of the same problem are not new independent tasks. The task bootstrap is descriptive; a degenerate interval cannot prove equivalence. Results concern only these five small repairs under the specified model, tools, and budget. Training contamination is unknown.

If both versions pass, report no observed functional benefit while examining behavior and cost. Report regressions equally plainly. Do not tune B after inspecting holdout results and continue calling that evaluation unseen.
