# Final A/B experiment

Start with the [English analysis](analysis.en.md) or the [original report](report.md).

- Five tasks, two prompts, three repeats: thirty planned attempts.
- A: 15/15 successful deliveries. B: 13/15.
- B's unsuccessful attempts: one response truncation and one first-request HTTPError.
- Judge missingness and unknown usage are retained, not imputed.

The [original Chinese analysis](analysis.md), task requests, and model responses retain their original language. The English analysis is a companion translation, not replacement evidence. Run `python -m examples.verify_experiment` from the repository root to audit the saved batch without model calls.
