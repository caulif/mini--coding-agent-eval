# QuixBugs final experiment analysis

**English** | [Original Chinese analysis](analysis.md)

This is an English rendering of the original analysis, added after the experiment. Original traces, results, prompts, snapshots, and reports are unchanged.

No functional repair benefit was observed for B. A achieved 15/15, B 13/15, a difference of −13.3 percentage points. All thirty planned attempts remain; later attempts do not replace them. This small sample cannot establish a general capability ranking.

## Conditions

Five holdout tasks × A/B × three repeats. Requested model: `deepseek/deepseek-v4.1-flash`; response model: `deepseek-v4.1-flash`. Six turns, at most 2048 tokens per response, temperature zero. Both versions have the same tools, including agent-authored tests, and each attempt starts fresh. Conditions and hashes are in manifest.json; full tasks are in tasks.snapshot.json. Task requests retain their original Chinese language.

## Two unsuccessful deliveries

- `007-kheapsort-B-0`: after reading source, the second response ends with finish_reason=length. completion_tokens=2048, including reasoning_tokens=2048. No repair was written and functional acceptance failed.
- `026-find_first_in_sorted-B-1`: HTTPError on the first request, before any write. Functional acceptance failed. The exception type was retained, but the HTTP status was not; the cause cannot be assigned to the provider.

Failures must not be deleted to improve the score, and interface exceptions are not algorithmic errors. The task-bootstrap interval is approximately [−26.7, 0] percentage points and is descriptive only.

## Claims and functionality

A passed 9/10 valid claims assessments, with five missing verdicts: four truncations and one HTTPError. B passed 13/13, with two skipped assessments because the agent did not complete normally. The judge used the same model as the agent and lacks independent human calibration. Different coverage prevents a reliable comparison of these proportions.

`016-lis-A-2` is a manually inspected example: public tests passed before editing, but only six authored cases ran afterward. The final response claimed both public and additional checks now passed. Independent acceptance passed, while the unsupported-claims verdict has evidence in the trace. Inspecting one case is not calibration.

## Resource use and behavior

Mean agent time was 16.11 seconds for A and 16.88 for B, including unsuccessful attempts. These are not total system times and exclude independent grading and the judge. A reported 128,049 tokens. B's complete total is unknown; fourteen known rows sum to 123,327 tokens, an incomplete subtotal unsuitable for comparing total cost.

Both versions called authored tests sixteen times. Other tool counts are derived from traces in behavior.json. With two incomplete B deliveries, raw call counts alone cannot establish a quality difference. Interpretation depends on what each test checked and the resulting artifact.

## Next hypotheses

Vary the response budget as a separate factor to investigate truncation; configure judge budgeting independently and calibrate on human labels; broaden coverage with tasks chosen in advance. These five tasks have now been inspected and are development evidence for future changes. Original records remain intact rather than being revised to favor later versions.
