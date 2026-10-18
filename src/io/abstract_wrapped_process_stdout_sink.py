import io
import re
import sys

from abc import abstractmethod
from typing import Optional, List

from src.io.abstract_wrapped_process_output_interceptor import AbstractWrappedProcessOutputInterceptor
from src.utils.util_objects import BaseString


# TODO: Decide if write implementation should be moved to this class.
class AbstractWrappedProcessStdoutSink:
    def __init__(self, input_line_match_pattern: BaseString,
                 ignore_input_line: bool,
                 optional_output_interceptor: Optional[AbstractWrappedProcessOutputInterceptor] = None,
                 io_sink: io.TextIOWrapper = sys.stdout):
        self.io_sink: io.TextIOWrapper = io_sink
        self.line_to_ignore_next_occurrence_of: Optional[str] = None
        self._input_line_format: BaseString = input_line_match_pattern
        self._ignore_input_line: bool = ignore_input_line
        self._optional_output_interceptor: Optional[AbstractWrappedProcessOutputInterceptor] = optional_output_interceptor
        self._last_write_call_trailing_unfinished_line: Optional[str] = None

    # Based on an assumption that the processes will always be run
    # in terminals with ONCLR enabled.
    def _split_text_into_lines(self, s: str) -> List[str]:
        s_lines = s.splitlines(keepends=True)
        n = len(s_lines)
        for i in range(n):
            if s_lines[i].endswith("\n") and (not s_lines[i].endswith("\r\n")): # Terminated with newline without carriage return
                s_lines[i] = s_lines[:-1]

        return s_lines        

    def _maybe_add_last_call_trailing_unfinished_line(self, s_lines: List[str]) -> List[str]:
        if self._last_write_call_trailing_unfinished_line is not None:
            s_lines[0] = self._last_write_call_trailing_unfinished_line + s_lines[0]
            self._last_write_call_trailing_unfinished_line = None

        # The return is technically redundant but makes the function look clearer in my opinion.
        return s_lines    

    # We assume that input line is never terminated with newline 
    # in the wrapped process.
    def _is_input_line(self, line: str) -> bool:
        if line.endswith("\n"):
            return False
        line = line.strip()
        if self._input_line_format.is_regex():
            return re.match(self._input_line_format, line)
        else:
            return self._input_line_format == line

    @abstractmethod
    def write(self, s: str) -> None:
        pass

    def flush(self) -> None:
        self.io_sink.flush()    