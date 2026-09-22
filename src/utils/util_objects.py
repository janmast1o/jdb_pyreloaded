import threading

from abc import abstractmethod
from typing_extensions import override

# The underlying value should always be set with `set_value()` method.
class BooleanWrapper:
    def __init__(self, value: bool):
        self._value: bool = value

    @staticmethod
    def create_empty() -> "BooleanWrapper":
        return BooleanWrapper(None)    

    def get_value(self) -> bool:
        return self._value

    def set_value(self, new_value: bool) -> None:
        self._value = new_value

    @property
    def is_valid(self) -> bool:
        return self._value is not None

    def __bool__(self):
        return self._value

    def __and__(self, other_value):
        return self._value and other_value

    def __or__(self, other_value):
        return self._value or other_value

    def __xor__(self, other_value):
        return self._value.__xor__(other_value)    

    def __rand__(self, other_value):
        return self._value.__rand__(other_value)

    def __ror__(self, other_value):
        return self._value.__ror__(other_value)

    def __rxor__(self, other_value):
        return self._value.__rxor__(other_value)

    def __getnewargs__(self):
        return self._value.__getnewargs__()

    def __invert__(self):
        return self._value.__invert__()


# Thread safe with respect to setting the value.
class ThreadSafeBooleanWrapper(BooleanWrapper):
    def __init__(self, value: bool):
        super().__init__(value)
        self.lock = threading.Lock()

    def set_value(self, new_value: bool):
        self.lock.acquire(blocking=True)
        super().set_value(new_value)    
        self.lock.release() 


class BaseString(str):
    @abstractmethod
    def is_regex(self) -> bool:
        pass


class SimpleString(BaseString):
    @override
    def is_regex(self) -> bool:
        return False


class Regex(BaseString):
    @override
    def is_regex(self) -> bool:
        return True
      
