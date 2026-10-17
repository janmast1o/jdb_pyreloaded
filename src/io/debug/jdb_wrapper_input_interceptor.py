import re

from typing import Optional, Tuple, Union, List
from typing_extensions import override

from src.io.debug.breakpoint_related_message_kind import BreakpointRelatedCommandKind
from src.io.debug.abstract_debugger_wrapper_input_interceptor import AbstractDebuggerWrapperInputInterceptor
from src.process.debug.breakpoints import BreakpointKind, BreakpointManager, BaseBreakpoint, ConditionalBreakpoint
from src.utils.custom_exceptions import CommandMalformedException


class JDBWrapperInputInterceptor(AbstractDebuggerWrapperInputInterceptor):
    def __init__(self, breakpoint_manager: BreakpointManager):
        self._breakpoint_manager: BreakpointManager = breakpoint_manager
        super().__init__()

    # For remove statements `code_address` can also refer to the breakpoint id. 
    def _get_code_address_and_try_get_condition_for_command(self, matched_kind: BreakpointRelatedCommandKind, c: Union[str, List[str]]) -> Tuple[str, Optional[str]]:
        command_parts: List[str] = None
        if isinstance(c, str): # Passed as command
            command_parts = c.split()
        elif isinstance(c, list):
            command_parts = c    
        
        if matched_kind == BreakpointRelatedCommandKind.SET_REGULAR_BREAKPOINT:
            return command_parts[2], None
        elif matched_kind == BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT:
            return command_parts[2], " ".join(command_parts[4:])
        elif matched_kind == BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT:
            return command_parts[1], None
        elif matched_kind == BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT:
            return command_parts[2], None
        else:
            raise CommandMalformedException(f"Couldn't match {matched_kind} to any branches in the conditional block")

    @override
    def _try_get_breakpoint_related_command_type_match(self, command: str) -> Optional[BreakpointRelatedCommandKind]:
        if command.startswith("stop in") or command.startswith("stop at"):
            command_parts = command.split()
            if len(command_parts) < 3:
                raise CommandMalformedException(f"Malformed command: '{command}'")
            
            if len(command_parts) == 3:
                return BreakpointRelatedCommandKind.SET_REGULAR_BREAKPOINT
            elif len(command_parts) >= 5 and command_parts[3] == "if":
                return BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT
            else:
                raise CommandMalformedException(f"Malformed exception: '{command}'")
        # TODO: Consider reworking this to regular string comparison if regex matching proves too inefficient    
        elif command == "clear" or re.match(r"list( all)? breakpoints", command) or re.match(r"show( all)? breakpoints", command):
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
            print(self._breakpoint_manager.get_current_state_message(), end="\n\n")
            return

        # Defining these variables earlier to make use of type hinting.
        code_address: str = None
        optional_condition: Optional[str] = None
        command_parts = command.split()
        code_address, optional_condition = self._get_code_address_and_try_get_condition_for_command(matched_kind, command_parts)

        # Multiple `if` statements instead of one `if-elif-else` block to 
        # improve readability.
        if matched_kind == BreakpointRelatedCommandKind.SET_REGULAR_BREAKPOINT:
            # We already set the breakpoint in jdb
            if self._breakpoint_manager.get_condition_type_for_code_address(code_address) is not None:
                command = None
            self._breakpoint_manager.add_regular_breakpoint(code_address)
            return command
        
        if matched_kind == BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT:
            # We already set the breakpoint in jdb
            if self._breakpoint_manager.get_condition_type_for_code_address(code_address) is not None:
                command = None
            self._breakpoint_manager.add_conditional_breakpoint(code_address, optional_condition)
            return " ".join(command_parts[:3]) if command is not None else None

        if matched_kind == BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT:
            # Accommodating removals with breakpoint ids
            try:
                breakpoint_id = int(code_address)
                code_address = self._breakpoint_manager.get_code_address_for_regular_breakpoint_from_id(breakpoint_id)
            except ValueError:
                pass    

            self._breakpoint_manager.remove_regular_breakpoint(code_address)
            # Conditional breakpoints still exists we should not delete it in jdb
            if self._breakpoint_manager.get_condition_type_for_code_address(code_address) is not None:
                return None
            else:
                return f"clear {code_address}"    
        
        if matched_kind == BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT:
            # Accommodating removals with breakpoint ids
            try:
                breakpoint_id = int(code_address)
                code_address = self._breakpoint_manager.get_code_address_for_conditional_breakpoint_from_id(breakpoint_id)
            except ValueError:
                pass 

            self._breakpoint_manager.remove_conditional_breakpoint(code_address)
            # Regular breakpoint still exists we should not delete it in jdb
            if self._breakpoint_manager.get_condition_type_for_code_address(code_address) is not None:
                return None
            else:
                return f"clear {code_address}"
        
        raise CommandMalformedException(f"Couldn't handle breakpoint related command")
