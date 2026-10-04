from abc import abstractmethod

from src.process.debug.breakpoints import BaseBreakpoint, ConditionalBreakpoint, BreakpointManager

# I had no idea how to organize the class structure cleanly, maybe if I figure something
# better out I'll change the structure.
class DebuggerWrapper:
    def __init__(self):
        self.breakpoint_manager: BreakpointManager = BreakpointManager()




        