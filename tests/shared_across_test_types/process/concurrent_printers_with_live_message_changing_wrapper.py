import os
import sys

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.input import Input
from typing import Optional, List, Dict, Any
from typing_extensions import override

from src.process.abstract_shell_process_wrapper import WrappingSessionOptions
from src.process.multi_threaded_shell_process_wrapper import MultiThreadedShellProcessWrapper
from src.utils.util_objects import BaseString, SimpleString

class ConcurrentPrintersWrapperCompleter(Completer):
    @override
    def get_completions(self, document, unimportant_complete_event):
        word = document.get_word_before_cursor()
        if len(document.text_after_cursor) == 0 or document.text_after_cursor[0].isspace():
            if "change_message".startswith(word):
                yield Completion("change_message", start_position=-len(word))
            elif "exit".startswith(word):
                yield Completion("exit", start_position=-len(word))


class ConcurrentPrintersWithLiveMessageChangingWrapper(MultiThreadedShellProcessWrapper):                
    def __init__(self, wrapping_session_options: WrappingSessionOptions,
                 ignore_wrapped_process_input_line: bool = True,
                 run_in_main_thread: bool = True,
                 start_immediately: bool = True, 
                 exit_keyword: str = "exit",
                 stdout = sys.stdout, stderr = sys.stderr,
                 input_for_wrapping_session: Optional[Input] = None,
                 number_of_printers: int = 4):
        self._number_of_printers: int = number_of_printers
        super().__init__(
            wrapping_session_options, 
            ignore_wrapped_process_input_line,
            run_in_main_thread,
            start_immediately, exit_keyword,
            stdout, stderr, input_for_wrapping_session
        )

    @override
    def _create_completer(self) -> Completer:
        return ConcurrentPrintersWrapperCompleter()

    @override
    def _get_introduction_message(self) -> str:
        return f"Welcome to concurrent printers test run wrapper. Type '{self._exit_keyword}' to quit"

    @override
    def _get_exit_keyword_for_wrapped_process(self) -> str:
        return "exit"

    @override
    def _preprocess_command(self, command: str) -> Optional[str]:
        return super()._preprocess_command(command.replace("'", '"'))

    @override
    def _get_wrapped_process_start_kwargs(self) -> Dict[str, Any]:
        return {
            "command": os.environ["SHELL"],
            "args": [
                '-c', 
                f'cd {os.getcwd()} && ' +
                'python -m tests.shared_across_test_types.process.run_concurrent_printers_with_live_message_changing ' +
                f'--number_of_printers={self._number_of_printers}'
            ],
            "encoding" : "utf-8"
        }

    @override
    def _create_input_line_match_pattern(self) -> BaseString:
        return SimpleString("")
