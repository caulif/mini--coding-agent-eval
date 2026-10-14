# Task construction notes

**English** | [简体中文](README.zh-CN.md)

Eight tasks adapt QuixBugs at commit `4257f44b0ff1181dedaedee6a447e133219fcebf`, under MIT. This is a subset of a program-repair benchmark, not industrial issues or an official QuixBugs score.

Read the [task contracts in English](TASKS.md) alongside the original task data.

## Selection and adaptation

- Development: knapsack, lcs_length, shunting_yard. Holdout: next_permutation, kheapsort, lis, mergesort, find_first_in_sorted.
- Selection: single-file, standard-library execution, short runtime, explicit input contracts, and different boundary/state/order/termination failures. Selection did not depend on A/B winners; difficulty is empirical.
- Original buggy and correct programs remain unchanged in `quixbugs/buggy` and `quixbugs/correct`. Task generation appends a JSON-compatible `solve(value)` adapter and materializes generators as lists.
- Inputs have explicit bounds. Independent enumeration/brute-force oracles generate expected values, rather than using upstream reference code as the sole authority. Reference repairs must pass acceptance.
- `build_tasks.py` deterministically produces public cases and disjoint acceptance cases. target/regression are interleaved groups of contract checks, not individually demonstrated “must fail/must pass before repair” labels. The buggy version may fail both.
- Public examples inside upstream source remain visible. Independent acceptance means its cases and expectations are not provided through the agent's tool interface. The Python runner is not an adversarial isolation sandbox.
- Huge, slow official cases are excluded. This project does not measure large-scale performance, cross-file localization, repository setup, or architecture quality.

## Quality checks

`python data/build_tasks.py` regenerates tasks.json, tests/oracles.json, and data/provenance.json. Provenance includes source paths, revision, and SHA-256 hashes.

Offline checks establish failing buggy programs, passing reference repairs, rejected plausible wrong repairs, source hashes, and the 3/5 split. Brute-force expected values do not imply exhaustive coverage of the declared domain: lis permits eight elements but the generator enumerates permutations only up to five. Acceptance cannot prove full algorithm correctness.

wrap was excluded before selection: for certain leading-space inputs, its reference loop may not advance (`end == 0`). Downloaded originals remain as exclusion evidence, outside the task set. This is a source-inspection finding, not an agent's observed failure.

## Reuse, language, and leakage

Tasks, acceptance cases, and reference repairs are public. Models may have encountered QuixBugs during training. Holdout means unused in this prompt-development process, not training-unseen. Once these results inform a prompt change, a new confirmation set is needed.

Task requests retain their original Chinese text to preserve experiment identity. English documentation does not silently translate model inputs. A future English-task experiment should use a separate version and record the changed language condition.
