import sys

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.input import Input
from subprocess import Popen, PIPE
from typing import Optional, Dict, Any, List
from typing_extensions import override

from src.process.shell_process_wrapper import ShellProcessWrapper, WrappingSessionOptions
from src.process.single_threaded_shell_process_wrapper import SingleThreadedShellProcessWrapper

class SelectedPythonKeywordsCompleter(Completer):
    PYTHON_KEYWORD_SELECTION = [
        "while", "for", "in", "if", "else", "elif", 
        "with", "as", "assert", "from", "import", 
        "True", "False", "None"
    ]

    def get_completions(self, document, unimportant_complete_event):
        word = document.get_word_before_cursor()
        if len(document.text_after_cursor) == 0 or document.text_after_cursor[0].isspace():
            for keyword in self.PYTHON_KEYWORD_SELECTION:
                if keyword.startswith(word):
                    yield Completion(word, start_position=0)


class PythonConsoleWrapper(SingleThreadedShellProcessWrapper):
    def __init__(self, wrapping_session_options: WrappingSessionOptions, 
                 run_in_main_thread: bool = True, 
                 start_immediately: bool = True, 
                 exit_keyword: str = "exit", 
                 stdout = sys.stdout, stderr = sys.stderr,
                 input_for_wrapping_session: Optional[Input] = None):
        super().__init__(
            wrapping_session_options, run_in_main_thread,
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
    def _normalize_command_and_try_change_command_execution_logic(self, command) -> str:
        return command

    # @override
    # def _execute_command_in_wrapped_process(self, command) -> None:
    #     # print("A")
    #     # self._wrapped_process.stdin.write(command)
    #     # print("B")
    #     # self._wrapped_process.stdin.flush()
    #     # print("C")

    #     # bufsize = 1024
    #     # while True:
    #     #     # Non-None returncode means the process has concluded
    #     #     if self._wrapped_process.returncode is not None:
    #     #         break
    #     #     # line: str = self._wrapped_process.stdout.readline()
    #     #     output_block = self._wrapped_process.stdout.read(bufsize)
    #     #     # print(f"Line: {output_block}")
    #     #     # if line.strip() == ">>>":
    #     #     if len(output_block) < bufsize:
    #     #         break
    #     #     print(output_block, end="")

    #     # self._wrapped_process.sendline(command)
    #     outcome_index = self._wrapped_process.expect([">>> ", pexpect.TIMEOUT, pexpect.EOF])
    #     # while True:
    #         # bufsize = 1024
    #         # read_output = self._wrapped_process.read()
    #         # print(read_output, end='')
    #         # if len(read_output) < bufsize:
    #             # break

    #     print(self._wrapped_process.before)
    #     print()    

    # @override
    # def _start_wrapped_process(self) -> None:
    #     self._wrapped_process = pexpect.spawn("python")
    #     # self._wrapped_process = Popen(
    #     #     ["python"],
    #     #     stdin=PIPE, stdout=PIPE, stderr=PIPE, 
    #     #     text=True, bufsize=True
    #     # )   

    @override
    def _get_wrapped_process_start_kwargs(self) -> Dict[str, Any]:
        return {"command" : "python", "encoding" : "utf-8"}

    @override
    def _get_wrapped_process_expect_options(self) -> List[str]:
        return [">>>"]

    @override
    def _handle_wrapped_process_shutdown(self) -> None:
        self._wrapped_process.close()
        print(f"Wrapped process has terminated with returncode: {self._wrapped_process.exitstatus}")  
        # wrapped_process_returncode = self._wrapped_process.returncode
        # assert wrapped_process_returncode is not None
        # print(f"Wrapped process has terminated with returncode: {wrapped_process_returncode}")  
