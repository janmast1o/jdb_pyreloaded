import os
import sys

from enum import Enum
from typing import Optional


class OSType(Enum):
    WIN32 = 1
    UNIX = 2


class TerminalInputConsumer:
    ORIGINAL_TERMINAL_SETTINGS = None

    def __init__(self):
        # Not annotating modules
        self.msvcrt = None
        self.select = None
        self.termios = None
        self.tty = None

        self.fd: Optional[int] = None
        self.old_settings = None 

        if sys.platform == "win32":
            import msvcrt
            self.msvcrt = msvcrt
        else:
            import select
            import termios
            import tty

            self.select = select
            self.termios = termios
            self.tty = tty

            self.fd = sys.stdin.fileno()
            self.old_settings = self.termios.tcgetattr(self.fd)

            # Also saves the original terminal settings to a static class field
            if TerminalInputConsumer.ORIGINAL_TERMINAL_SETTINGS is None:
                TerminalInputConsumer.ORIGINAL_TERMINAL_SETTINGS = self.old_settings

    @property
    def os_type(self) -> OSType:
        return (OSType.WIN32 if (self.msvcrt is not None) else OSType.UNIX)

    def put_terminal_in_cbreak_mode_if_unix(self) -> None:
        if self.os_type == OSType.UNIX:
            print("Putting terminal in cbreak mode")
            self.tty.setcbreak(self.fd)

    def revert_to_original_settings_if_unix(self) -> None:
        if self.os_type == OSType.UNIX:
            self.termios.tcsetattr(self.fd, self.termios.TCSADRAIN, self.old_settings)

    def get_char_from_terminal_buffer(self) -> Optional[str]:
        if self.os_type == OSType.WIN32:
            if self.msvcrt.kbhit():
                return self.msvcrt.getwch()
            return None

        ready, _, _ = self.select.select([self.fd], [], [], 0.1)
        if ready:
            c = os.read(self.fd, 1)
            if c == b"":
                return None
            else:
                return str(c)

        return None

    def empty_terminal_buffer_and_return_result(self) -> Optional[str]:
        result = ""
        if self.os_type == OSType.WIN32:
            while True:
                if self.msvcrt.kbhit():
                    result = result + self.msvcrt.getwch()
                else:
                    return result if len(result) > 0 else None

        while True:    
            ready, _, _ = self.select.select([self.fd], [], [], 0.1)
            if ready:
                c = os.read(self.fd, 1)
                if c == b"":
                    return result
                else:
                    result = result + str(c)
            else:
                return result if len(result) > 0 else None       

    def empty_terminal_buffer_and_discard(self) -> None:
        if self.os_type == OSType.WIN32:
            while True:
                if self.msvcrt.kbhit():
                    self.msvcrt.getwch()
                else:
                    break

        while True:
            ready, _, _ = self.select.select([self.fd], [], [], 0.1)
            if ready:
                c = os.read(self.fd, 1)
                if c == b"":
                    break
            else:
                break     

    # This exists as a static method to make sure it can be easily called from 
    # any place in the code. It is hard to predict what might be needed to be
    # wrapped in try/except/finally clause so object lifetime should not
    # hinder our crucial control over the terminal
    @staticmethod
    def put_terminal_back_in_original_state() -> None:
        print("Will attempt to put terminal back to original state")
        if TerminalInputConsumer.ORIGINAL_TERMINAL_SETTINGS is None:
            return

        if sys.platform != "win32":
            import termios
            print("Putting terminal back to original state")
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, TerminalInputConsumer.ORIGINAL_TERMINAL_SETTINGS)                   

                