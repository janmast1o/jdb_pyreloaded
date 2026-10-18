from enum import Enum
from typing import Dict, Optional, Tuple, Union
from typing_extensions import override, overload

from src.utils.util_functions import parse_to_string_and_pad_to_digits

class BreakpointKind(Enum):
    REGULAR = 1
    CONDITIONAL = 2


class BaseBreakpoint:
    def __init__(self, code_address: str):
        self.code_address: str = code_address

    def get_kind(self) -> BreakpointKind:
        return BreakpointKind.REGULAR


# Only stop execution on breakpoint hit if the associated condition is met.
# If it is evaluated as false, immediately resume execution
class ConditionalBreakpoint(BaseBreakpoint):
    def __init__(self, code_address: str, condition: str):
        super().__init__(code_address)
        self.condition: str = condition    
        self._assert_that_condition_is_well_formed()

    # TODO: Implement advanced form validation
    def _assert_that_condition_is_well_formed(self) -> None:
        pass

    @override
    def get_kind(self) -> BreakpointKind:
        return BreakpointKind.CONDITIONAL

    def merge_other_condition_disjunctive(self, other_condition: str) -> None:
        current_condition: str = self.condition
        new_condition: str = "(" + current_condition + ")" + " || (" + other_condition + ")"
        self.condition = new_condition
        self._assert_that_condition_is_well_formed()

    def merge_other_condition_conjunctive(self, other_condition: str) -> None:
        current_condition: str = self.condition
        new_condition: str = "(" + current_condition + ")" + " && (" + other_condition + ")"
        self.condition = new_condition
        self._assert_that_condition_is_well_formed()   


