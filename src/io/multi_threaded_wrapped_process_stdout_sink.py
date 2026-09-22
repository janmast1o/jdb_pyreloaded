import io
import signal
import sys
import threading

from typing import Optional
from typing_extensions import override

from src.io.abstract_wrapped_process_stdout_sink import AbstractWrappedProcessStdoutSink
from src.io.special_line_processor import SpecialLineProcessor
from src.utils.custom_exceptions import ShellProcessWrapperInterruptException
from src.utils.signal_utils import RaiseExceptionAfterReceivingSignal
from src.utils.util_objects import BooleanWrapper

# NOTE: This class is not thread-safe. In this instance 'multi-threaded' refers
# to the fact that the wrapped process is multi-threaded, `write()` and `flush()`
# methods are still meant to be called from a singular thread.
class MultiThreadedWrappedProcessStdoutSink(AbstractWrappedProcessStdoutSink):
    def __init__(self, special_line_processor: SpecialLineProcessor, 
                 can_display_wrapping_process_prompt: BooleanWrapper,
                 wrapping_process_prompt_displayed: BooleanWrapper, 
                 ignore_command_from_prompt: BooleanWrapper,
                 io_sink: io.TextIOWrapper = sys.stdout):
        super().__init__(special_line_processor, io_sink)
        self._can_display_wrapping_process_prompt: BooleanWrapper = can_display_wrapping_process_prompt
        self._wrapping_process_prompt_displayed: BooleanWrapper = wrapping_process_prompt_displayed
        self._ignore_command_from_prompt: BooleanWrapper = ignore_command_from_prompt
        self._awaiting_post_prompt_method_cv_notify: BooleanWrapper = BooleanWrapper(False)
        self._prompt_method_exited_cv: threading.Condition = threading.Condition()
        self._prompt_method_exited_cv_notify_triggered_in_current_wait: bool = False
        self._any_text_written_to_io_sink: bool = False

        # Registering `SIGUSR1` handler to trigger `PromptSession.prompt()` exit.
        # TODO: Consider if there is a place in code which will make it seem more elegant.
        old_sigusr1_handler = signal.signal(
            signal.SIGUSR1, 
            RaiseExceptionAfterReceivingSignal(error_type_to_raise=ShellProcessWrapperInterruptException).get_handler()
        )
        # Check if `SIGUSR1` has already been overriden somewhere else in the code
        if old_sigusr1_handler != signal.Handlers.SIG_DFL:
            raise Exception(f"Handler for signal {signal.SIGUSR1.name} has already been overriden in this process")

        # self._terminal_input_consumer: Optional[TerminalInputConsumer] = None
        # if self._stdin_source is sys.stdin:
        #     self._terminal_input_consumer = TerminalInputConsumer()
        #     self._terminal_input_consumer.put_terminal_in_cbreak_mode_if_unix()

    def is_flush_awaiting_prompt_method_cv_notify(self) -> bool:
        return self._awaiting_post_prompt_method_cv_notify.get_value()

    def notify_prompt_method_exited_cv(self) -> None:
        with self._prompt_method_exited_cv:
            self._prompt_method_exited_cv.notify()
        self._prompt_method_exited_cv_notify_triggered_in_current_wait = True

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

        separate_lines = s.splitlines(keepends=True)
        processed_lines = []
        for line in separate_lines:
            i = self._special_line_processor.maybe_get_matching_special_line_index(line)
            if i is None:
                processed_lines.append(line)
            else:
                processed_special_line = self._special_line_processor.apply_to_line_of_type(i, line)
                if processed_special_line is not None:
                    line_terminated_with_newline = len(line) > 0 and line[-1] == "\n"
                    processed_lines.append(processed_special_line + "\n" if line_terminated_with_newline else "")

        if len(processed_lines) == 0:
            return 

        self.io_sink.write("".join(processed_lines))   
        self._any_text_written_to_io_sink = True

    @override
    def flush(self) -> None: 
        if not self._any_text_written_to_io_sink:
            super().flush()
        elif self._wrapping_process_prompt_displayed:
            self._can_display_wrapping_process_prompt.set_value(False)
            self._ignore_command_from_prompt.set_value(True)

            self._awaiting_post_prompt_method_cv_notify.set_value(True)
            self._prompt_method_exited_cv_notify_triggered_in_current_wait = False
            with self._prompt_method_exited_cv:
                # Wait for `prompt` method call to exit and only then proceed
                signal.raise_signal(signal.SIGUSR1)
                print("Entering cv waiting block")
                while not self._prompt_method_exited_cv_notify_triggered_in_current_wait:
                    print("Started waiting")
                    self._prompt_method_exited_cv.wait()
                    print("Woke up")
                print("Proceeding")    

            self._awaiting_post_prompt_method_cv_notify.set_value(False)    

            # if self._terminal_input_consumer is not None:
            #     written_to_terminal = self._terminal_input_consumer.empty_terminal_buffer_and_return_result()
            #     print("Written to terminal: ", written_to_terminal)
            
            # self._wrapping_process_prompt_displayed.value = False
            self._erase_prompt_line_from_terminal()

            # if self._terminal_input_consumer is not None:
                # written_to_terminal = self._terminal_input_consumer.empty_terminal_buffer_and_return_result()
                # print("Written to terminal: ", written_to_terminal)

            super().flush()
            self._ignore_command_from_prompt.set_value(False)
            self._can_display_wrapping_process_prompt.set_value(True)
        else:
            super().flush()

        self._any_text_written_to_io_sink = False        


