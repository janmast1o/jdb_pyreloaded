import argparse

from src.process.abstract_shell_process_wrapper import WrappingSessionOptions
from tests.shared_across_test_types.process.concurrent_printers_with_live_message_changing_wrapper import ConcurrentPrintersWithLiveMessageChangingWrapper


def create_argument_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--complete_while_typing", type=bool, default=False)
    arg_parser.add_argument("--complete_in_thread", type=bool, default=False)
    arg_parser.add_argument("--number_of_printers", type=int, default=4)
    return arg_parser


if __name__ == "__main__":
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()

    wrapping_session_options = WrappingSessionOptions(
        line_begin_marker="concurrent_printers> ",
        complete_while_typing=args.complete_while_typing, 
        complete_in_thread=args.complete_in_thread
    )   

    concurrent_printers_wrapper = ConcurrentPrintersWithLiveMessageChangingWrapper(
        wrapping_session_options=wrapping_session_options, 
        start_immediately=True, exit_keyword="exit",
        number_of_printers=args.number_of_printers
    )