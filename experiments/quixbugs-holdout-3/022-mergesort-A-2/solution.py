
def mergesort(arr):
    # Base case: a list of length 0 or 1 is already sorted.
    # (Stopping only at length 0 causes infinite recursion for length 1,
    # since middle == 0 and arr[middle:] is the whole list again.)
    if len(arr) <= 1:
        return list(arr)

    middle = len(arr) // 2
    left = mergesort(arr[:middle])
    right = mergesort(arr[middle:])

    result = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


"""
Merge Sort


Input:
    arr: A list of ints

Output:
    The elements of arr in sorted order
"""


def solve(value):
    return mergesort(value)
