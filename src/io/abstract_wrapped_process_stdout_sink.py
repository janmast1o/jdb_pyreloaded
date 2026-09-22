import io
import sys

from abc import abstractmethod
from typing import Optional

from src.io.special_line_processor import SpecialLineProcessor


# TODO: Decide if write implementation should be moved to this class.
class AbstractWrappedProcessStdoutSink:
    def __init__(self, special_line_processor: SpecialLineProcessor,
                 io_sink: io.TextIOWrapper = sys.stdout):
        self.io_sink: io.TextIOWrapper = io_sink
        self.line_to_ignore_next_occurrence_of: Optional[str] = None
        self._special_line_processor: SpecialLineProcessor = special_line_processor

    @abstractmethod
    def write(self, s: str) -> None:
        pass

    @abstractmethod
    def flush(self) -> None:
        pass    