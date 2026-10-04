from abc import ABC as AbstractClass
from typing import Optional


class AbstractWrappingProcessInputInterceptor(AbstractClass):
    def __init__(self):
        ...

    # Returns filtered input
    def intercept_on_input_send(self, command: str) -> Optional[str]:
        pass