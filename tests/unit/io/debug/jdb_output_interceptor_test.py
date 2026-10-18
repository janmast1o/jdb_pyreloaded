import unittest

from typing import List, Tuple, Optional

from src.io.debug.jdb_output_interceptor import *


class MockWrappedDebuggerCommandExecutorFunctionWrapper:
    def __init__(self):
        self.executed_commands_list: List[str] = []

    def mock_execute_function_handler(self, command: str) -> None:
        self.executed_commands_list.append(command)

    def assert_last_line_is(self, line: str) -> None:
        if len(self.executed_commands_list) == 0:
            raise Exception(f"The list of executed commands is empty")

        assert line == self.executed_commands_list[-1]    


class JDBOutputInterceptorTest(unittest.TestCase):
    CODE_ADDRESS = "org.company.project.auth.AuthenticationLog:546"
    BREAKPOINT_HIT_CODE_ADDRESS = CODE_ADDRESS.split(":")[0] + ".appendAuthAttempt()"
    LINES_AND_EXPECTED_MATCH_KINDS: List[Tuple[str, Optional[BreakpointRelatedMessageKind]]] = [
        (f"Deferring breakpoint {CODE_ADDRESS}.", BreakpointRelatedMessageKind.DEFERRING_BREAKPOINT),
        ("It will be loaded after the class is loaded", None),
        (f"> Set breakpoint {CODE_ADDRESS}", BreakpointRelatedMessageKind.BREAKPOINT_SET),
        (f"> Set deferred breakpoint {CODE_ADDRESS}", BreakpointRelatedMessageKind.BREAKPOINT_SET),
        (f"Removed: breakpoint {CODE_ADDRESS}", BreakpointRelatedMessageKind.BREAKPOINT_REMOVED),
        (f"Breakpoints set:", BreakpointRelatedMessageKind.BREAKPOINTS_LISTED_HEADER),
        (f'Breakpoint hit: "thread=main", {BREAKPOINT_HIT_CODE_ADDRESS}, line=546, bci=1', BreakpointRelatedMessageKind.BREAKPOINT_HIT),
        ("nonsense", None)
    ]

    @classmethod
    def setUpClass(cls):
        cls.mock_wrapped_debugger_command_executor_function_wrapper = MockWrappedDebuggerCommandExecutorFunctionWrapper()
        cls.jdb_output_interceptor = JDBOutputInterceptor(
            wrapped_debugger_command_execute_function=cls.mock_wrapped_debugger_command_executor_function_wrapper.mock_execute_function_handler,
            breakpoint_manager=BreakpointManager()
        )
        return super().setUpClass()

    def test_try_get_breakpoint_related_message_kind_match(self):
        lines_and_expected_matched_kinds = JDBOutputInterceptorTest.LINES_AND_EXPECTED_MATCH_KINDS
        for line, expected_matched_kind in lines_and_expected_matched_kinds:
            matched_kind = self.jdb_output_interceptor._try_get_breakpoint_related_message_kind_match(line)
            self.assertEqual(expected_matched_kind, matched_kind, f"Failed to match the proper kind for {(line, expected_matched_kind)}")

    def test_find_code_address_in_line(self):
        lines_and_expected_matched_kinds = JDBOutputInterceptorTest.LINES_AND_EXPECTED_MATCH_KINDS

        for line, expected_matched_kind in lines_and_expected_matched_kinds:
            if expected_matched_kind is None:
                continue
            code_address = None
            if expected_matched_kind == BreakpointRelatedMessageKind.BREAKPOINT_HIT:
                code_address = f"{JDBOutputInterceptorTest.BREAKPOINT_HIT_CODE_ADDRESS}|{JDBOutputInterceptorTest.CODE_ADDRESS}"
            else:
                code_address = JDBOutputInterceptorTest.CODE_ADDRESS
            found_code_address = self.jdb_output_interceptor._find_code_address_in_line(line, expected_matched_kind)
            self.assertEqual(
                code_address if expected_matched_kind != BreakpointRelatedMessageKind.BREAKPOINTS_LISTED_HEADER else None, 
                found_code_address, 
                f"Could not find code address for {(line, expected_matched_kind)}"
            )

    def test_handle_breakpoint_related_message(self):
        regular_code_address = JDBOutputInterceptorTest.CODE_ADDRESS
        conditional_code_address = "org.company.project.IPBlacklistedException:681"
        condition = "ipAddress.everBlacklisted()"
        # Assert that the messages which are meant to be throttled
        # are indeed throttled
        self.assertIsNone(self.jdb_output_interceptor._handle_breakpoint_related_message(
            BreakpointRelatedMessageKind.BREAKPOINTS_LISTED_HEADER, "Breakpoints set:"
        ))
        self.assertIsNone(self.jdb_output_interceptor._handle_breakpoint_related_message(
            BreakpointRelatedMessageKind.ENTRY_IN_BREAKPOINT_LIST, f"   breakpoint {regular_code_address}"
        ))

        # Adding breakpoints
        self.jdb_output_interceptor._breakpoint_manager.add_regular_breakpoint(regular_code_address)
        self.jdb_output_interceptor._breakpoint_manager.add_conditional_breakpoint(conditional_code_address, condition)

        # Simulated hitting regular breakpoint
        regular_breakpoint_hit_message = f'Breakpoint hit: "thread=main", {regular_code_address}, line=546, bci=1'
        new_line = self.jdb_output_interceptor._handle_breakpoint_related_message(
            BreakpointRelatedMessageKind.BREAKPOINT_HIT, regular_breakpoint_hit_message
        )
        self.assertEqual("Regular " + regular_breakpoint_hit_message, new_line)

        # Simulated hitting conditional breakpoint
        conditional_breakpoint_hit_message = f'Breakpoint hit: "thread=main", {conditional_code_address}, line=681, bci=1'
        new_line = self.jdb_output_interceptor._handle_breakpoint_related_message(
            BreakpointRelatedMessageKind.BREAKPOINT_HIT, conditional_breakpoint_hit_message
        )
        self.assertEqual("Conditional " + conditional_breakpoint_hit_message + ", will assess whether to stop.", new_line)
        self.mock_wrapped_debugger_command_executor_function_wrapper.assert_last_line_is(f"print {condition}")
        self.assertEqual(condition, self.jdb_output_interceptor._awaiting_breakpoint_condition_check_line_begin)


if __name__ == "__main__":
    unittest.main()        