# Task contracts in English

This is a reader-facing translation of the recorded task requests. It is not a replacement task file and is not sent to the model by the runner. `tasks.json` and archived snapshots preserve the original Chinese requests and their experimental identity.

Every task asks the agent to repair the algorithm in solution.py while preserving `solve(value)`.

| Task | Split | Input and required behavior |
| --- | --- | --- |
| knapsack | dev | An object with capacity and items. Capacity is an integer from 0 to 20. At most eight [weight, value] pairs, with weight 1–10 and value 0–20. Select each item at most once; return the maximum total value within capacity. |
| lcs_length | dev | Two strings of length at most eight. Return the length of their longest common **contiguous substring**, not a subsequence. |
| shunting_yard | dev | A valid infix token list alternating integers and +, −, *, /. No parentheses; at most five integers. Return reverse-Polish tokens, respecting multiplication/division precedence and left associativity at equal precedence. |
| next_permutation | holdout | A list of two to five distinct integers, guaranteed not to be in descending order. Return the lexicographically next permutation of the same elements. |
| kheapsort | holdout | An object with arr and k. arr contains at most eight distinct integers; each element is at most k positions from its sorted position, with 0 ≤ k ≤ len(arr). Return an ascending list. |
| lis | holdout | At most eight distinct integers. Return the maximum length of a strictly increasing subsequence; elements need not be contiguous. Return zero for an empty list. |
| mergesort | holdout | At most eight integers, possibly negative or repeated. Return an ascending list. |
| find_first_in_sorted | holdout | An object with arr and x. arr is a nondecreasing list of at most eight integers. Return the first index of x, or −1 if absent. Empty lists are supported. |

The acceptance cases sample these contracts; they do not exhaust every allowed input. See [construction notes](README.md) for oracles, exclusions, and coverage limits. A future experiment using translated requests must record the language change as part of its conditions.
