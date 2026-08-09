import argparse

from src.process.shell_process_wrapper import WrappingSessionOptions
from tests.shared_across_test_types.process.python_console_wrapper import PythonConsoleWrapper

def create_argument_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--complete_while_typing", type=bool, default=False)
    arg_parser.add_argument("--complete_in_thread", type=bool, default=False)
    return arg_parser

if __name__ == "__main__":
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()

    wrapping_session_options = WrappingSessionOptions(
        line_begin_marker="python_console> ",
        complete_while_typing=args.complete_while_typing, 
        complete_in_thread=args.complete_in_thread
    )

    python_console_wrapper = PythonConsoleWrapper(
        wrapping_session_options, start_immediately=True, exit_keyword="exit"
    )