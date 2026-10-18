import pexpect
import sys

from typing import List
from typing_extensions import override

from src.process.abstract_shell_process_wrapper import *
from src.io.single_threaded_wrapped_process_stdout_sink import SingleThreadedWrappedProcessStdoutSink


class SingleThreadedShellProcessWrapper(AbstractShellProcessWrapper):
    def __init__(self, wrapping_session_options: WrappingSessionOptions, 
                 ignore_wrapped_process_input_line: bool = True,
                 run_in_main_thread: bool = True, 
                 start_immediately: bool = True, 
                 exit_keyword: str = "exit", 
                 stdout=sys.stdout, 
                 stderr=sys.stderr, 
                 input_for_wrapping_session = None):
        self._wrapped_process_expect_full_list = self._get_wrapped_process_expect_options() + [pexpect.EOF, pexpect.TIMEOUT]
        super().__init__(
            wrapping_session_options, 
            ignore_wrapped_process_input_line,
            run_in_main_thread, start_immediately, 
            exit_keyword, stdout, stderr, input_for_wrapping_session    
        )    

    @abstractmethod
    def _get_wrapped_process_expect_options(self) -> List[str]:
        pass

    @override
    def _execute_command_in_wrapped_process(self, command: str) -> None:
        self._notify_wrapped_process_sink_of_last_command(command)
        self._wrapped_process.sendline(command.strip())  
        self._wrapped_process.expect(self._wrapped_process_expect_full_list)
        print()

    @override
    def _start_wrapped_process(self) -> None:
        wrapped_process_start_kwargs = self._get_wrapped_process_start_kwargs()
        self._wrapped_process = pexpect.spawn(**wrapped_process_start_kwargs)
        self._wrapped_process.logfile = None
        self._wrapped_process.logfile_read = SingleThreadedWrappedProcessStdoutSink(
            input_line_match_pattern=self._create_input_line_match_pattern(),
            ignore_input_line=self._ignore_wrapped_process_input_line,
            io_sink=self._stdout,
            optional_output_interceptor=self._create_output_interceptor()
        )
        self._wrapped_process.logfile_send = None
        self._wrapped_process.expect(self._wrapped_process_expect_full_list)
        print()

