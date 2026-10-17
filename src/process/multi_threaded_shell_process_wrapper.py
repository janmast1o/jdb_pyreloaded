import threading
import time

from typing_extensions import override

from src.process.abstract_shell_process_wrapper import *
from src.io.terminal_input_consumer import TerminalInputConsumer
from src.io.multi_threaded_wrapped_process_stdout_sink import MultiThreadedWrappedProcessStdoutSink
from src.utils.util_objects import BooleanWrapper


class MultiThreadedShellProcessWrapper(AbstractShellProcessWrapper):
    def __init__(self, wrapping_session_options: WrappingSessionOptions,
                 ignore_wrapped_process_input_line: bool = True,
                 run_in_main_thread: bool = True,
                 start_immediately: bool = True,
                 exit_keyword: str = "exit",
                 stdout=sys.stdout,
                 stderr=sys.stderr,
                 input_for_wrapping_session = None,
                 wait_time_per_spin_while_waiting_for_prompt_ms: int = 200,
                 min_time_between_prompt_displays_ms: int = 200):
        # Not annotating this as Optional because it is never meant to be None
        # if the wrapped process has been started
        self._wrapped_process_output_reading_thread: threading.Thread = None
        self._wrapped_process_sink: MultiThreadedWrappedProcessStdoutSink = None
        # Divide by one thousand to get seconds from milliseconds
        self._wait_time_per_spin_while_waiting_for_prompt: float = wait_time_per_spin_while_waiting_for_prompt_ms * 1e-3
        self._min_wait_time_between_prompt_displays: float = min_time_between_prompt_displays_ms * 1e-3

        self._can_display_wrapping_process_prompt: BooleanWrapper = BooleanWrapper(True)
        self._wrapping_process_prompt_displayed: BooleanWrapper = BooleanWrapper(False)
        self._ignore_command_from_prompt: BooleanWrapper = BooleanWrapper(False)
        self._terminal_input_consumer: TerminalInputConsumer = TerminalInputConsumer()
        self._terminal_input_consumer.put_terminal_in_cbreak_mode_if_unix()
        self._prompt_method_exited_cv: threading.Condition = threading.Condition()
        super().__init__(
            wrapping_session_options,
            ignore_wrapped_process_input_line,
            run_in_main_thread, start_immediately,
            exit_keyword, stdout, stderr, input_for_wrapping_session
        )

    def _start_wrapped_process_reading_thread(self) -> None:
        # This is a simplified re-implementation of the code
        # from `expect_loop` in `pexpect.Expecter` with only elements relevant
        # for our use case (redirecting output to stdout, but ignoring matching
        # expected patterns). Might need tweaking to work correctly.
        def internal_wrapped_process_reading_loop_function():
            try:
                wrapped_process: pexpect.spawn = self._wrapped_process
                while self._keep_running:
                    try:
                        wrapped_process.read_nonblocking(wrapped_process.maxread, None)
                    except pexpect.TIMEOUT:
                        # Do not do anything if nothing can be read from 
                        # the child process as in this multithreaded mode this can
                        # be considered normal behavior
                        pass
                    except Exception as e:
                        # print(f"Got unexpected exception: {str(e)}, will resume anyway")
                        continue
                    if wrapped_process.delayafterread is not None:
                        time.sleep(wrapped_process.delayafterread) 
            except KeyboardInterrupt:
                return
            except OSError as e:
                # Errno 9 == bad file descriptor
                if e.errno == 9:
                    print("Stopped reading output of the wrapped process")
                    return
                raise e

        self._wrapped_process_output_reading_thread = threading.Thread(target=internal_wrapped_process_reading_loop_function)
        self._wrapped_process_output_reading_thread.start()

    @override
    def _execute_command_in_wrapped_process(self, command: str) -> None:
        if self._ignore_command_from_prompt:
            return
        self._notify_wrapped_process_sink_of_last_command(command)
        self._wrapped_process.sendline(command.strip())

    @override
    def _start_wrapped_process(self) -> None:
        wrapped_process_start_kwargs = self._get_wrapped_process_start_kwargs()
        self._wrapped_process = pexpect.spawn(**wrapped_process_start_kwargs)
        self._wrapped_process.logfile = None
        self._wrapped_process_sink = MultiThreadedWrappedProcessStdoutSink(
            input_line_match_pattern=self._create_input_line_match_pattern(),
            ignore_input_line=self._ignore_wrapped_process_input_line,
            can_display_wrapping_process_prompt=self._can_display_wrapping_process_prompt,
            wrapping_process_prompt_displayed=self._wrapping_process_prompt_displayed,
            ignore_command_from_prompt=self._ignore_command_from_prompt,
            io_sink=self._stdout,
            optional_output_interceptor=self._create_output_interceptor()
        )
        self._wrapped_process.logfile_read = self._wrapped_process_sink
        self._wrapped_process.logfile_send = None
        self._start_wrapped_process_reading_thread()

    @override
    def _start_wrapping_session(self) -> None:
        self._wrapping_session = PromptSession(
            completer=self._create_completer(),
            complete_while_typing=self._wrapping_session_options.complete_while_typing,
            complete_in_thread=self._wrapping_session_options.complete_in_thread,
            input=self._input_for_wrapping_session,
            reserve_space_for_menu=0 # TODO: Add this as an option
        )

    @override
    def _read_command_from_wrapping_session_prompt(self) -> str:
        while not self._can_display_wrapping_process_prompt:
            time.sleep(self._wait_time_per_spin_while_waiting_for_prompt)

        while True:
            time.sleep(self._min_wait_time_between_prompt_displays)
            if self._can_display_wrapping_process_prompt:
                break
            else:
                continue

        # Right before entering `prompt()` method clean anything that might
        # be in the buffer, ie. something that was written there
        # between `prompt()` calls.
        self._terminal_input_consumer.empty_terminal_buffer_and_discard()

        self._wrapping_process_prompt_displayed.set_value(True)    
        command = super()._read_command_from_wrapping_session_prompt()
        self._wrapping_process_prompt_displayed.set_value(False)
        return command

    @override
    def _handle_prompt_method_call_interrupt(self) -> None:
        self._wrapping_process_prompt_displayed.set_value(False)
        # If necessary notify the sink waiting in the flush method
        while self._wrapped_process_sink.is_flush_awaiting_prompt_method_cv_notify():
            self._wrapped_process_sink.notify_prompt_method_exited_cv()

    @override
    def _start(self) -> None:
        self._can_display_wrapping_process_prompt.set_value(True)
        self._ignore_command_from_prompt.set_value(False)
        try:
            return super()._start()    
        finally: # Putting it here to make sure it always gets executed even if the mainloop was to be exited incorrectly 
            TerminalInputConsumer.put_terminal_back_in_original_state()
    