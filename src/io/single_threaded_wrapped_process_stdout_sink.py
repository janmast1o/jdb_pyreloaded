import io
import sys

from typing import Any, List, Optional

from src.io.special_line_processor import SpecialLineProcessor

# Since it's meant to be used primarly with pexpect it needs to implement
# two methods - write() and flush(), which should behave simiarly
# to those of a TextIOWrapper object
class SingleThreadedWrappedProcessStdoutSink():
    def __init__(self, special_line_processor: SpecialLineProcessor,
                 io_sink: io.TextIOWrapper = sys.stdout):
        self.io_sink: io.TextIOWrapper = io_sink
        self.line_to_ignore_next_occurrence_of: Optional[str] = None
        self._special_line_processor: SpecialLineProcessor = special_line_processor

    def write(self, s: str) -> None:
        # This check is based on an assumption formed after empirically observing
        # that whenever this `write` method is called for input passed to wrapped process
        # it is passed by itself. This is not a guarantee and could be a good place
        # to start debugging if some problems regarding console output redirection
        # from wrapped process are encountered
        if s.strip() == self.line_to_ignore_next_occurrence_of:
            self.line_to_ignore_next_occurrence_of = None
            return

        separate_lines = s.splitlines(keepends=True)
        processed_lines = []
        for line in separate_lines:
            i = self._special_line_processor.maybe_get_matching_special_line_index(line)
            if i is None:
                processed_lines.append(line)
            else:
                processed_special_line = self._special_line_processor.apply_to_line_of_type(i, line)
                if processed_special_line is not None:
                    line_terminated_with_newline = len(line) > 0 and line[-1] == "\n"
                    processed_lines.append(processed_special_line + "\n" if line_terminated_with_newline else "")

        self.io_sink.write("".join(processed_lines))                

    def flush(self) -> None:
        self.io_sink.flush()
           