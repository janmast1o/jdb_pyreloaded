import io
import sys

from typing import Any, List

from src.io.special_line_processor import SpecialLineProcessor

# Since it's meant to be used primarly with pexpect it needs to implement
# two methods - write() and flush(), which should behave simiarly
# to those of a TextIOWrapper object
class SingleThreadedWrappedProcessStdoutSink():
    def __init__(self, special_line_processor: SpecialLineProcessor,
                 io_sink: io.TextIOWrapper = sys.stdout):
        self.io_sink: io.TextIOWrapper = io_sink
        self.lines: List[str] = []

    def write(self, s: Any) -> None:

        self.io_sink.write(f"Inside wrapper: {s}\ntype: {type(s)}\nsplit_lines: {s.splitlines()}\nbytes: {list(s)}\n") 

    def flush(self) -> None:
        self.io_sink.flush()
           