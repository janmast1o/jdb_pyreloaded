from abc import ABC as AbstractClass, abstractmethod
from prompt_toolkit.completion import Completer
from typing import Optional

from src.io.abstract_wrapping_process_input_interceptor import AbstractWrappingProcessInputInterceptor
from src.io.abstract_wrapped_process_output_interceptor import AbstractWrappedProcessOutputInterceptor


class InternalUseInterceptorsAndCompleterCreator(AbstractClass):
    @abstractmethod
    def _create_completer(self) -> Completer:
        pass

    @abstractmethod
    def _create_input_interceptor(self) -> Optional[AbstractWrappingProcessInputInterceptor]:
        pass

    @abstractmethod
    def _create_output_interceptor(self) -> Optional[AbstractWrappedProcessOutputInterceptor]:
        pass