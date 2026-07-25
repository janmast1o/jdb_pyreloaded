def find_longest_common_prefix_of_two_words(a: str, b: str) -> str:
    i = 0
    len_a, len_b = len(a), len(b)

    while i < len_a and i < len_b and a[i] == b[i]:
        i += 1

    if i == 0:
        return ""

    return a[:i]    