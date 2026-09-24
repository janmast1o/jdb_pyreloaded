import pexpect
import sys

from typing import List
from typing_extensions import override

from src.process.abstract_shell_process_wrapper import *
from src.io.single_threaded_wrapped_process_stdout_sink import SingleThreadedWrappedProcessStdoutSink
from src.io.special_line_processor import SpecialLineProcessor


class SingleThreadedShellProcessWrapper(AbstractShellProcessWrapper):
    def __init__(self, wrapping_session_options: WrappingSessionOptions, 
                 run_in_main_thread: bool = True, 
                 start_immediately: bool = True, 
                 exit_keyword: str = "exit", 
                 stdout=sys.stdout, 
                 stderr=sys.stderr, 
                 input_for_wrapping_session = None):
        self._wrapped_process_expect_full_list = self._get_wrapped_process_expect_options() + [pexpect.EOF, pexpect.TIMEOUT]
        super().__init__(
            wrapping_session_options, 
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
            special_line_processor=self._create_special_line_processor(),
            io_sink=self._stdout
        )
        self._wrapped_process.logfile_send = None
        self._wrapped_process.expect(self._wrapped_process_expect_full_list)
        print()

