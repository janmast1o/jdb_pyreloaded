from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion

get_completions_triggers = []

class PyJDBCompleter(Completer):
    KEYWORDS = ["CREATE", "CREATED", "CREATURE", "ALTER", "ALTERATION", "DELETE", "DELETION", "DOG", "DOGHOUSE"]

    def get_completions(self, document, complete_event):
        get_completions_triggers.append((document.text_before_cursor, document.text_after_cursor))

        word = document.get_word_before_cursor().upper()
        # text = document.text_before_cursor.upper()

        for keyword in self.KEYWORDS:
            if keyword.startswith(word):
                yield Completion(keyword, start_position=-len(word))


def execute(command):
    print(f"Executing: {command}")


def main():
    session = PromptSession(
        completer=PyJDBCompleter(), 
        complete_while_typing=False, 
        complete_in_thread=False
    )

    print("PyJDB Reloaded Shell. Type 'exit' to quit")
    while True:
        try:
            command : str = session.prompt("pyjdb> ")

            if command.strip().lower() == "exit":
                break

            execute(command)
        except KeyboardInterrupt:
            continue

        except EOFError:
            break


if __name__ == "__main__":
    main()
    print(get_completions_triggers)   
