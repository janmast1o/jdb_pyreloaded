from abc import abstractmethod
from typing import Optional
from typing_extensions import override

from src.io.abstract_wrapping_process_input_interceptor import AbstractWrappingProcessInputInterceptor
from src.io.debug.breakpoint_related_message_kind import BreakpointRelatedCommandKind


class AbstractDebuggerWrapperInputInterceptor(AbstractWrappingProcessInputInterceptor):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def _try_get_breakpoint_related_command_type_match(self, command: str) -> Optional[BreakpointRelatedCommandKind]:
        pass

    # A non-null returned string should be sent further
    @abstractmethod
    def _handle_breakpoint_related_command(self, matched_kind: BreakpointRelatedCommandKind, command: str) -> Optional[str]:
        pass

    @override
    def intercept_on_input_send(self, command: str) -> Optional[str]:
        if (breakpoint_related_command_type := self._try_get_breakpoint_related_command_type_match(command)) is not None:
            command = self._handle_breakpoint_related_command(breakpoint_related_command_type, command)

        return command