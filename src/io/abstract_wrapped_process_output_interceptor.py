from abc import abstractmethod, ABC as AbstractClass

class AbstractWrappedProcessOutputInterceptor(AbstractClass):
    def __init__(self):
        pass

    # Returns filtered output
    @abstractmethod
    def _filter_and_handle_intercepted_output(self, s: str) -> str:
        pass
    
    def intercept_on_write(self, s: str) -> None:
        s = self._filter_and_handle_intercepted_output(s)
        return s