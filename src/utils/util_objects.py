from abc import abstractmethod
from typing_extensions import override

class BooleanWrapper:
    def __init__(self, value: bool):
        self.value: bool = value

    @staticmethod
    def create_empty(self) -> "BooleanWrapper":
        return BooleanWrapper(None)    

    @property
    def is_valid(self) -> bool:
        return self.value is not None

    def __bool__(self):
        return self.value

    def __and__(self, other_value):
        return self.value and other_value

    def __or__(self, other_value):
        return self.value or other_value

    def __xor__(self, other_value):
        return self.value.__xor__(other_value)    

    def __rand__(self, other_value):
        return self.value.__rand__(other_value)

    def __ror__(self, other_value):
        return self.value.__ror__(other_value)

    def __rxor__(self, other_value):
        return self.value.__rxor__(other_value)

    def __getnewargs__(self):
        return self.value.__getnewargs__()

    def __invert__(self):
        return self.__invert__()


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
      
