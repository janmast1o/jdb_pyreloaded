import argparse
import re

from tests.shared_across_test_types.process.concurrent_printers_runner import ConcurrentPrintersRunner


def create_argument_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--number_of_printers", type=int)
    return arg_parser


def print_introduction_message():
    print("""
Welcome to concurrent printers with live message changing test.
The printers are started immediately.
Into the standard input type:
    - exit: to terminate the process
    - change_message(<printer number>, <message>): changes the message printed by a printer with id = <printer number>

Printer messages cannot be empty and also can only contain letters, numbers and sentence termination characters.
    """)


if __name__=="__main__":
    print_introduction_message()
    exit_command = "exit"
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()
    printers_runner = ConcurrentPrintersRunner(
        number_of_printers=args.number_of_printers,
        printing_frequency_range=(5, 9),
        start_immediately=True
    )

    while True:
        received_command = input().strip()
        if received_command == exit_command:
            printers_runner.shutdown()
            break
        elif re.match(r'change_message\(\d+, "[a-zA-Z0-9.!?]+"\)', received_command):
            call_arguments: str = re.findall('\(\d+, "[a-zA-Z0-9.!?]+"\)', received_command)[0]
            call_arguments = call_arguments.lstrip("(").rstrip(")")
            printer_index, message = call_arguments.split(", ")
            printer_index = int(printer_index)
            printers_runner.printer_messages[printer_index] = message
        