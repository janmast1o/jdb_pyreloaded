from platform import processor
from typing import Callable

from prompt_toolkit import PromptSession, Application
from prompt_toolkit.auto_suggest import AutoSuggest
from prompt_toolkit.clipboard import Clipboard, DynamicClipboard
from prompt_toolkit.completion import Completer
from prompt_toolkit.cursor_shapes import AnyCursorShapeConfig, DynamicCursorShapeConfig
from prompt_toolkit.document import Document
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.eventloop import InputHook
from prompt_toolkit.filters import FilterOrBool, has_focus
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.history import History
from prompt_toolkit.input import Input
from prompt_toolkit.key_binding import (
    KeyBindingsBase, 
    merge_key_bindings, 
    ConditionalKeyBindings,
    DynamicKeyBindings
)
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.layout.processors import Processor
from prompt_toolkit.output import ColorDepth, Output
from prompt_toolkit.shortcuts.prompt import (
    CompleteStyle, 
    PromptContinuationText, 
    load_auto_suggest_bindings, 
    load_open_in_editor_bindings, 
    merge_style_transformations,
)
from prompt_toolkit.styles import (
    BaseStyle, 
    DynamicStyle, 
    StyleTransformation, 
    DynamicStyleTransformation, 
    ConditionalStyleTransformation, 
    SwapLightAndDarkStyleTransformation,
)
from prompt_toolkit.validation import Validator
from typing import TypeVar
from typing_extensions import override

from src.process.application_with_interruptable_run import ApplicationWithInterruptableRun
from src.utils.util_objects import BooleanWrapper, ThreadSafeBooleanWrapper


_T = TypeVar("_T")

