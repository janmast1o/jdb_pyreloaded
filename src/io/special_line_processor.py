import re

from typing import List, Callable, Optional
from typing_extensions import overload

from src.utils.util_objects import BaseString

# `line_processing_function` takes the index corresponding to the line type
# at the same index in `lines_to_process_specially`.
#
# `lines_to_process_specially` must be a list of `BaseString` (a class implemented in this project)
# as the comparison will differ whether a sequence is considered to be regular expression or not.
#
# TODO: Consider removing this, as input interceptor already does something similar
class SpecialLineProcessor:
    def __init__(self, lines_to_process_specially: List[BaseString], 
                 line_processing_function: Callable[[int, str], str],
                 automatically_strip_lines: bool = True):
        self.lines_to_process_specially: List[BaseString] = lines_to_process_specially
        self._line_processing_function: Callable[[int, str], str] = line_processing_function
        self._automatically_strip_lines: bool = automatically_strip_lines

    # `None` being returned denotes no match being found.
    def maybe_get_matching_special_line_index(self, line: str) -> Optional[int]:
        if self.maybe_get_matching_special_line_index:
            line = line.strip()
        for i in range(len(self.lines_to_process_specially)):
            special_line_i = self.lines_to_process_specially[i]
            if special_line_i.is_regex() and re.match(line):
                return i
            elif (not special_line_i.is_regex()) and line == special_line_i:
                return i

        return None    

    def apply_to_line_of_type(self, special_line_type_index: int, special_line: str) -> str:
        if self._automatically_strip_lines:
            special_line = special_line.strip()
        return self._line_processing_function(special_line_type_index, special_line)