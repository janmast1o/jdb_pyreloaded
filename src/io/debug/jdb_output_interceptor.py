import re

from typing import Optional, Callable
from typing_extensions import override

from src.io.debug.abstract_wrapped_debugger_output_interceptor import AbstractWrappedDebuggerOutputInterceptor, BreakpointRelatedMessageKind
from src.process.debug.breakpoints import BaseBreakpoint, ConditionalBreakpoint, BreakpointManager, BreakpointKind

# NOTE: This is what JDB says about setting threads
# stop [go|thread] [<thread_id>] <at|in> <location>
#                           -- set a breakpoint
#                           -- if no options are given, the current list of breakpoints is printed
#                           -- if "go" is specified, immediately resume after stopping
#                           -- if "thread" is specified, only suspend the thread we stop in
#                           -- if neither "go" nor "thread" are specified, suspend all threads
#                           -- if an integer <thread_id> is specified, only stop in the specified thread
#                           -- "at" and "in" have the same meaning
#                           -- <location> can either be a line number or a method:
#                           --   <class_id>:<line_number>
#                           --   <class_id>.<method>[(argument_type,...)]
#
# It is important to note, however, that from empiric evidence I can assess
# that options `[go|thread]` and `[<thread_id>]` are either very unreliable or just 
# flat out don't work. For that reason I will not accommodate them in this project (at least for the time being).

# TODO: Optimize `line.strip(">").strip()` - not very high priority since
# this should not be a costly operation overall.
class JDBOutputInterceptor(AbstractWrappedDebuggerOutputInterceptor):
    BREAKPOINT_MESSAGE_KINDS_TO_THROTTLE = (
        BreakpointRelatedMessageKind.BREAKPOINTS_LISTED_HEADER |
        BreakpointRelatedMessageKind.ENTRY_IN_BREAKPOINT_LIST
    )  

    def __init__(self, wrapped_debugger_command_execute_function: Callable[[str], None],
                 breakpoint_manager: BreakpointManager):
        self._breakpoint_manager: BreakpointManager = breakpoint_manager
        super().__init__(wrapped_debugger_command_execute_function)

    def _find_code_address_in_line(self, line: str, message_kind: BreakpointRelatedMessageKind) -> Optional[str]:
        code_address: Optional[str] = None
        line_parts = line.lstrip(">").strip().split()
        # print(f"Line: {line}")
        # print(f"Line chars: {list(line)}")

        if message_kind == BreakpointRelatedMessageKind.DEFERRING_BREAKPOINT:
            # After 'Deferring' and 'breakpoint'
            code_address = line_parts[2]
        elif message_kind == BreakpointRelatedMessageKind.BREAKPOINT_SET:
            # The last in the line
            code_address = line_parts[-1]
        elif message_kind == BreakpointRelatedMessageKind.BREAKPOINT_REMOVED:
            # The last in the line
            code_address = line_parts[-1]
        elif message_kind == BreakpointRelatedMessageKind.BREAKPOINTS_LISTED_HEADER:
            # No code address in breakpoints listed header
            code_address = None
        elif message_kind == BreakpointRelatedMessageKind.BREAKPOINT_HIT:
            # After 'Breakpoint', 'hit:' and 'thread=<thread_name>'
            first_possible_code_address = line_parts[3].rstrip(",")
            # After 'Breakpoint', 'hit:' and 'thread=<thread_name>' with the method name removed and line number added
            second_possible_code_address = ".".join(line_parts[3].rstrip(",").split(".")[:-1]) + ":" + line_parts[4].split("=")[-1]
            code_address = f"{first_possible_code_address}|{second_possible_code_address}"
        elif message_kind == BreakpointRelatedMessageKind.ENTRY_IN_BREAKPOINT_LIST:
            # Last in the breakpoint entry line
            code_address = line_parts[-1]    

        if code_address is not None:
            code_address = code_address.rstrip(".,;")
        return code_address

    # TODO: If this code is too slow consider replacing regex with something faster
    @override
    def _try_get_breakpoint_related_message_kind_match(self, line: str) -> Optional[BreakpointRelatedMessageKind]:
        # Strip white characters, starter character (if it exists)
        line = line.lstrip(">").strip()
        if line.startswith("Deferring breakpoint"):
            return BreakpointRelatedMessageKind.DEFERRING_BREAKPOINT
        elif re.match(r"Set( deferred)? breakpoint .+", line):
            return BreakpointRelatedMessageKind.BREAKPOINT_SET
        elif line.startswith("Removed: breakpoint"):
            return BreakpointRelatedMessageKind.BREAKPOINT_REMOVED
        elif line.startswith("Breakpoints set:"): # After this line all lines starting with "<indent> breakpoint" are breakpoints
            return BreakpointRelatedMessageKind.BREAKPOINTS_LISTED_HEADER
        elif line.startswith("Breakpoint hit:"):
            return BreakpointRelatedMessageKind.BREAKPOINT_HIT

        return None

    @override
    def _handle_breakpoint_related_message(self, matched_kind: BreakpointRelatedMessageKind, line: str) -> Optional[str]:
        # print(f"Matched kind: {matched_kind}, line: {line}")
        if (matched_kind & JDBOutputInterceptor.BREAKPOINT_MESSAGE_KINDS_TO_THROTTLE) != 0:
            return None
        
        code_address = self._find_code_address_in_line(line, matched_kind)
        # TODO: Refactor this to be more universal
        if matched_kind == BreakpointRelatedMessageKind.BREAKPOINT_HIT:
            first_possible_code_address, second_possible_code_address = code_address.split("|")
            breakpoint_kind = self._breakpoint_manager.get_condition_type_for_code_address(first_possible_code_address)
            code_address = first_possible_code_address
            if breakpoint_kind is None:
                breakpoint_kind = self._breakpoint_manager.get_condition_type_for_code_address(second_possible_code_address)
                code_address = second_possible_code_address
        else:
            breakpoint_kind = self._breakpoint_manager.get_condition_type_for_code_address(code_address)        

        print(f"Line: {line}, CA: {code_address}, BK: {breakpoint_kind}")
        terminated_with_newline = False
        if line.endswith("\n"):
            terminated_with_newline = True

        line = line.lstrip(">").strip().rstrip(".")
        # If the breakpoint is conditional we need to trigger the condition check in 
        if matched_kind == BreakpointRelatedMessageKind.BREAKPOINT_HIT and breakpoint_kind == BreakpointKind.CONDITIONAL:
            associated_breakpoint_condition = self._breakpoint_manager.get_condition_for_code_address(code_address)
            # Do not wait here to determine if should halt the execution.
            # Let's keep the program stopped and only resume it after we get the output from
            # condition check.
            self._awaiting_breakpoint_condition_check_line_begin = associated_breakpoint_condition
            self._wrapped_debugger_command_execute_function(f"print {associated_breakpoint_condition}")
            line = "Conditional " + line + ", will assess whether to stop."
        elif matched_kind == BreakpointRelatedMessageKind.BREAKPOINT_HIT:
            line = "Regular " + line
        else:
            line = line + " in the wrapped jdb process itself."         

        if terminated_with_newline:
            line = line + "\n"
        return line

    @override
    def _get_resume_execution_command(self) -> str:
        return "cont"
        