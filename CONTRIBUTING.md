# Contributing

**English** | [简体中文](CONTRIBUTING.zh-CN.md)

This project records an exploration of agent evaluation. Changes should explain observations, design choices, and validation. Keep the implementation readable in full; add abstraction only when needed. Corrections to concepts, code, and interpretation are welcome.

## Changes and checks

- Chinese article sources are `tutorial/01.html` through `12.html`; English counterparts are in `tutorial/en/`. Build both guide.html (English default) and guide.zh-CN.html. Keep matching subsection order and anchors; code blocks and experiment tables share sources.
- README.md defaults to English; README.zh-CN.md is Chinese. Update both. Code comments and docstrings are English; original tasks and experimental evidence retain their language.
- Add behavioral regression coverage for grading, experimental accounting, or tool execution changes.
- New tasks need pinned provenance/license, explicit input contracts, buggy starts, independent expectations, passing reference repairs, and rejected plausible wrong repairs.
- Label constructed examples, real model observations, and human calibration separately. Once holdout findings inform a prompt change, use new confirmation tasks.

From the repository root with Python 3.12:

```sh
python -m unittest discover -s tests -v
python -m examples.inspect_grader
python -m examples.verify_experiment
python tutorial/build.py
python tutorial/build.py --check
node tests/article_ui.cjs
```

The runtime needs only the Python standard library. UI simulation checks use Node.js and do not establish real browser acceptance. CI is configured for Windows and Ubuntu. Model experiments are optional and should report tasks, model, repeats, and budgets; a favorable score is not an acceptance criterion.

## Pages and releases

Check desktop and narrow layouts, anchors, collapsible content, copy buttons, reading restoration, overflow, and language switching in a real browser. Static checks do not prove visual quality.

The HTML pages work offline. Add a public website link only after deployment is explicitly requested and completed. A release should preserve recoverable source versions so experiment hashes can be traced to actual files.

## Evidence and execution boundaries

Do not overwrite original experiments. Recomputed reports, rejudging, and new executions are separate records. Explain source-hash differences instead of rewriting historical hashes to conceal them. Translate commentary into separate, labeled companions; do not translate raw responses in place.

Do not commit API keys, environment files, private code, local connection settings, or unchecked traces. Candidate Python subprocesses are not security sandboxes; model execution needs a restricted environment. The author's local model service is not a project dependency.

Internal planning notes are maintenance material, not the first-read entry point. Public documentation should avoid personal machine details and describe only reproducible project requirements.

## Current limits

Local offline tests and DOM simulations pass; current desktop/narrow browser visual acceptance and remote CI execution remain unverified. Model trials retain missing judge verdicts and unknown usage. A static privacy review found no blocking disclosure; raw judge responses retain provider-generated identifiers and timestamps as correlation metadata. Review new evidence before publication. Local work logs, old experiments, and editing drafts are not part of the repository.
