import signal

from typing import Callable, Any


class RaiseExceptionAfterReceivingSignal:
    def __init__(self, error_type_to_raise: type, print_on_handler_enter: bool = True):
        self._error_type_to_raise: type = error_type_to_raise
        self._print_on_handler_enter: bool = print_on_handler_enter
        assert isinstance(self._error_type_to_raise(), Exception)

    def _internal_handler(self, signum, frame):
        if self._print_on_handler_enter:
            print(f"Received signal: {signal.Signals(signum).name}")
        raise self._error_type_to_raise()

    def get_handler(self) -> Callable[[Any, Any], None]:
        return self._internal_handler
      

