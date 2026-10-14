# Experiment records

**English** | [简体中文](README.zh-CN.md)

Original batches retain all planned attempts. Audits read existing evidence; reruns and post-hoc assessments are separate records. Later successes never replace original failures.

| Record | Purpose | Included in the article's primary conclusion |
| --- | --- | --- |
| [quixbugs-dev-1](quixbugs-dev-1/report.md) | Three development tasks, one A/B pair each | No |
| [quixbugs-holdout-3](quixbugs-holdout-3/analysis.en.md) | Five final tasks, three A/B pairs each; thirty attempts | Yes: A 15/15, B 13/15 |
| [quixbugs-missing-followup-1](quixbugs-missing-followup-1/README.md) | Targeted single follow-up attempts for missing observations | No replacement of original denominators, cost, or missingness |

## Audit the current experiment

From the repository root, run `python -m examples.verify_experiment`. No API key, model call, or candidate execution is needed. The audit checks record consistency and recomputes metrics, retaining errors, missing verdicts, and unknown usage.

The [protocol](PROTOCOL.md) fixes hypotheses, model, budgets, and denominators. [Task construction](../data/README.md) explains provenance and adaptation. Manifests preserve actual settings; source hashes identify changes but are not recoverable source archives.

For English descriptions of the recorded inputs, see [task contracts](../data/TASKS.md).


## Evidence and language

The final batch used a real model and observed no repair-delivery benefit for B. Its two unsuccessful deliveries stopped at the response limit and at a first-request HTTPError. These failures remain useful design feedback.

Public algorithm problems may have appeared in model training. Holdout means unused during this prompt-development process, not unseen by the model. Traces retain response model names, usage, and termination. Timing depends on the host and network; tokens are not invoice amounts. The judge lacks independent human calibration.

Default indexes and explanatory summaries are English. Raw task prompts, model replies, and preserved original analyses retain their source language. English companion translations are labeled explicitly; translating a request changes experimental conditions, while rewriting a response changes evidence.
