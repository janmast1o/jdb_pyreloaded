from src.process.internal_use_interceptors_and_completer_creator import InternalUseInterceptorsAndCompleterCreator
from src.process.debug.breakpoints import BreakpointManager

# I had no idea how to organize the class structure cleanly, maybe if I figure something
# better out I'll change the structure.
class DebuggerWrapper(InternalUseInterceptorsAndCompleterCreator):
    def __init__(self):
        self._breakpoint_manager: BreakpointManager = BreakpointManager()




        