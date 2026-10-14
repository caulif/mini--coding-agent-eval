# mini coding agent eval

**English** | [简体中文](README.zh-CN.md)

An exploration of agent evaluation, from concepts and implementation to real experiments.

**After changing a coding agent's system prompt, does it actually get better at fixing code?** I wanted a project small enough to inspect, yet substantial enough to retain real problems. This repository records my ideas, design choices, and results: defining evaluation goals, constructing tasks, combining programmatic grading with an LLM judge, and comparing two prompts.

The experiment did not show a repair benefit from the new prompt. It exposed issues with response budgets, verification claims, and missing judge verdicts. Those findings are the starting point for further work. Code and original records are included for inspection and discussion.

Read the article in [English HTML](guide.html) or [中文 HTML](guide.zh-CN.html). HTML files open locally after cloning or downloading; GitHub displays their source, and no public website has been deployed.

## Design choices

- Eight algorithm-repair tasks from a pinned QuixBugs revision: three development tasks and five holdout tasks. Original code, MIT licensing, reference repairs, independent expectations, and rejected wrong repairs are traceable.
- One minimal coding agent with read, write, and test. `test()` runs public cases; `test(cases=...)` accepts one to eight small authored cases. Both prompts have identical tools.
- Every attempt starts in a fresh directory. Final acceptance reruns independent checks; agent-authored expectations are feedback, not acceptance criteria.
- Primary success requires functional acceptance and normal completion. An optional LLM judge separately assesses verification claims and retains its evidence, errors, and resource use.
- A/B trials are paired by task/repeat and interleaved. All planned attempts remain; successful retries do not replace inconvenient failures.

These tasks adapt a public algorithm benchmark, not industrial repository issues. Provenance does not establish difficulty or absence from model training. Conclusions remain tied to tasks and conditions. Original task prompts are in Chinese; translating them would change the experiment, so this documentation update preserves them and all raw records.

## Run and inspect

Run commands from the repository root with Python 3.12, the currently supported and verified version. Runtime code uses only the standard library.

**Check whether the grader distinguishes repairs — no model required**

```sh
python -m examples.inspect_grader
```

Expected output:

```text
starter {'target': False, 'regression': False}
reference {'target': True, 'regression': True}
one-item-only {'target': False, 'regression': False}
```

On the same knapsack task, the buggy program and a wrong repair that picks only one item fail, while the reference passes. This checks the cases' ability to distinguish those programs; it does not yet evaluate an agent's capabilities.

**Audit the recorded experiment — no model required**

```sh
python -m examples.verify_experiment
```

This checks the schedule, task snapshot hash, individual results, grade evidence, and saved metrics. It recomputes A=15/15 and B=13/15, with one B `output_limit` and one `agent_error`. Missing usage stays unknown. The command only reads files: it runs no candidates, calls no model, and overwrites no records.

It lists current source files or prompts that differ from the frozen batch. For example, the report code later gained termination counts; the original agent did not run with those changes. This audit checks internal consistency, not the authenticity of historical responses or the correctness of candidate code.

**Run one A/B pair with your model**

Candidate Python executes in a host subprocess: **this is not a security sandbox**. Run model-generated code in a restricted environment without sensitive data. Temporary directories and timeouts cannot prevent arbitrary Python from accessing the host.

The model must support Chat Completions and function tools. PowerShell configuration:

```powershell
$env:EVAL_BASE_URL = 'https://your-provider.example/v1'
$env:EVAL_MODEL = 'your-model'
# Set EVAL_API_KEY securely in the current environment; do not commit it.
python -m evalcourse.run --split dev --tasks knapsack --repeats 1 --judge --out runs/first-pair
```

This runs A and B once each, with at most twelve agent requests and two judge requests. Billing depends on the provider. Inspect `runs/first-pair/report.md`, then each attempt's `result.json`, `solution.py`, and `trace.jsonl`. New results may differ from the recorded batch; both versions are not required to succeed.

## Run a full experiment

```sh
python -m evalcourse.run --split dev --repeats 1 --judge --out runs/dev-check
python -m evalcourse.run --split holdout --repeats 3 --judge --out runs/holdout-check
```

These commands need model configuration. Output directories must not already exist. Options include `--tasks`, `--turns`, and `--seed`; defaults are dev, three repeats, six turns, and seed zero. The client fixes temperature at zero, response allowance at 2048 tokens, and request timeout at thirty seconds, without automatic retries. `--judge` enables claims grading. `EVAL_JUDGE_MODEL` can select another judge model; otherwise it uses the agent model. Reports record tokens, not assumed prices.

