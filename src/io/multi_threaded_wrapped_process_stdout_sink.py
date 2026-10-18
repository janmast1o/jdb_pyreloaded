import io
import signal
import sys
import threading

from typing import Optional, List
from typing_extensions import override

from src.io.abstract_wrapped_process_output_interceptor import AbstractWrappedProcessOutputInterceptor
from src.io.abstract_wrapped_process_stdout_sink import AbstractWrappedProcessStdoutSink
from src.utils.custom_exceptions import ShellProcessWrapperInterruptException
from src.utils.signal_utils import RaiseExceptionAfterReceivingSignal
from src.utils.util_objects import BooleanWrapper, BaseString


MOVE_UP_ONE_LINE_AND_ERASE_LINE = "\033[1A\033[2K"


# NOTE: This class is not thread-safe. In this instance 'multi-threaded' refers
# to the fact that the wrapped process is multi-threaded, `write()` and `flush()`
# methods are still meant to be called from a singular thread.
class MultiThreadedWrappedProcessStdoutSink(AbstractWrappedProcessStdoutSink):
    def __init__(self, input_line_match_pattern: BaseString, 
                 ignore_input_line: bool,
                 can_display_wrapping_process_prompt: BooleanWrapper,
                 wrapping_process_prompt_displayed: BooleanWrapper, 
                 ignore_command_from_prompt: BooleanWrapper,
                 optional_output_interceptor: Optional[AbstractWrappedProcessOutputInterceptor] = None,
                 io_sink: io.TextIOWrapper = sys.stdout):
        super().__init__(input_line_match_pattern, ignore_input_line, optional_output_interceptor, io_sink)
        self._can_display_wrapping_process_prompt: BooleanWrapper = can_display_wrapping_process_prompt
        self._wrapping_process_prompt_displayed: BooleanWrapper = wrapping_process_prompt_displayed
        self._ignore_command_from_prompt: BooleanWrapper = ignore_command_from_prompt
        self._awaiting_post_prompt_method_cv_notify: BooleanWrapper = BooleanWrapper(False)
        self._prompt_method_exited_cv: threading.Condition = threading.Condition()
        self._prompt_method_exited_cv_notify_triggered_in_current_wait: bool = False
        self._any_text_written_to_io_sink: bool = False
        self._contents_to_write_to_io: Optional[str] = None

        # Registering `SIGUSR1` handler to trigger `PromptSession.prompt()` exit.
        # TODO: Consider if there is a place in code which will make it seem more elegant.
        old_sigusr1_handler = signal.signal(
            signal.SIGUSR1, 
            RaiseExceptionAfterReceivingSignal(
                error_type_to_raise=ShellProcessWrapperInterruptException,
                print_on_handler_enter=False,
            ).get_handler()
        )
        # Check if `SIGUSR1` has already been overriden somewhere else in the code
        if old_sigusr1_handler != signal.Handlers.SIG_DFL:
            raise Exception(f"Handler for signal {signal.SIGUSR1.name} has already been overriden in this process")

    def is_flush_awaiting_prompt_method_cv_notify(self) -> bool:
        return self._awaiting_post_prompt_method_cv_notify.get_value()

    def notify_prompt_method_exited_cv(self) -> None:
        with self._prompt_method_exited_cv:
            self._prompt_method_exited_cv.notify()
        self._prompt_method_exited_cv_notify_triggered_in_current_wait = True

    def _write_deferred_contents_to_io_sink(self) -> None:
        if self._contents_to_write_to_io is not None:
            self.io_sink.write(self._contents_to_write_to_io)
        self._contents_to_write_to_io = None    

    def _erase_prompt_line_from_terminal(self) -> None:
        print("\n", end="")
        print("\033[2K\n\033[1A", end="")

    @override
    def write(self, s: str) -> None:
        # This check is based on an assumption formed after empirically observing
        # that whenever this `write` method is called for input passed to wrapped process
        # it is passed by itself. This is not a guarantee and could be a good place
        # to start debugging if some problems regarding console output redirection
        # from wrapped process are encountered.
        if s.strip() == self.line_to_ignore_next_occurrence_of:
            self.line_to_ignore_next_occurrence_of = None
            return

        s_lines = self._split_text_into_lines(s)
        s_lines = self._maybe_add_last_call_trailing_unfinished_line(s_lines)
        # Might look clearer without De Morgan's law applied:
        # (not an input line) and (doesn't end with newline)
        last_is_an_input_line = self._is_input_line(s_lines[-1])
        if not (last_is_an_input_line or s_lines[-1].endswith("\n")):
            self._last_write_call_trailing_unfinished_line = s_lines.pop(-1)
        elif last_is_an_input_line:
            if self._ignore_input_line:
                s_lines.pop(-1)
            else:
                s_lines[-1] = s_lines[-1] + "\n"

        if self._optional_output_interceptor is not None:
            s_lines = self._optional_output_interceptor.intercept_on_write(s_lines)        

        # We need to defer the write to `io_sink`
        self._contents_to_write_to_io = "".join(s_lines)
        self._any_text_written_to_io_sink = True

    @override
    def flush(self) -> None: 
        if not self._any_text_written_to_io_sink:
            self._write_deferred_contents_to_io_sink()
            super().flush()
        elif self._wrapping_process_prompt_displayed:
            self._can_display_wrapping_process_prompt.set_value(False)
            self._ignore_command_from_prompt.set_value(True)

            self._awaiting_post_prompt_method_cv_notify.set_value(True)
            self._prompt_method_exited_cv_notify_triggered_in_current_wait = False
            with self._prompt_method_exited_cv:
                # Wait for `prompt` method call to exit and only then proceed
                signal.raise_signal(signal.SIGUSR1)
                while not self._prompt_method_exited_cv_notify_triggered_in_current_wait:
                    self._prompt_method_exited_cv.wait()

            self._awaiting_post_prompt_method_cv_notify.set_value(False)
            # TODO: Consider if it wouldn't be more convenient to keep
            # the input line we were forced out of. 
            self.io_sink.write(MOVE_UP_ONE_LINE_AND_ERASE_LINE)
            self._write_deferred_contents_to_io_sink()
            super().flush()
            self._ignore_command_from_prompt.set_value(False)
            self._can_display_wrapping_process_prompt.set_value(True)
        else:
            self._write_deferred_contents_to_io_sink()
            super().flush()

        self._any_text_written_to_io_sink = False        
