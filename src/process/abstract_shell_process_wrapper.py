import pexpect
import sys
import threading

from abc import abstractmethod
from typing import Union, Optional, Dict, Any
from typing_extensions import override
from prompt_toolkit import PromptSession
from prompt_toolkit.input import Input

from src.io.abstract_wrapping_process_input_interceptor import AbstractWrappingProcessInputInterceptor
from src.io.abstract_wrapped_process_output_interceptor import AbstractWrappedProcessOutputInterceptor
from src.process.internal_use_interceptors_and_completer_creator import InternalUseInterceptorsAndCompleterCreator
from src.utils.util_objects import BaseString
from src.utils.custom_exceptions import ShellProcessWrapperInterruptException, CommandMalformedException

class WrappingSessionOptions:
    def __init__(self, line_begin_marker: str,
                 complete_while_typing: bool = False,
                 complete_in_thread: bool = False):
        self.line_begin_marker: str = line_begin_marker
        self.complete_while_typing: bool = complete_while_typing
        self.complete_in_thread: bool = complete_in_thread
        
# If wrapping process is meant to use `sys.stdin` as input
# set `input_for_wrapping_session` to `None`
class AbstractShellProcessWrapper(InternalUseInterceptorsAndCompleterCreator):
    def __init__(self, wrapping_session_options: WrappingSessionOptions, 
                 ignore_wrapped_process_input_line: bool = True,
                 run_in_main_thread: bool = True, 
                 start_immediately: bool = True, 
                 exit_keyword: str = "exit", 
                 stdout = sys.stdout, stderr = sys.stderr, 
                 input_for_wrapping_session: Optional[Input] = None):
        self._wrapped_process: pexpect.spawn = None
        self._wrapping_session: PromptSession = None
        self._wrapping_session_options: WrappingSessionOptions = wrapping_session_options
        self._ignore_wrapped_process_input_line: bool = ignore_wrapped_process_input_line
        self._run_in_main_thread: bool = run_in_main_thread
        self._exit_keyword = exit_keyword
        self._stdout = stdout
        self._stderr = stderr
        self._input_for_wrapping_session = input_for_wrapping_session
        self._thread: Optional[threading.Thread] = None
        self._keep_running = False
        self._optional_input_interceptor: AbstractWrappingProcessInputInterceptor = self._create_input_interceptor()

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

    @abstractmethod
    def _get_exit_keyword_for_wrapped_process(self) -> str:
        pass

    @abstractmethod
    def _create_input_line_match_pattern(self) -> BaseString:
        pass

    def _preprocess_command(self, command: str) -> Optional[str]:
        if self._optional_input_interceptor is None:
            return command
        else:
            return self._optional_input_interceptor.intercept_on_input_send(command)

    @abstractmethod
    def _execute_command_in_wrapped_process(self, command: str) -> None:
        pass

    @abstractmethod
    def _get_wrapped_process_start_kwargs(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _start_wrapped_process(self) -> None:
        pass

    # Returns `None` by default. It could make sense reimplementing this in inheriting classes.
    @override
    def _create_input_interceptor(self) -> Optional[AbstractWrappingProcessInputInterceptor]:
        return None

    # Returns `None` by default. It could make sense reimplementing this in inheriting classes..
    @override
    def _create_output_interceptor(self) -> Optional[AbstractWrappedProcessOutputInterceptor]:
        return None

    def _handle_wrapped_process_shutdown(self) -> None:
        self._wrapped_process.close()
        assert self._wrapped_process.closed
        print(f"Wrapped process terminated with exit code: {self._wrapped_process.exitstatus}")

        self._keep_running = False
        if self._thread is not None:
            self._thread.join()   

    def _notify_wrapped_process_sink_of_last_command(self, command: str) -> None:
        self._wrapped_process.logfile_read.line_to_ignore_next_occurrence_of = command     

    def _start_wrapping_session(self) -> None:
        self._wrapping_session = PromptSession(
            completer=self._create_completer(), 
            complete_while_typing=self._wrapping_session_options.complete_while_typing, 
            complete_in_thread=self._wrapping_session_options.complete_in_thread, 
            input=self._input_for_wrapping_session,
            reserve_space_for_menu=0 # TODO: Add this as an option
        )

        print(self._get_introduction_message())

    def _read_command_from_wrapping_session_prompt(self) -> str:
        command: str = self._wrapping_session.prompt(self._wrapping_session_options.line_begin_marker)
        return command.strip()

    def _handle_prompt_method_call_interrupt(self) -> None:
        pass

    # TODO: Implement stdout, stdin, stderr redirection
    # Returns:
    #   - None: if the process wrapper is meant to start in the main thread
    #   - threading.Thread: if the process is meant to start in a separate thread
    def _start(self) -> Union[None, threading.Thread]:

        def internal_start_function():
            self._keep_running = True
            # This order is crucial for the multithreaded process inheriting class
            # to work. I know that base class accommodating the design of 
            # an inheriting class isn't all that good, but oh well.
            self._start_wrapping_session()
            self._start_wrapped_process()

            # TODO: Add silencing the error from the wrapping session
            while self._keep_running:
                try:
                    command: str = self._read_command_from_wrapping_session_prompt()
                    if command == self._exit_keyword:
                        command = self._get_exit_keyword_for_wrapped_process()
                        self._keep_running = False

                    normalized_command = self._preprocess_command(command)
                    if normalized_command is not None:
                        self._execute_command_in_wrapped_process(normalized_command)
                # To accommodate asyncio SIGINT handler override
                except KeyboardInterrupt:
                    self._handle_prompt_method_call_interrupt()
                    continue 
                # To be safe between asyncio.Runner.run() executions       
                except ShellProcessWrapperInterruptException:
                    self._handle_prompt_method_call_interrupt()
                    continue
                except CommandMalformedException as e:
                    print(f"Command malformed exception: {str(e)}")
                    continue
                except EOFError:
                    break

            self._handle_wrapped_process_shutdown()  

        if self.runs_in_main_thread:
            internal_start_function()
        else:
            self._thread = threading.Thread(target=internal_start_function)
            self._thread.start()
            return self._thread

    def _stop(self) -> None:
        self._handle_wrapped_process_shutdown()     



                
            







         