# TODO: Consider replacing hashmaps with prefix trees to see if
# there may be any significant performance gains to be had.
class BreakpointManager:
    def __init__(self):
        self._regular_breakpoint_counter: int = 0
        self._conditional_breakpoint_counter: int = 0
        # Store pairs of <code_address, <breakpoint_number, breakpoint>>
        self._regular_breakpoints_code_address_map: Dict[str, Tuple[int, BaseBreakpoint]] = {}
        self._conditional_breakpoints_code_address_map: Dict[str, Tuple[int, ConditionalBreakpoint]] = {}
        # Store pairs of <breakpoint_number, code_address>
        self._regular_breakpoints_id_map: Dict[int, str] = {}
        self._conditional_breakpoints_id_map: Dict[int, str] = {}

    def get_code_address_for_regular_breakpoint_from_id(self, breakpoint_id: int) -> str:
        if breakpoint_id not in self._regular_breakpoints_id_map:
            raise Exception(f"No regular breakpoint with id={breakpoint_id}")
        return self._regular_breakpoints_id_map[breakpoint_id]

    def get_code_address_for_conditional_breakpoint_from_id(self, breakpoint_id: int) -> str:
        if breakpoint_id not in self._conditional_breakpoints_id_map:
            raise Exception(f"No conditional breakpoint with id={breakpoint_id}")
        return self._conditional_breakpoints_id_map[breakpoint_id]

    def add_regular_breakpoint(self, code_address: str) -> None:  
        if code_address in self._regular_breakpoints_code_address_map:
            raise Exception(f"Regular breakpoint at: {code_address} already defined")
        self._regular_breakpoint_counter += 1
        breakpoint_id = self._regular_breakpoint_counter
        self._regular_breakpoints_code_address_map[code_address] = (breakpoint_id, BaseBreakpoint(code_address))
        self._regular_breakpoints_id_map[breakpoint_id] = code_address

    def add_conditional_breakpoint(self, code_address: str, condition: str) -> None:
        if code_address in self._conditional_breakpoints_code_address_map:
            self._conditional_breakpoints_code_address_map[code_address][1].merge_other_condition_disjunctive(condition)
        else:
            self._conditional_breakpoint_counter += 1
            breakpoint_id = self._conditional_breakpoint_counter
            self._conditional_breakpoints_code_address_map[code_address] = (breakpoint_id, ConditionalBreakpoint(code_address, condition))
            self._conditional_breakpoints_id_map[breakpoint_id] = code_address

    @overload
    def add_conjunction_to_conditional_breakpoint(self, code_address: str, condition: str) -> None:
        ...

    @overload
    def add_conjunction_to_conditional_breakpoint(self, breakpoint_id: int, condition: str) -> None:
        ...

    def add_conjunction_to_conditional_breakpoint(self, x: Union[int, str], condition: str) -> None:
        if isinstance(x, int):
            breakpoint_id: int = x
            associated_code_address = self._conditional_breakpoints_id_map.get(breakpoint_id, None)
            if associated_code_address is None:
                raise Exception("Cannot add conjunction to a non-existent conditional breakpoint")
            self._conditional_breakpoints_code_address_map[associated_code_address][1].merge_other_condition_conjunctive(condition)    
        elif isinstance(x, str):
            code_address: str = x
            if code_address not in self._conditional_breakpoints_code_address_map:
                raise Exception("Cannot add conjunction to a non-existent conditional breakpoint")
            self._conditional_breakpoints_code_address_map[code_address][1].merge_other_condition_conjunctive(condition)

    # If for a given code address both a regular and conditional breakpoints exist
    # the regular one will take precedence.
    # Returns `None` if no mapping is found.
    def get_condition_type_for_code_address(self, code_address: str) -> Optional[BreakpointKind]:
        if code_address in self._regular_breakpoints_code_address_map:
            return BreakpointKind.REGULAR
        elif code_address in self._conditional_breakpoints_code_address_map:
            return BreakpointKind.CONDITIONAL
        else:
            return None

    # This should be called only if one is certain that 
    # a conditional breakpoint for that code address exists.
    # To do so, call `get_condition_type_for_code_address()` method beforehand.
    def get_condition_for_code_address(self, code_address: str) -> str:
        if code_address not in self._conditional_breakpoints_code_address_map:
            raise Exception(f"No conditional breakpoint corresponding to {code_address}")
        else:
            return self._conditional_breakpoints_code_address_map[code_address][1].condition

    @overload
    def remove_regular_breakpoint(self, breakpoint_number: int) -> None: 
        ...

    @overload
    def remove_regular_breakpoint(self, code_address: str) -> None: 
        ...
        
    def remove_regular_breakpoint(self, x: Union[int, str]) -> None:
        if isinstance(x, int):
            breakpoint_number: int = x
            if breakpoint_number not in self._regular_breakpoints_id_map:
                raise Exception(f"Regular breakpoint with id={breakpoint_number} does not exist")

            associated_code_address = self._regular_breakpoints_id_map[breakpoint_number]
            self._regular_breakpoints_id_map.pop(breakpoint_number)
            self._regular_breakpoints_code_address_map.pop(associated_code_address)
        elif isinstance(x, str):
            code_address: str = x
            if code_address not in self._regular_breakpoints_code_address_map:
                raise Exception(f"Regular breakpoint with code_address={code_address} does not exist")

            associated_id = self._regular_breakpoints_code_address_map[code_address][0]
            self._regular_breakpoints_code_address_map.pop(code_address)
            self._regular_breakpoints_id_map.pop(associated_id)

    @overload
    def remove_conditional_breakpoint(self, breakpoint_number: int) -> None:
        ...

    @overload
    def remove_conditional_breakpoint(self, code_address: str) -> None:
        ...

    def remove_conditional_breakpoint(self, x: Union[int, str]) -> None:
        if isinstance(x, int):
            breakpoint_number: int = x
            if breakpoint_number not in self._conditional_breakpoints_id_map:
                raise Exception(f"Regular breakpoint with id={breakpoint_number} does not exist")

            associated_code_address = self._conditional_breakpoints_id_map[breakpoint_number]
            self._conditional_breakpoints_id_map.pop(breakpoint_number)
            self._conditional_breakpoints_code_address_map.pop(associated_code_address)
        elif isinstance(x, str):
            code_address: str = x    
            if code_address not in self._conditional_breakpoints_code_address_map:
                raise Exception(f"Regular breakpoint with code_address={code_address} does not exist")

            associated_id = self._conditional_breakpoints_code_address_map[code_address][0]
            self._conditional_breakpoints_code_address_map.pop(code_address)
            self._conditional_breakpoints_id_map.pop(associated_id)

    # Returns a list of breakpoints as `str` in easily readable format
    def get_current_state_message(self) -> str:
        lines = ["Regular breakpoints:"]
        sorted_regular_breakpoint_ids = sorted([id for id in self._regular_breakpoints_id_map.keys()])
        
        for id in sorted_regular_breakpoint_ids:
            code_address = self._regular_breakpoints_id_map[id]
            # It is reasonable to assume that someone will probably create no more than 99 breakpoints
            # inside a single debugging session.
            lines.append("{" + f"id={parse_to_string_and_pad_to_digits(id, digits=2)}, code_address={code_address}" + "}")

        lines.append(" ")
        lines.append("Conditional breakpoints:")

        sorted_conditional_breakpoint_ids = sorted([id for id in self._conditional_breakpoints_id_map.keys()])

        for id in sorted_conditional_breakpoint_ids:
            code_address = self._conditional_breakpoints_id_map[id]
            condition = self._conditional_breakpoints_code_address_map[code_address][1].condition
            lines.append(
                "{" + f"id={parse_to_string_and_pad_to_digits(id, digits=2)}, code_address={code_address}" 
                + "\n " + f"condition=({condition})" + "}"
            )

        return "\n".join(lines)

    def remove_all_breakpoints_and_reset_counters(self) -> None:
        self._regular_breakpoint_counter = 0
        self._conditional_breakpoint_counter = 0
        self._regular_breakpoints_code_address_map.clear()
        self._conditional_breakpoints_code_address_map.clear()
        self._regular_breakpoints_id_map.clear() 
        self._conditional_breakpoints_id_map.clear()
        