# Largely rewritten library source code. Such an approach was necessary
# to enable interruptable runs.
class InterruptablePromptSession(PromptSession):
    # Constructor arguments the exact same as for the prompt session
    def __init__(self, message: AnyFormattedText = "", *,
                 multiline: FilterOrBool = False,
                 wrap_lines: FilterOrBool = True,
                 is_password: FilterOrBool = False,
                 vi_mode: bool = False,
                 editing_mode: EditingMode = EditingMode.EMACS,
                 complete_while_typing: FilterOrBool = True,
                 validate_while_typing: FilterOrBool = True,
                 enable_history_search: FilterOrBool = False,
                 search_ignore_case: FilterOrBool = False,
                 lexer: Lexer | None = None,
                 enable_system_prompt: FilterOrBool = False,
                 enable_suspend: FilterOrBool = False,
                 enable_open_in_editor: FilterOrBool = False,
                 validator: Validator | None = None,
                 completer: Completer | None = None,
                 complete_in_thread: bool = False,
                 reserve_space_for_menu: int = 8,
                 complete_style: CompleteStyle = CompleteStyle.COLUMN,
                 auto_suggest: AutoSuggest | None = None,
                 style: BaseStyle | None = None,
                 style_transformation: StyleTransformation | None = None,
                 swap_light_and_dark_colors: FilterOrBool = False,
                 color_depth: ColorDepth | None = None,
                 cursor: AnyCursorShapeConfig = None,
                 include_default_pygments_style: FilterOrBool = True,
                 history: History | None = None,
                 clipboard: Clipboard | None = None,
                 prompt_continuation: PromptContinuationText | None = None,
                 rprompt: AnyFormattedText = None,
                 bottom_toolbar: AnyFormattedText = None,
                 mouse_support: FilterOrBool = False,
                 input_processors: list[processor] | None = None,
                 placeholder: AnyFormattedText | None = None,
                 key_bindings: KeyBindingsBase | None = None,
                 erase_when_done: bool = False,
                 tempfile_suffix: str | Callable[[], str] | None = ".txt",
                 tempfile: str | Callable[[], str] | None = None,
                 refresh_interval: float = 0,
                 show_frame: FilterOrBool = False,
                 input: Input | None = None,
                 output: Output | None = None,
                 interrupt_exception: type[BaseException] = KeyboardInterrupt,
                 eof_exception: type[BaseException] = EOFError):
        self._interrupt_prompt_method_call_boolean_wrapper: BooleanWrapper = ThreadSafeBooleanWrapper.create_empty()
        super().__init__(
            message=message,
            multiline=multiline,
            wrap_lines=wrap_lines,
            is_password=is_password,
            vi_mode=vi_mode,
            editing_mode=editing_mode,
            complete_while_typing=complete_while_typing,
            validate_while_typing=validate_while_typing,
            enable_history_search=enable_history_search,
            search_ignore_case=search_ignore_case,
            lexer=lexer,
            enable_system_prompt=enable_system_prompt,
            enable_suspend=enable_suspend,
            enable_open_in_editor=enable_open_in_editor,
            validator=validator,
            completer=completer,
            complete_in_thread=complete_in_thread,
            reserve_space_for_menu=reserve_space_for_menu,
            complete_style=complete_style,
            auto_suggest=auto_suggest,
            style=style,
            style_transformation=style_transformation,
            swap_light_and_dark_colors=swap_light_and_dark_colors,
            color_depth=color_depth,
            cursor=cursor,
            include_default_pygments_style=include_default_pygments_style,
            history=history,
            clipboard=clipboard,
            prompt_continuation=prompt_continuation,
            rprompt=rprompt,
            bottom_toolbar=bottom_toolbar,
            mouse_support=mouse_support,
            input_processors=input_processors,
            placeholder=placeholder,
            key_bindings=key_bindings,
            erase_when_done=erase_when_done,
            tempfile_suffix=tempfile_suffix,
            tempfile=tempfile,
            refresh_interval=refresh_interval,
            show_frame=show_frame,
            input=input,
            output=output,
            interrupt_exception=interrupt_exception,
            eof_exception=eof_exception
        )

    def interrupt_prompt_method_call(self) -> None:
        self._interrupt_prompt_method_call_boolean_wrapper.set_value(False)

    # Rewrote `PromptSession._create_application()` method to
    # instead return `ApplicationWithInterruptableRun`. Otherwise
    # the implementation remains the same as in the base class. 
    @override
    def _create_application(self, editing_mode: EditingMode, erase_when_done: bool) -> Application[_T]:
        dyncond = self._dyncond
        auto_suggest_bindings = load_auto_suggest_bindings()
        open_in_editor_bindings = load_open_in_editor_bindings()
        prompt_bindings = self._create_prompt_bindings()

        # We create an `ApplicationWithInterruptableRun` object instead of a regular `Application`
        # one like in the source code. This is the only difference from the source code.
        application: ApplicationWithInterruptableRun = ApplicationWithInterruptableRun(
            should_interrupt_boolean_wrapper=self._interrupt_prompt_method_call_boolean_wrapper,
            layout=self.layout,
            style=DynamicStyle(lambda: self.style),
            style_transformation=merge_style_transformations(
                [
                    DynamicStyleTransformation(lambda: self.style_transformation),
                    ConditionalStyleTransformation(
                        SwapLightAndDarkStyleTransformation(),
                        dyncond("swap_light_and_dark_colors")
                    )
                ]
            ),
            include_default_pygments_style=dyncond("include_default_pygments_style"),
            clipboard=DynamicClipboard(lambda: self.clipboard),
            key_bindings=merge_key_bindings(
                [
                    merge_key_bindings(
                        [
                            auto_suggest_bindings,
                            ConditionalKeyBindings(
                                open_in_editor_bindings,
                                dyncond("enable_open_in_editor")
                                & has_focus("DEFAULT_BUFFER"),
                            ),
                            prompt_bindings,
                        ]
                    ),
                    DynamicKeyBindings(lambda: self.key_bindings),
                ]
            ),
            mouse_support=dyncond("mouse_support"),
            editing_mode=editing_mode,
            erase_when_done=erase_when_done,
            reverse_vi_search_direction=True,
            color_depth=lambda: self.color_depth,
            cursor=DynamicCursorShapeConfig(lambda: self.cursor),
            refresh_interval=self.refresh_interval,
            input=self._input,
            output=self._output,
        )

        return application

    @override
    def prompt(self,
               message: AnyFormattedText | None = None,
               *,
               editing_mode: EditingMode | None = None,
               refresh_interval: float | None = None,
               vi_mode: bool | None = None,
               lexer: Lexer | None = None,
               completer: Completer | None = None,
               complete_in_thread: bool | None = None,
               is_password: bool | None = None,
               key_bindings: KeyBindingsBase | None = None,
               bottom_toolbar: AnyFormattedText | None = None,
               style: BaseStyle | None = None,
               color_depth: ColorDepth | None = None,
               cursor: AnyCursorShapeConfig | None = None,
               include_default_pygments_style: FilterOrBool | None = None,
               style_transformation: StyleTransformation | None = None,
               swap_light_and_dark_colors: FilterOrBool | None = None,
               rprompt: AnyFormattedText | None = None,
               multiline: FilterOrBool | None = None,
               prompt_continuation: PromptContinuationText | None = None,
               wrap_lines: FilterOrBool | None = None,
               enable_history_search: FilterOrBool | None = None,
               search_ignore_case: FilterOrBool | None = None,
               complete_while_typing: FilterOrBool | None = None,
               validate_while_typing: FilterOrBool | None = None,
               complete_style: CompleteStyle | None = None,
               auto_suggest: AutoSuggest | None = None,
               validator: Validator | None = None,
               clipboard: Clipboard | None = None,
               mouse_support: FilterOrBool | None = None,
               input_processors: list[Processor] | None = None,
               placeholder: AnyFormattedText | None = None,
               reserve_space_for_menu: int | None = None,
               enable_system_prompt: FilterOrBool | None = None,
               enable_suspend: FilterOrBool | None = None,
               enable_open_in_editor: FilterOrBool | None = None,
               tempfile_suffix: str | Callable[[], str] | None = None,
               tempfile: str | Callable[[], str] | None = None,
               show_frame: FilterOrBool | None = None,
               default: str | Document = "",
               accept_default: bool = False,
               pre_run: Callable[[], None] | None = None,
               set_exception_handler: bool = True,
               handle_sigint: bool = True,
               in_thread: bool = False,
               inputhook: InputHook | None = None) -> _T:
        # Ensure that we will not interrupt prompt method call before calling the
        # implementation from the base class.
        self._interrupt_prompt_method_call_boolean_wrapper.set_value(False)
        return super().prompt(
            message=message, 
            editing_mode=editing_mode, 
            refresh_interval=refresh_interval, 
            vi_mode=vi_mode, lexer=lexer, 
            completer=completer, 
            complete_in_thread=complete_in_thread, 
            is_password=is_password, 
            key_bindings=key_bindings, 
            bottom_toolbar=bottom_toolbar, 
            style=style, 
            color_depth=color_depth, 
            cursor=cursor, 
            include_default_pygments_style=include_default_pygments_style, 
            style_transformation=style_transformation, 
            swap_light_and_dark_colors=swap_light_and_dark_colors, 
            rprompt=rprompt, 
            multiline=multiline, 
            prompt_continuation=prompt_continuation, 
            wrap_lines=wrap_lines, 
            enable_history_search=enable_history_search, 
            search_ignore_case=search_ignore_case, 
            complete_while_typing=complete_while_typing, 
            validate_while_typing=validate_while_typing, 
            complete_style=complete_style, 
            auto_suggest=auto_suggest, 
            validator=validator, 
            clipboard=clipboard, 
            mouse_support=mouse_support, 
            input_processors=input_processors, 
            placeholder=placeholder, 
            reserve_space_for_menu=reserve_space_for_menu, 
            enable_system_prompt=enable_system_prompt, 
            enable_suspend=enable_suspend, 
            enable_open_in_editor=enable_open_in_editor, 
            tempfile_suffix=tempfile_suffix, 
            tempfile=tempfile, 
            show_frame=show_frame, 
            default=default, 
            accept_default=accept_default, 
            pre_run=pre_run, 
            set_exception_handler=set_exception_handler, 
            handle_sigint=handle_sigint, 
            in_thread=in_thread, 
            inputhook=inputhook
        )

        