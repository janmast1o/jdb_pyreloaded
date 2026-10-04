from enum import Enum


# These values were chosen to allow for quickly comparing against subsets of enum values
# Output
class BreakpointRelatedMessageKind(Enum):
    DEFERRING_BREAKPOINT = 1 << 1
    BREAKPOINT_SET = 1 << 2
    BREAKPOINT_REMOVED = 1 << 3
    BREAKPOINTS_LISTED_HEADER = 1 << 4
    BREAKPOINT_HIT = 1 << 5
    ENTRY_IN_BREAKPOINT_LIST = 1 << 6


# Input
class BreakpointRelatedCommandKind(Enum):
    SET_REGULAR_BREAKPOINT = 1 << 1
    SET_CONDITIONAL_BREAKPOINT = 1 << 2
    REMOVE_REGULAR_BREAKPOINT = 1 << 3
    REMOVE_CONDITIONAL_BREAKPOINT = 1 << 4
    LIST_BREAKPOINTS = 1 << 5   

    @staticmethod
    def is_set_kind(breakpoint_related_command_type: "BreakpointRelatedCommandKind") -> bool:
        return breakpoint_related_command_type & (
            BreakpointRelatedCommandKind.SET_REGULAR_BREAKPOINT |
            BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT
        ) != 0

    @staticmethod
    def is_remove_kind(breakpoint_related_command_type: "BreakpointRelatedCommandKind") -> bool:
        return breakpoint_related_command_type & (
            BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT | 
            BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT
        ) != 0