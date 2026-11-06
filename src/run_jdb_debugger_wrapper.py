import argparse

from src.process.debug.jdb_debugger_wrapper import JDBDebuggerWrapper, WrappingSessionOptions


def create_argument_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--complete_while_typing", type=bool, default=False, help="`complete_while_typing` setting of `prompt_toolkit.PromptSession`.")
    arg_parser.add_argument("--complete_in_thread", type=bool, default=False, help="`complete_in_thread` setting of `prompt_toolkit.PromptSession`.")
    arg_parser.add_argument("--jvm_address", type=str, help="The address in format <ip_address>:<port> of the JVM to connect to.")
    arg_parser.add_argument("--local_project_path", type=str, required=False, help="""Absolute path to the project being debugged (needed to create the autocompletion tree for class names). 
If skipped the autocompletion will not be built. This feature is not supported when debugging a remote java process. 
""")
    arg_parser.add_argument("--pyjdb_target_list", type=str, default="", help="Can be passed as an argument instead of being read from the `target.pyjdb` in the project directory.")
    return arg_parser


if __name__ == "__main__":
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()

    jvm_ip_address, jvm_port = args.jvm_address.split(":")
    jvm_ip_address = jvm_ip_address.strip()
    jvm_port = int(jvm_port)
    local_project_path = None
    try:
        local_project_path = args.local_project_path
    except Exception:
        pass
    pyjdb_target_list = args.pyjdb_target_list.split(sep=",") if len(args.pyjdb_target_list) > 0 else None

    wrapping_session_options = WrappingSessionOptions(
        line_begin_marker="jdb_pyreloaded> ",
        complete_while_typing=args.complete_while_typing,
        complete_in_thread=args.complete_in_thread
    )

    jdb_debugger_wrapper = JDBDebuggerWrapper(
        jvm_process_ip_address=jvm_ip_address, jvm_process_port=jvm_port,
        optional_local_project_path=local_project_path,
        optional_pyjdb_target_list=pyjdb_target_list,
        start_immediately=True, exit_keyword="exit",
        wrapping_session_options=wrapping_session_options
    )