Auditing records and rerunning an experiment are different operations. Changing the model, service version, or budget changes conditions; even the same model name does not guarantee identical results. New runs belong in new directories.

## Outputs and interpretation

A batch saves a manifest (configuration, schedule, prompts, hashes), task snapshot, results.jsonl, and report.json/report.md. Each attempt saves trace.jsonl, solution.py, and result.json.

- `functional_pass`: target and regression acceptance checks all pass.
- `passed`: functional_pass and `status == done`.
- `termination_counts`: counts by agent termination state. `done` does not guarantee functional success; `budget` means exhausted turns, `output_limit` means exhausted response allowance, `agent_error` means a request/execution exception, and `filtered` means provider content filtering.
- `judge.status`: ok, error, or skipped. Only ok enters the verdict denominator; errors and skips are reported separately.
- Agent and judge time/tokens are separate. Missing usage remains unknown, not zero.
- Any/all success are empirical task proportions with at least one/all attempts successful. The small-sample task bootstrap is descriptive, not evidence of general capability or equivalence.

Reassess saved claims without rerunning the agent:

```sh
python -m evalcourse.rejudge runs/holdout-check --out runs/claims-check
```

Rejudge validates batch completeness before model calls and writes a new directory with source hashes. Changing the rubric after inspecting results makes the new assessment exploratory.

## Tasks and evidence

- [Protocol](experiments/PROTOCOL.md): fixed hypotheses, budgets, metrics, and interpretation rules.
- [Task construction](data/README.md): provenance, input domains, independent oracles, wrong repairs, and exclusions.
- [Experiment index](experiments/README.md): development, final, and follow-up batches.
- Development check: `experiments/quixbugs-dev-1/`, six attempts.
- Final A/B: `experiments/quixbugs-holdout-3/`, five tasks × two versions × three repeats.
- Follow-up: `experiments/quixbugs-missing-followup-1/`, retained separately from the primary comparison.

Public problems may have appeared in model training. Holdout means unused in this prompt-development process, not unseen by the model. The claims judge has no independent human-label calibration; its results support diagnosis, not a reliable quality ranking.

The final batch produced **A 15/15, B 13/15**, with no observed functional repair benefit for B. Its two unsuccessful deliveries stopped at the response limit and at a first-request exception. See [section eleven of the English article](guide.html#ch11), the [original report](experiments/quixbugs-holdout-3/report.md), and the [detailed analysis](experiments/quixbugs-holdout-3/analysis.en.md). Missing results and costs remain in the original account.

## Repository structure

```text
evalcourse/     client / agent / grading / judge / run / report / rejudge
data/           Upstream programs, licenses, provenance, task generator
tasks.json      Eight tasks with public and independent acceptance cases
prompts/        A and B system prompts
tests/          Runner, graders, task quality, protocol, offline audit
examples/       Grader inspection, offline audit, mini-agent judge adapter
tutorial/       Chinese source, shared styles/scripts, builders
tutorial/en/    English article source
experiments/    Protocol and preserved real-run evidence
```

I use size as a constraint: the implementation should remain small enough to read in full while retaining tasks, traces, grading, and comparisons. The page's core line count covers evalcourse runtime, grading, reporting, and rejudging code, excluding task assets, tests, and writing.

## Explore and edit

Edit Chinese sections in `tutorial/01.html` through `12.html` and English counterparts in `tutorial/en/`, then run `python tutorial/build.py`. This builds `guide.html` (English by default) and `guide.zh-CN.html` (Chinese). Each page links to the other; with JavaScript enabled, switching retains the current section. Code snippets and experiment tables share the same sources.

To explore how the graders and experiment accounting behave, optionally run `python -m unittest discover -s tests -v`. To check that both HTML pages match their sources, run `python tutorial/build.py --check`. The optional `node tests/article_ui.cjs` checks reading controls through a DOM simulation; it does not verify real-browser layout or clipboard behavior.

This repository is a course and experiment record, with no automatic CI or required contribution checks. Keep new experiments in separate directories, preserve original records, and check any new material for credentials or private data before sharing it.

## Execution boundaries and license

The grading subprocess is not a sandbox. Temporary directories, timeouts, and environment cleanup provide reset and fault control for the current controlled tasks. Do not directly expose private repositories or sensitive host directories to candidate code. Real repository execution needs a restricted environment.

Original writing and code are MIT-licensed. Third-party programs retain their accompanying licenses. See [sources and attribution](THIRD_PARTY_NOTICES.md).
