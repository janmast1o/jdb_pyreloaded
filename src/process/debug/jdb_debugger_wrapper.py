import ipaddress
import os
import sys

from prompt_toolkit.completion import Completer, Completion
from typing import Optional, Dict, Any
from typing_extensions import override

from src.io.abstract_wrapping_process_input_interceptor import AbstractWrappingProcessInputInterceptor
from src.io.abstract_wrapped_process_output_interceptor import AbstractWrappedProcessOutputInterceptor
from src.io.debug.jdb_output_interceptor import JDBOutputInterceptor
from src.io.debug.jdb_wrapper_input_interceptor import JDBWrapperInputInterceptor
from src.process.multi_threaded_shell_process_wrapper import (
    MultiThreadedShellProcessWrapper,
    WrappingSessionOptions
)
from src.process.debug.debugger_wrapper import DebuggerWrapper
from src.utils.util_objects import BaseString, Regex


# TODO: Implement `JDBCompleter`
class JDBCompleter(Completer):
    @override
    def get_completions(self, document, unimportant_complete_event):
        yield Completion("", start_position=0)


class JDBDebuggerWrapper(DebuggerWrapper, MultiThreadedShellProcessWrapper):
    def __init__(self, jvm_process_ip_address: str, jvm_process_port: int,
                 wrapping_session_options: WrappingSessionOptions,
                 ignore_wrapped_process_input_line: bool = False,
                 run_in_main_thread: bool = True,
                 start_immediately: bool = True,
                 exit_keyword: str = "exit",
                 stdout=sys.stdout,
                 stderr=sys.stderr,
                 input_for_wrapping_session = None,
                 wait_time_per_spin_while_waiting_for_prompt_ms: int = 200,
                 min_time_between_prompt_displays_ms: int = 200):
        self._jvm_process_ip_address: str = jvm_process_ip_address
        self._jvm_process_port: int = jvm_process_port
        # Validating ip address
        try:
            ipaddress.ip_address(self._jvm_process_ip_address)
        except ValueError:
            raise Exception(f"IP Address {self._jvm_process_ip_address} is not valid")

        DebuggerWrapper.__init__(self)
        MultiThreadedShellProcessWrapper.__init__(
            self, wrapping_session_options, 
            ignore_wrapped_process_input_line,
            run_in_main_thread, start_immediately,
            exit_keyword, stdout, stderr, input_for_wrapping_session,
            wait_time_per_spin_while_waiting_for_prompt_ms,
            min_time_between_prompt_displays_ms
        )

    @override
    def _create_completer(self) -> Completer:
        return JDBCompleter()

    @override
    def _create_input_interceptor(self) -> Optional[AbstractWrappingProcessInputInterceptor]:
        return JDBWrapperInputInterceptor(self._breakpoint_manager)

    # TODO: Decide if we should also notify wrapped process sink of the command we're sending here
    @override
    def _create_output_interceptor(self) -> Optional[AbstractWrappedProcessOutputInterceptor]:
        return JDBOutputInterceptor(
            lambda command: self._wrapped_process.sendline(command.strip()), self._breakpoint_manager
        )

    @override
    def _get_introduction_message(self) -> str:
        return """Welcome to jdb pyreloaded! 

This jdb wrapper enriches the experience, by adding, among others:
- better arrow key utilization, 
- conditional breakpoints"""

    @override
    def _get_exit_keyword_for_wrapped_process(self) -> str:
        return "exit"

    @override
    def _get_wrapped_process_start_kwargs(self) -> Dict[str, Any]:
        return {
            "command": os.environ["SHELL"],
            "args": [
                '-c',
                f'jdb -attach ' + 
                ("" if self._jvm_process_ip_address == "127.0.0.1" else (self._jvm_process_ip_address + ":")) +
                str(self._jvm_process_port)
            ], 
            "encoding" : "utf-8"
        }

    # Input line can either be empty, be a simple ">", or <thread name>[<thread id>]
    @override
    def _create_input_line_match_pattern(self) -> BaseString:
        return Regex(r"(>?|.+\[\d+\])")
    