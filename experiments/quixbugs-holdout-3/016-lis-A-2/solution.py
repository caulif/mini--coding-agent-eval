

def lis(arr):
    # ends[L] = index of the smallest possible tail of an increasing
    # subsequence of length L found so far.
    ends = {}
    longest = 0

    for i, val in enumerate(arr):
        # Longest prefix length whose tail value is strictly less than val.
        prefix_lengths = [j for j in range(1, longest + 1) if arr[ends[j]] < val]
        length = max(prefix_lengths) if prefix_lengths else 0

        if length == longest:
            # We can extend the longest subsequence found so far.
            ends[length + 1] = i
            longest = length + 1
        elif val < arr[ends[length + 1]]:
            # Improve the tail for the same length without changing longest.
            ends[length + 1] = i

    return longest


"""
Longest Increasing Subsequence
longest-increasing-subsequence


Input:
    arr: A sequence of ints

Precondition:
    The ints in arr are unique

Output:
    The length of the longest monotonically increasing subsequence of arr

Example:
    >>> lis([4, 1, 5, 3, 7, 6, 2])
    3
"""


def solve(value):
    return lis(value)
