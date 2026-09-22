import asyncio

from src.io.interruptable_loop_wrapper import InterruptableLoopWrapperFactory
from src.utils.util_objects import BooleanWrapper
        

class InterruptableRunner(asyncio.Runner):
    def __init__(self, should_interrupt_boolean_wrapper: BooleanWrapper, *, debug = None):
        super().__init__(
            debug=debug, 
            loop_factory=InterruptableLoopWrapperFactory(should_interrupt_boolean_wrapper)
        )