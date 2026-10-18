from abc import abstractmethod, ABC as AbstractClass
from typing import List


class AbstractWrappedProcessOutputInterceptor(AbstractClass):
    def __init__(self):
        pass

    # Returns filtered output
    @abstractmethod
    def _filter_and_handle_intercepted_output_lines(self, s_lines: List[str]) -> List[str]:
        pass
    
    def intercept_on_write(self, s_lines: List[str]) -> List[str]:
        return self._filter_and_handle_intercepted_output_lines(s_lines)