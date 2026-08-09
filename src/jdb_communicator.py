import subprocess
import re
import ipaddress

from typing import Optional

from .logger import Logger
from .process_information_checker import ProcessInformationChecker
from .source_code_information_registry import SourceCodeChecker

class JDBCommunicator:
    logger = Logger.get_logger("JDBCommunicator")

    def __init__(self, ip_address: str, port: int, start_immdediately: bool = True, 
                 source_code_address: str = None):
        self.ip_address: str = ip_address
        self.port: int = port
        try:
            ipaddress.ip_address(self.ip_address)
            assert isinstance(port, int)
        except ValueError | AssertionError:
            raise Exception("IP Address and/or port invalid")

        self.jdb_process: Optional[subprocess.Popen] = None
        self.process_information_checker: Optional[ProcessInformationChecker] = None 
        self.source_code_checker: Optional[SourceCodeChecker] = None

        if start_immdediately:
            self.start_jdb()


    def __check_if_jdb_is_running(self) -> bool:
        if self.jdb_process is None:
            self.logger.warning("Cannot exit jdb, as it is not running, the request will be ignored")   
            return False 

        return True   
    
    # def __check_if_jdb_termination_line(self, line: str) -> bool:
    #     line = line.strip()
    #     if line in ["The application has exited", ">"]:
    #         return True 
    #     elif re.fullmatch(r"^[0-9a-zA-Z\-_\s]+\[\d+\]$"):
    #         thread_name = 



    def start_jdb(self) -> None:
        self.jdb_process = subprocess.Popen(
            [
                "jdb", "-attach", 
                f"{self.ip_address}:{self.port}"
            ],
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=True,
        )

        # self.process_information_checker = 

    def exit_jdb(self) -> None:
        if not self.__check_if_jdb_is_running():
            return 
        
        self.jdb_process.stdin.write("exit\n")
        self.jdb_process.stdin.flush()

    def execute_command(self, command: str) -> str:   
        if not self.__check_if_jdb_is_running():
            return 
        
        self.jdb_process.stdin.write(command)
        self.jdb_process.stdin.flush()

        output_lines = []
        while True:
            line = self.jdb_process.stdout.readline()
            if self.__check_if_jdb_termination_line(line):
                break 
            output_lines.append(line)


# from prompt_toolkit import PromptSession
# from prompt_toolkit.completion import Completer, Completion

# get_completions_triggers = []

# class PyJDBCompleter(Completer):
#     KEYWORDS = ["CREATE", "CREATED", "CREATURE", "ALTER", "ALTERATION", "DELETE", "DELETION", "DOG", "DOGHOUSE"]

#     def get_completions(self, document, complete_event):
#         get_completions_triggers.append((document.text_before_cursor, document.text_after_cursor))

#         word = document.get_word_before_cursor().upper()
#         # text = document.text_before_cursor.upper()

#         for keyword in self.KEYWORDS:
#             if keyword.startswith(word):
#                 yield Completion(keyword, start_position=-len(word))


# def execute(command):
#     print(f"Executing: {command}")


# def main():
#     session = PromptSession(
#         completer=PyJDBCompleter(), 
#         complete_while_typing=False, 
#         complete_in_thread=False
#     )

#     print("PyJDB Reloaded Shell. Type 'exit' to quit")
#     while True:
#         try:
#             command : str = session.prompt("pyjdb> ")

#             if command.strip().lower() == "exit":
#                 break

#             execute(command)
#         except KeyboardInterrupt:
#             continue

#         except EOFError:
#             break


# if __name__ == "__main__":
#     main()
#     print(get_completions_triggers)   

            
