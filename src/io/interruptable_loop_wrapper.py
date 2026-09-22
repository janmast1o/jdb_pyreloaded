import asyncio
import sys
import threading

from types import CoroutineType
from typing import Any, Callable
from typing_extensions import override

from src.utils.util_objects import BooleanWrapper


# Copied from `asyncio` library.
def _run_until_complete_cb(future: asyncio.Future):
    if not future.cancelled():
        exc = future.exception()
        if isinstance(exc, (SystemExit, KeyboardInterrupt)):
            return
    asyncio.futures._get_loop(future).stop()


class InterruptableLoopWrapperFactory:
    def __init__(self, should_interrupt_boolean_wrapper: BooleanWrapper):
        self._should_interrupt_boolean_wrapper: BooleanWrapper = should_interrupt_boolean_wrapper

    def __call__(self, *args, **kwargs):
        return InterruptableLoopWrapper(
            loop=asyncio.events.new_event_loop(),
            should_interrupt_boolean_wrapper=self._should_interrupt_boolean_wrapper
        )    


class InterruptableLoopWrapper:
    def __init__(self, loop: asyncio.BaseEventLoop, 
                 should_interrupt_boolean_wrapper: BooleanWrapper):
        self.loop: asyncio.BaseEventLoop = loop
        self._should_interrupt_boolean_wrapper: BooleanWrapper = should_interrupt_boolean_wrapper

    async def shutdown_asyncgens(self) -> CoroutineType:
        return self.loop.shutdown_asyncgens()    

    async def shutdown_default_executor(self) -> Any:
        return self.shutdown_default_executor()

    def create_future(self) -> asyncio.futures.Future:
        return self.loop.create_future()

    def create_task(self, coroutine: CoroutineType, *, 
                    name: str = None, context: Any = None) -> asyncio.tasks.Task:
        return self.loop.create_task(coro=coroutine, name=name, context=context)

    def set_debug(self, debug: bool) -> None:
        self.loop.set_debug(debug)

    def call_soon_threadsafe(self, function: Callable) -> Any:
        return self.loop.call_soon_threadsafe(function)

    def run_until_complete(self, future: asyncio.Future) -> Any:
        # No idea why these method calls are not recognized
        self.loop._check_closed()
        self.loop._check_running()

        new_task = not asyncio.futures.isfuture(future)
        future = asyncio.tasks.ensure_future(future, loop=self.loop)
        if new_task:
            future._log_destroy_pending = False

        future.add_done_callback(asyncio.base_events)
        try:
            self.run_forever()
        except:
            if new_task and future.done() and not future.cancelled():
                future.exception()
            raise
        finally:
            future.remove_done_callback(_run_until_complete_cb)

        if not future.done():
            raise RuntimeError("Event loop stopped before Future completed")

        return future.result()        

    def run_forever(self) -> Any:
        # No idea why these method calls are not recognized
        self.loop._check_closed()
        self.loop._check_running()    
        self.loop._set_coroutine_origin_tracking(self.loop._debug)
        self.loop._thread_id = threading.get_ident()

        old_agen_hooks = sys.get_asyncgen_hooks()
        sys.set_asyncgen_hooks(
            firstiter=self.loop._asyncgen_firstiter_hook,
            finalizer=self.loop._asyncgen_finalizer_hook
        )

        try:
            asyncio.events._set_running_loop(self.loop)
            # `while` being conditional the difference introduced from the regular loop object.
            while not self._should_interrupt_boolean_wrapper:
                self.loop._run_once()
                if self.loop._stopping:
                    break    
        finally:
            self.loop._stopping = False
            self.loop._thread_id = None
            asyncio.events._set_running_loop(None)
            self.loop._set_coroutine_origin_tracking(False)
            sys.set_asyncgen_hooks(*old_agen_hooks)

            # Resetting `self.should_interrupt`
            self._should_interrupt_boolean_wrapper.set_value(False)    

    def close(self) -> None:
        self.loop.close()            