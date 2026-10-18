from abc import abstractmethod
from typing import List, Optional, Callable
from typing_extensions import override

from src.io.abstract_wrapped_process_output_interceptor import AbstractWrappedProcessOutputInterceptor
from src.io.debug.breakpoint_related_message_kind import BreakpointRelatedMessageKind
from src.utils.util_functions import turn_text_to_bold


class AbstractWrappedDebuggerOutputInterceptor(AbstractWrappedProcessOutputInterceptor):
    def __init__(self, wrapped_debugger_command_execute_function: Callable[[str], None]):
        self._wrapped_debugger_command_execute_function: Callable[[str], None] = wrapped_debugger_command_execute_function
        self._awaiting_breakpoint_condition_check_line_begin: Optional[str] = None

    @abstractmethod
    def _try_get_breakpoint_related_message_kind_match(self, line: str) -> Optional[BreakpointRelatedMessageKind]:
        pass

    # Returns processed line or `None` if the line is not meant to be printed. 
    # Should handle non-stripped lines on its own.
    @abstractmethod
    def _handle_breakpoint_related_message(self, matched_kind: BreakpointRelatedMessageKind, line: str) -> Optional[str]:
        pass

    # Marked as abstract as it is debugger specific
    @abstractmethod
    def _get_resume_execution_command(self) -> str:
        pass

    @override
    def _filter_and_handle_intercepted_output_lines(self, s_lines: List[str]) -> List[str]:
        # separate_lines = s.splitlines(keepends=True)
        filtered_lines: List[str] = []
        breakpoint_related_message_kind: Optional[BreakpointRelatedMessageKind] = None
        commands_to_send_to_wrapped_debugger: List[str] = []

        for line in s_lines:
            # Handling empty lines (probably a better way to do this, but I don't have an idea where right now)
            if len(line.strip()) == 0 or line.strip() == ">": 
                line = None
            elif (breakpoint_related_message_kind := self._try_get_breakpoint_related_message_kind_match(line)) is not None:
                line = self._handle_breakpoint_related_message(breakpoint_related_message_kind, line)
            elif self._awaiting_breakpoint_condition_check_line_begin is not None and line.strip().startswith(self._awaiting_breakpoint_condition_check_line_begin):
                condition_check_result_as_str = line.split()[-1]
                condition_check_result: bool = None
                if condition_check_result_as_str == "true":
                    condition_check_result = True
                elif condition_check_result_as_str == "false":
                    condition_check_result = False
                else: # Equivalent to `elif condition_check_result_as_str == "null"`
                    print(
                        f"{turn_text_to_bold(Warning)}: Condition " +
                        f"{self._awaiting_breakpoint_condition_check_line_begin} for one of the breakpoints is ill-formed.\n" +
                        "Remove that breakpoint, rework the condition and add it again. Will halt execution just in case."
                    )
                    condition_check_result = True

                self._awaiting_breakpoint_condition_check_line_begin = None 
                if not condition_check_result: # Condition check evaluated as false
                    commands_to_send_to_wrapped_debugger.append(self._get_resume_execution_command())

            if line is not None:    
                filtered_lines.append(line)

        for command in commands_to_send_to_wrapped_debugger:
            self._wrapped_debugger_command_execute_function(command)

        return filtered_lines  