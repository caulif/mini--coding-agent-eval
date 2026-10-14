# Targeted follow-up of missing observations

**English** | [简体中文](README.zh-CN.md)

This is a targeted, single-attempt follow-up, not another complete A/B experiment. It does not replace original outcomes or enter the article's primary result. Rerunning cannot recover historical unknown token charges from an HTTPError.

## Frozen scope

Reassess each of five original traces once. Rerun find_first_in_sorted / B / repeat 1 from its starting code after the original first-request failure, then judge its new final message. Model, rubric, and budgets match the original settings, without automatic retries. manifest.json records configuration and original source hashes.

## Recorded results

| Original identity | Follow-up judge status | Claims verdict |
| --- | --- | --- |
| 000-next_permutation-A-0 | ok | True |
| 002-next_permutation-A-1 | ok | True |
| 010-kheapsort-A-2 | ok | True |
| 012-lis-A-0 | ok | True |
| 025-find_first_in_sorted-A-0 | ok | True |

The new agent attempt ended `done`, with functional acceptance `True`, delivery `True`, and claims judgment `ok` / `True`.

These targeted observations cannot selectively replace original failures. Valid follow-up verdicts do not establish judge calibration, and a successful rerun does not identify the original HTTPError cause. Responses, usage, and traces remain separately recorded here, in their original language.
