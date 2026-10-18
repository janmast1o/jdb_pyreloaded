def find_longest_common_prefix_of_two_words(a: str, b: str) -> str:
    i = 0
    len_a, len_b = len(a), len(b)

    while i < len_a and i < len_b and a[i] == b[i]:
        i += 1

    if i == 0:
        return ""

    return a[:i]


def parse_to_string_and_pad_to_digits(x: int, digits=2) -> str:
    assert isinstance(x, int)
    assert x >= 0
    x_stringified = str(x)
    if len(x_stringified) >= digits:
        return x_stringified
    remaining_padding = digits - len(x_stringified)
    return x_stringified + " " * remaining_padding


def turn_text_to_bold(self, text: str) -> str:
    return f"\033[1m{text}\033[0m"
    