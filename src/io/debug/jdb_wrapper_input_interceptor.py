from typing import Optional
from typing_extensions import override

from src.io.debug.breakpoint_related_message_kind import BreakpointRelatedCommandKind
from src.io.debug.abstract_debugger_wrapper_input_interceptor import AbstractDebuggerWrapperInputInterceptor
from src.process.debug.breakpoints import BreakpointKind, BreakpointManager, BaseBreakpoint, ConditionalBreakpoint
from src.utils.custom_exceptions import CommandMalformedException


class JDBWrapperInputInterceptor(AbstractDebuggerWrapperInputInterceptor):
    def __init__(self, breakpoint_manager: BreakpointManager):
        self.breakpoint_manager: BreakpointManager = breakpoint_manager
        super().__init__()


    @override
    def _try_get_breakpoint_related_command_type_match(self, command: str) -> Optional[BreakpointRelatedCommandKind]:
        if command.startswith("stop in ") or command.startswith("stop at "):
            command_parts = command.split()
            if len(command_parts) < 3:
                raise CommandMalformedException(f"Malformed command: '{command}'")
            
            if len(command_parts) == 3:
                return BreakpointRelatedCommandKind.SET_REGULAR_BREAKPOINT
            elif len(command_parts) >= 5 and command_parts[3] == "if":
                return BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT
            else:
                raise CommandMalformedException(f"Malformed exception: '{command}'")
        elif command == "clear" or command == "list breakpoints" or command == "show breakpoints":
            return BreakpointRelatedCommandKind.LIST_BREAKPOINTS
        elif command.startswith("clear "):
            if command.startswith("clear conditional "):
                return BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT
            else:
                return BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT

        return None    

    @override
    def _handle_breakpoint_related_command(self, matched_kind: BreakpointRelatedCommandKind, command: str) -> Optional[str]:
        if matched_kind == BreakpointRelatedCommandKind.LIST_BREAKPOINTS:
            print(self.breakpoint_manager.get_current_state_message(), end="\n\n")
            return
        if BreakpointRelatedCommandKind.is_set_kind(matched_kind):
            

    
