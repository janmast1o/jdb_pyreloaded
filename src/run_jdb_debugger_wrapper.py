import argparse

from src.process.debug.jdb_debugger_wrapper import JDBDebuggerWrapper, WrappingSessionOptions


def create_argument_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--complete_while_typing", type=bool, default=False)
    arg_parser.add_argument("--complete_in_thread", type=bool, default=False)
    arg_parser.add_argument("--jvm_address", type=str)
    return arg_parser


if __name__ == "__main__":
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()

    jvm_ip_address, jvm_port = args.jvm_address.split(":")
    jvm_ip_address = jvm_ip_address.strip()
    jvm_port = int(jvm_port)

    wrapping_session_options = WrappingSessionOptions(
        line_begin_marker="jdb_pyreloaded> ",
        complete_while_typing=args.complete_while_typing,
        complete_in_thread=args.complete_in_thread
    )

    jdb_debugger_wrapper = JDBDebuggerWrapper(
        jvm_process_ip_address=jvm_ip_address, jvm_process_port=jvm_port,
        start_immediately=True, exit_keyword="exit",
        wrapping_session_options=wrapping_session_options
    )