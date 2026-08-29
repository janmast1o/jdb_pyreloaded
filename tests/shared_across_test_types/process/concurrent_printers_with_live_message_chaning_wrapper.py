import sys

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.input import Input
from typing_extensions import override

from src.process.single_threaded_shell_process_wrapper import SingleThreadedShellProcessWrapper

class ConcurrentPrintersWrapperCompleter(Completer):
    @override
    def get_completions(self, document, unimportant_complete_event):
        word = document.get_word_before_cursor()
        if len(document.text_after_cursor) == 0 or document.text_after_cursor[0].isspace():
            if "change_message".startswith(word):
                yield Completion("change_message", start_position=-len(word))
            elif "exit".startswith(word):
                yield Completion("exit", start_position=-len(word))


class ConcurrentPrintersWithLiveMessageChangingWrapper(SingleThreadedShellProcessWrapper):                
