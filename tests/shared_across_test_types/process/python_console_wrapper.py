import sys

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.input import Input
from typing import Optional, Dict, Any, List
from typing_extensions import override

from src.process.abstract_shell_process_wrapper import WrappingSessionOptions
from src.process.single_threaded_shell_process_wrapper import SingleThreadedShellProcessWrapper
from src.utils.util_objects import BaseString, SimpleString

class SelectedPythonKeywordsCompleter(Completer):
    PYTHON_KEYWORD_SELECTION = [
        "while", "for", "in", "if", "else", "elif", 
        "with", "as", "assert", "from", "import", 
        "True", "False", "None"
    ]

    @override
    def get_completions(self, document, unimportant_complete_event):
        word = document.get_word_before_cursor()
        if len(document.text_after_cursor) == 0 or document.text_after_cursor[0].isspace():
            for keyword in self.PYTHON_KEYWORD_SELECTION:
                if keyword.startswith(word):
                    yield Completion(keyword, start_position=-len(word))


class PythonConsoleWrapper(SingleThreadedShellProcessWrapper):
    def __init__(self, wrapping_session_options: WrappingSessionOptions, 
                 ignore_wrapped_process_input_line: bool = True,
                 run_in_main_thread: bool = True, 
                 start_immediately: bool = True, 
                 exit_keyword: str = "exit", 
                 stdout = sys.stdout, stderr = sys.stderr,
                 input_for_wrapping_session: Optional[Input] = None):
        super().__init__(
            wrapping_session_options, 
            ignore_wrapped_process_input_line,
            run_in_main_thread,
            start_immediately, exit_keyword, 
            stdout, stderr, input_for_wrapping_session
        )

    @override    
    def _get_introduction_message(self) -> str:
        return f"Welcome to python console wrapper. Type '{self._exit_keyword}' to quit"

    @override
    def _create_completer(self) -> Completer:
        return SelectedPythonKeywordsCompleter()

    @override
    def _get_exit_keyword_for_wrapped_process(self) -> str:
        return "exit()"

    @override
    def _preprocess_command(self, command) -> Optional[str]:
        return command

    @override
    def _get_wrapped_process_start_kwargs(self) -> Dict[str, Any]:
        return {"command" : "python", "encoding" : "utf-8"}

    @override
    def _get_wrapped_process_expect_options(self) -> List[str]:
        return [">>>"]

    @override
    def _create_input_line_match_pattern(self) -> BaseString:
        return SimpleString(">>>")