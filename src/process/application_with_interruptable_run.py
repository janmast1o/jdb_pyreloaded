import asyncio
import asyncio.events as events
import selectors
import sys
import threading

from asyncio import AbstractEventLoop
from prompt_toolkit import Application
from prompt_toolkit.clipboard import Clipboard
from prompt_toolkit.cursor_shapes import AnyCursorShapeConfig
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.eventloop import (
    InputHook, 
    InputHookContext, 
    InputHookSelector
)
from prompt_toolkit.filters import FilterOrBool
from prompt_toolkit.input import Input
from prompt_toolkit.key_binding import KeyBindingsBase
from prompt_toolkit.layout import Layout
from prompt_toolkit.output import ColorDepth, Output
from prompt_toolkit.styles import BaseStyle, StyleTransformation
from types import CoroutineType
from typing import Callable, Union, Optional, TypeVar, Any
from typing_extensions import override

from src.io.interruptable_runner import InterruptableRunner
from src.utils.util_objects import BooleanWrapper


ApplicationEventHandler = Callable[["Application[_AppResult]"], None]
_AppResult = TypeVar("_AppResult")


# Largely rewritten library source code. Such an approach was necessary
# to enable interruptable runs.
class ApplicationWithInterruptableRun(Application):
    def __init__(self, should_interrupt_boolean_wrapper: BooleanWrapper,
                 layout: Layout = None, 
                 style: BaseStyle = None, 
                 include_default_pygments_style: FilterOrBool = True, 
                 style_transformation: StyleTransformation = None, 
                 key_bindings: KeyBindingsBase = None, 
                 clipboard: Clipboard = None, full_screen: bool = False, 
                 color_depth: (ColorDepth | Callable[[], ColorDepth | None] | None) = None, 
                 mouse_support: FilterOrBool = False, 
                 enable_page_navigation_bindings = None, 
                 paste_mode: FilterOrBool = False, 
                 editing_mode: EditingMode = EditingMode.EMACS, 
                 erase_when_done: bool = False, 
                 reverse_vi_search_direction: FilterOrBool = False, 
                 min_redraw_interval: Union[float, int] = None, 
                 max_render_postpone_time: Union[float, int] = 0.01, 
                 refresh_interval: Optional[float] = None, 
                 terminal_size_polling_interval: Optional[float] = 0.5, 
                 cursor: AnyCursorShapeConfig = None, 
                 on_reset: ApplicationEventHandler = None, 
                 on_invalidate: ApplicationEventHandler = None, 
                 before_render: ApplicationEventHandler = None, 
                 after_render: ApplicationEventHandler = None, 
                 input: Optional[Input] = None, 
                 output: Optional[Output] = None):
        super().__init__(
            layout, style, 
            include_default_pygments_style, 
            style_transformation, 
            key_bindings, clipboard, 
            full_screen, color_depth, 
            mouse_support, enable_page_navigation_bindings, 
            paste_mode, editing_mode, erase_when_done, 
            reverse_vi_search_direction, min_redraw_interval, 
            max_render_postpone_time, refresh_interval, 
            terminal_size_polling_interval, cursor, on_reset, 
            on_invalidate, before_render, 
            after_render, input, output
        )
        self._should_interrupt_boolean_wrapper: BooleanWrapper = should_interrupt_boolean_wrapper

    @staticmethod
    def new_eventloop_with_input_hook(inputhook: Callable[[InputHookContext], None]) -> AbstractEventLoop: 
        selector = InputHookSelector(selectors.DefaultSelector(), inputhook)
        # Possibly a place in code to change for the purposes of the project,
        # not sure yet.
        loop = asyncio.SelectorEventLoop(selector)
        return loop

    # Rewrote `asyncio.run()`, but omitted `debug` kwarg, since
    # it is not important in this instance.
    def _run_interruptable_coroutine(self, coroutine: CoroutineType) -> Any:
        if events._get_running_loop() is not None:
            raise RuntimeError(
                "ApplicationWithInterruptableRun.run_interruptable_coroutine() cannot be called from a running event loop"
            )
        
        with InterruptableRunner(self._should_interrupt_boolean_wrapper) as runner:
            return runner.run(coroutine)
        

    @override
    def run(self, pre_run: Optional[Callable[[], None]] = None, 
            set_exception_handler: bool = True, 
            handle_sigint: bool = True, in_thread = False, inputhook: InputHook = None):
        if in_thread:
            result: _AppResult = None
            exception: Optional[BaseException] = None

            def run_in_thread() -> None:
                nonlocal result, exception
                try:
                    result = self.run(
                        pre_run=pre_run,
                        set_exception_handler=set_exception_handler,
                        # Signal handling only works in the main thread.
                        handle_sigint=False,
                        inputhook=inputhook,
                    )
                except BaseException as e:
                    exception = e

            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()

            if exception is not None:
                raise exception
            return result

        coroutine = self.run_async(
            pre_run=pre_run,
            set_exception_handler=set_exception_handler,
            handle_sigint=handle_sigint,
        )

        def _called_from_ipython() -> bool:
            try:
                return (
                    sys.modules["IPython"].version_info < (8, 18, 0, "")
                    and "IPython/terminal/interactiveshell.py"
                    in sys._getframe(3).f_code.co_filename
                )
            except BaseException:
                return False

        if inputhook is not None:
            # See the method definition if problems with interrupting are encountered.
            loop = ApplicationWithInterruptableRun.new_eventloop_with_inputhook(inputhook)
            result = loop.run_until_complete(coroutine)
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            return result

        elif _called_from_ipython():
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # Changed from `asyncio.run(coroutine)`
                return self._run_interruptable_coroutine(coroutine)
            else:
                # Change also this bit of code to appropriate interruptable logic here
                return loop.run_until_complete(coroutine)

        else:
            # Changed from `asyncio.run(coroutine)`
            return self._run_interruptable_coroutine(coroutine)

    