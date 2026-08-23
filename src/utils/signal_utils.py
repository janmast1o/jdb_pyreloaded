import signal

from typing import Callable, Any

from src.utils.util_objects import BooleanWrapper

class BooleanValueFlippedInSignalHandlerException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class FlipBooleanValueAfterReceivingSignal:
    def __init__(self, boolean_wrapper: BooleanWrapper, raise_error: bool = True):
        self.boolean_wrapper: BooleanWrapper = boolean_wrapper
        self.raise_error: bool = raise_error

    def _internal_handler(self, signum, frame):
        print(f"Received signal: {signal.Signals(signum).name}, flipping the boolean value...")
        self.boolean_wrapper.value = not bool(self.boolean_wrapper)
        print(f"Flipped the boolean value")
        if self.raise_error:
            raise BooleanValueFlippedInSignalHandlerException()

    def get_handler(self) -> Callable[[Any, Any], None]:
        return self._internal_handler
      

