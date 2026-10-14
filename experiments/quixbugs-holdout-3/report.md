# Prompt A/B report

| Version | Passed / trials | Rate | Any / all | Mean seconds | Tokens | Errors |
|---|---:|---:|---:|---:|---:|---:|
| A | 15/15 | 100.0% | 100.0% / 100.0% | 16.11 | 128049 | 0 |
| B | 13/15 | 86.7% | 100.0% / 60.0% | 16.88 | None | 1 |

Repeats per task: 3
B − A: -13.3%
Task bootstrap interval: [-0.2666666666666667, 0]

Tiny convenience sample: descriptive evidence, not a general capability claim. Bootstrap resamples tasks; it does not fully model within-task stochasticity.

## Per-task changes
- find_first_in_sorted: -33.3%
- kheapsort: -33.3%
- lis: +0.0%
- mergesort: +0.0%
- next_permutation: +0.0%

## Verification claims (separate from task success)

| Version | Passed / scored | Errors | Skipped | Not requested | Judge seconds | Judge tokens |
|---|---:|---:|---:|---:|---:|---:|
| A | 9/10 | 5 | 0 | 0 | 161.45 | None |
| B | 13/13 | 0 | 2 | 0 | 79.27 | 40236 |

Only valid judge verdicts enter the scored denominator. Errors/skips are not passes; inspect coverage and calibration before comparing rates.
