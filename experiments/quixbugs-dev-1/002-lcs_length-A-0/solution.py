def lcs_length(s, t):
    from collections import Counter

    dp = Counter()
    best = 0

    for i in range(len(s)):
        for j in range(len(t)):
            if s[i] == t[j]:
                dp[i, j] = dp[i - 1, j - 1] + 1
                if dp[i, j] > best:
                    best = dp[i, j]

    return best


"""
Longest Common Substring
longest-common-substring

Input:
    s: a string
    t: a string

Output:
    Length of the longest substring common to s and t

Example:
    >>> lcs_length('witch', 'sandwich')
    2
    >>> lcs_length('meow', 'homeowner')
    4
"""


def solve(value):
    return lcs_length(*value)
