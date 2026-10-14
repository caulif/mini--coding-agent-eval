# Prompt A/B report

| Version | Passed / trials | Rate | Any / all | Mean seconds | Tokens | Errors |
|---|---:|---:|---:|---:|---:|---:|
| A | 3/3 | 100.0% | 100.0% / 100.0% | 12.24 | 20461 | 0 |
| B | 3/3 | 100.0% | 100.0% / 100.0% | 16.74 | 30451 | 0 |

Repeats per task: 1
B − A: +0.0%
Task bootstrap interval: [0, 0]

Tiny convenience sample: descriptive evidence, not a general capability claim. Bootstrap resamples tasks; it does not fully model within-task stochasticity.

## Per-task changes
- knapsack: +0.0%
- lcs_length: +0.0%
- shunting_yard: +0.0%

## Verification claims (separate from task success)

| Version | Passed / scored | Errors | Skipped | Not requested | Judge seconds | Judge tokens |
|---|---:|---:|---:|---:|---:|---:|
| A | 3/3 | 0 | 0 | 0 | 20.45 | 8629 |
| B | 3/3 | 0 | 0 | 0 | 14.52 | 9323 |

Only valid judge verdicts enter the scored denominator. Errors/skips are not passes; inspect coverage and calibration before comparing rates.
