# import contextlib
import pexpect
import sys
import threading

from abc import ABC as AbstractClass, abstractmethod
# from subprocess import Popen
from typing import Union, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.input import Input
from prompt_toolkit.completion import Completer, Completion

class WrappingSessionOptions:
    def __init__(self, line_begin_marker: str,
                 complete_while_typing: bool = False,
                 complete_in_thread: bool = False):
        self.line_begin_marker: str = line_begin_marker
        self.complete_while_typing: bool = complete_while_typing
        self.complete_in_thread: bool = complete_in_thread
        
# If wrapping process is meant to use `sys.stdin` as input
# set `input_for_wrapping_session` to `None`
class ShellProcessWrapper(AbstractClass):
    def __init__(self, wrapping_session_options: WrappingSessionOptions, 
                 run_in_main_thread: bool = True, 
                 start_immediately: bool = True, 
                 exit_keyword: str = "exit", 
                 stdout = sys.stdout, stderr = sys.stderr, 
                 input_for_wrapping_session: Optional[Input] = None):
        self._wrapped_process: pexpect.spawn = None
        self._wrapping_session: PromptSession = None
        self._wrapping_session_options: WrappingSessionOptions = wrapping_session_options
        self._run_in_main_thread: bool = run_in_main_thread

        self._exit_keyword = exit_keyword
        self._stdout = stdout
        self._stderr = stderr
        self._input_for_wrapping_session = input_for_wrapping_session
        self._thread: Optional[threading.Thread] = None

        if start_immediately:
            self._start()

    @property
    def runs_in_main_thread(self) -> bool:
        return self._run_in_main_thread

    def maybe_get_thread(self) -> Optional[threading.Thread]:
        return self._thread

    @abstractmethod
    def _get_introduction_message(self) -> str:
        pass

    # Completer creation is tied to how the wrapped process works,
    # hence it's marked as abstract and has to be implented in 
    # inheriting class
    @abstractmethod
    def _create_completer(self) -> Completer:
        pass

    @abstractmethod
    def _get_exit_keyword_for_wrapped_process(self) -> str:
        pass

    # Returns normalized command, suitable to be sent to the wrapped process
    @abstractmethod
    def _normalize_command_and_try_change_command_execution_logic(self, command: str) -> str:
        pass

    @abstractmethod
    def _execute_command_in_wrapped_process(self, command) -> None:
        pass

    @abstractmethod
    def _start_wrapped_process(self) -> None:
        pass

    @abstractmethod
    def _handle_wrapped_process_shutdown(self) -> None:
        pass

    def _start_wrapping_session(self) -> None:
        self._wrapping_session = PromptSession(
            completer=self._create_completer(), 
            complete_while_typing=self._wrapping_session_options.complete_while_typing, 
            complete_in_thread=self._wrapping_session_options.complete_in_thread, 
            input=self._input_for_wrapping_session
        )

        print(self._get_introduction_message())

    # TODO: Implement stdout, stdin, stderr redirection
    # Returns:
    #   - None: if the process wrapper is meant to start in the main thread
    #   - threading.Thread: if the process is meant to start in a separate thread
    def _start(self) -> Union[None, threading.Thread]:
        def internal_start_function():
            line_begin_marker = self._wrapping_session_options.line_begin_marker
            self._start_wrapped_process()
            self._start_wrapping_session()

            keep_running = True
            while keep_running:
                try:
                    command: str = self._wrapping_session.prompt(line_begin_marker)
                    command = command.strip()
                    if command == self._exit_keyword:
                        command = self._get_exit_keyword_for_wrapped_process()
                        keep_running = False

                    normalized_command = self._normalize_command_and_try_change_command_execution_logic(command)
                    self._execute_command_in_wrapped_process(normalized_command)
                except KeyboardInterrupt:
                    continue
                except EOFError:
                    break

            self._handle_wrapped_process_shutdown()  

        if self.runs_in_main_thread:
            internal_start_function()
        else:
            self._thread = threading.Thread(target=internal_start_function)
            self._thread.start()



                
            







         