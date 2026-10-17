import io
import sys

from typing import Optional, List
from typing_extensions import override

from src.io.abstract_wrapped_process_output_interceptor import AbstractWrappedProcessOutputInterceptor
from src.io.abstract_wrapped_process_stdout_sink import AbstractWrappedProcessStdoutSink
from src.io.special_line_processor import SpecialLineProcessor
from src.utils.util_objects import BaseString


# Since it's meant to be used primarily with pexpect it needs to implement
# two methods - write() and flush(), which should behave similarly
# to those of a TextIOWrapper object
class SingleThreadedWrappedProcessStdoutSink(AbstractWrappedProcessStdoutSink):
    def __init__(self, input_line_match_pattern: BaseString,
                 ignore_input_line: bool,
                 optional_output_interceptor: Optional[AbstractWrappedProcessOutputInterceptor] = None,
                 io_sink: io.TextIOWrapper = sys.stdout):
        super().__init__(input_line_match_pattern, ignore_input_line, optional_output_interceptor, io_sink)

    @override
    def write(self, s: str) -> None:
        # This check is based on an assumption formed after empirically observing
        # that whenever this `write` method is called for input passed to wrapped process
        # it is passed by itself. This is not a guarantee and could be a good place
        # to start debugging if some problems regarding console output redirection
        # from wrapped process are encountered
        if s.strip() == self.line_to_ignore_next_occurrence_of:
            self.line_to_ignore_next_occurrence_of = None
            return

        s_lines = self._split_text_into_lines(s)
        # print("S_lines: ", s_lines)
        # print("Trailing = ", self._last_write_call_trailing_unfinished_line)
        s_lines = self._maybe_add_last_call_trailing_unfinished_line(s_lines)
        # print(s_lines)
        # Might look clearer without De Morgan's law applied:
        # (not an input line) and (doesn't end with newline)
        last_is_an_input_line = self._is_input_line(s_lines[-1])
        if not (last_is_an_input_line or s_lines[-1].endswith("\n")):
            self._last_write_call_trailing_unfinished_line = s_lines.pop(-1)
        elif last_is_an_input_line:
            if self._ignore_input_line:
                s_lines.pop(-1)
            else:
                s_lines[-1] = s_lines[-1] + "\n"

        if self._optional_output_interceptor is not None:
            s_lines = self._optional_output_interceptor.intercept_on_write(s_lines)

        self.io_sink.write("".join(s_lines))