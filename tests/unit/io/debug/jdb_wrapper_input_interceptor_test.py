import unittest

from typing import List, Tuple, Union

from src.io.debug.jdb_wrapper_input_interceptor import *


class JDBWrapperInputInterceptorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jdb_wrapper_input_interceptor: JDBWrapperInputInterceptor = JDBWrapperInputInterceptor(BreakpointManager())
        return super().setUpClass()

    def setUp(self):
        self.jdb_wrapper_input_interceptor._breakpoint_manager.remove_all_breakpoints_and_reset_counters()
        return super().setUp()

    def _assert_breakpoint_manager_has_breakpoints(self, regular_breakpoints: List[str],
                                                   conditional_breakpoints: List[Tuple[str, str]]):
        breakpoint_manager = self.jdb_wrapper_input_interceptor._breakpoint_manager
        self.assertEqual(len(regular_breakpoints), len(breakpoint_manager._regular_breakpoints_code_address_map))
        self.assertEqual(len(regular_breakpoints), len(breakpoint_manager._regular_breakpoints_id_map))
        self.assertEqual(len(conditional_breakpoints), len(breakpoint_manager._conditional_breakpoints_code_address_map))
        self.assertEqual(len(conditional_breakpoints), len(breakpoint_manager._conditional_breakpoints_id_map))

        self.assertEqual(
            set(regular_breakpoints),
            {code_address for code_address in breakpoint_manager._regular_breakpoints_code_address_map.keys()}
        )

        self.assertEqual(
            set(conditional_breakpoints),
            {
                (conditional_breakpoint.code_address, conditional_breakpoint.condition) 
                for _, conditional_breakpoint in breakpoint_manager._conditional_breakpoints_code_address_map.values()
            }
        )

    def test_proper_kind_matches(self):
        code_address = "org.company.project.auth.AuthenticationLog:57"
        conditions = [
            "this.checkNLastCommitsAndTryFind(ipAddress, 5)", 
            "this.wasIPEverBlacklisted(ipAddress)",
            "requestedLeaseTime.exceeds(25, TimeUnits.MINUTES)"
        ]

        valid_commands_and_matches: List[Tuple[str, BreakpointRelatedCommandKind]] = [
            (f"stop at {code_address}", BreakpointRelatedCommandKind.SET_REGULAR_BREAKPOINT)
        ] + [
            (f"stop at {code_address} if " + " || ".join(conditions[:i]), BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT)
            for i in range(1, len(conditions)+1)
        ] + [
            (f"stop at {code_address} if " + " && ".join(conditions[:i]), BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT)
            for i in range(1, len(conditions)+1)
        ] + [
            (f"clear {code_address}", BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT),
            (f"clear conditional {code_address}", BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT),
            ("clear", BreakpointRelatedCommandKind.LIST_BREAKPOINTS), 
            ("clear 1", BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT),
            ("clear 99", BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT),
            ("clear conditional 1", BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT),
            ("clear conditional 99", BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT),
            ("show breakpoints", BreakpointRelatedCommandKind.LIST_BREAKPOINTS),
            ("show all breakpoints", BreakpointRelatedCommandKind.LIST_BREAKPOINTS),
            ("list breakpoints", BreakpointRelatedCommandKind.LIST_BREAKPOINTS),
            ("list all breakpoints", BreakpointRelatedCommandKind.LIST_BREAKPOINTS)
        ]

        for command, expected_kind in valid_commands_and_matches:
            matched_kind = self.jdb_wrapper_input_interceptor._try_get_breakpoint_related_command_type_match(command)
            self.assertEqual(expected_kind, matched_kind, f"Failed assertion: {(command, expected_kind)}")

        invalid_commands_and_outcomes: List[Tuple[str, Union[CommandMalformedException, None]]] = [
            ("stop at", CommandMalformedException()),
            ("stop in", CommandMalformedException()),
            ("listall breakpoints", None),
            ("showall breakpoints", None),
            ("list allbreakpoints", None),
            ("show allbreakpoints", None),
            ("apple", None),
            ("watermelon", None)
        ]

        outcome: Optional[CommandMalformedException] = None
        for command, expected_outcome in invalid_commands_and_outcomes:
            try:
                outcome = self.jdb_wrapper_input_interceptor._try_get_breakpoint_related_command_type_match(command)
            except CommandMalformedException as e:
                outcome = e

            if expected_outcome is None:
                self.assertIsNone(outcome, f"Failed assertion: {(command, expected_outcome)}")
            elif isinstance(expected_outcome, CommandMalformedException):
                self.assertIsInstance(outcome, CommandMalformedException, f"Failed assertion: {(command, expected_outcome)}")
            else:
                raise AssertionError(f"For pair {(command, expected_outcome)} the outcome was {outcome}")

    def test_getting_code_address_and_condition_in_breakpoint_message(self):
        set_regular_breakpoint_code_address = "org.company.project.auth.AuthenticationLog:255"
        set_conditional_breakpoint_code_address = "org.company.project.auth.IPBlacklistedException:85"
        remove_regular_breakpoint_code_address = "org.company.project.serialization.MessageCompressor:901"
        remove_conditional_breakpoint_code_address = "org.company.project.service.Main:204"

        conditions = [
            "(blacklistExpiration(ipAddress)) != null",
            "(ipAddress.isPublic())"
        ]

        code_address, condition = self.jdb_wrapper_input_interceptor._get_code_address_and_try_get_condition_for_command(
            matched_kind=BreakpointRelatedCommandKind.SET_REGULAR_BREAKPOINT,
            c=f"stop at {set_regular_breakpoint_code_address}"
        )
        self.assertEqual(set_regular_breakpoint_code_address, code_address)
        self.assertIsNone(condition)

        code_address, condition = self.jdb_wrapper_input_interceptor._get_code_address_and_try_get_condition_for_command(
            matched_kind=BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT,
            c=f"stop at {set_conditional_breakpoint_code_address} if {conditions[0]}"
        )
        self.assertEqual(set_conditional_breakpoint_code_address, code_address)
        self.assertEqual(conditions[0], condition)

        code_address, condition = self.jdb_wrapper_input_interceptor._get_code_address_and_try_get_condition_for_command(
            matched_kind=BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT,
            c=f"stop at {set_conditional_breakpoint_code_address} if " + " || ".join(conditions)
        )
        self.assertEqual(set_conditional_breakpoint_code_address, code_address)
        self.assertEqual(condition, " || ".join(conditions))

        code_address, condition = self.jdb_wrapper_input_interceptor._get_code_address_and_try_get_condition_for_command(
            matched_kind=BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT,
            c=f"clear {remove_regular_breakpoint_code_address}"
        )
        self.assertEqual(remove_regular_breakpoint_code_address, code_address)
        self.assertIsNone(condition)

        code_address, condition = self.jdb_wrapper_input_interceptor._get_code_address_and_try_get_condition_for_command(
            matched_kind=BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT,
            c=f"clear 1"
        )
        self.assertEqual("1", code_address)
        self.assertIsNone(condition)

        code_address, condition = self.jdb_wrapper_input_interceptor._get_code_address_and_try_get_condition_for_command(
            matched_kind=BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT,
            c=f"clear conditional {remove_conditional_breakpoint_code_address}"
        )
        self.assertEqual(remove_conditional_breakpoint_code_address, code_address)
        self.assertIsNone(condition)

        code_address, condition = self.jdb_wrapper_input_interceptor._get_code_address_and_try_get_condition_for_command(
            matched_kind=BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT,
            c=f"clear conditional 1"
        )
        self.assertEqual("1", code_address)
        self.assertIsNone(condition)

    def test_handle_breakpoint_related_command(self):
        regular_breakpoint_code_address = "org.company.project.auth.AuthenticationLog:255"
        conditional_breakpoint_code_address = "org.company.project.auth.IPBlacklistedException:85"
        shared_breakpoint_code_address = "org.company.project.serialization.MessageCompressor:901"

        conditions = [
            "(blacklistExpiration(ipAddress)) != null",
            "(ipAddress.isPublic())"
        ]

        new_command = self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.SET_REGULAR_BREAKPOINT,
            command=f"stop at {regular_breakpoint_code_address}"
        )
        self.assertEqual(f"stop at {regular_breakpoint_code_address}", new_command)
        self._assert_breakpoint_manager_has_breakpoints([regular_breakpoint_code_address], [])

        new_command = self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT,
            command=f"stop at {conditional_breakpoint_code_address} if {conditions[0]}"
        )
        self.assertEqual(f"stop at {conditional_breakpoint_code_address}", new_command)
        self._assert_breakpoint_manager_has_breakpoints(
            [regular_breakpoint_code_address], [(conditional_breakpoint_code_address, conditions[0])]
        )

        new_command = self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT,
            command=f"stop at {conditional_breakpoint_code_address} if {conditions[1]}"
        )
        self.assertIsNone(new_command)
        self._assert_breakpoint_manager_has_breakpoints(
            [regular_breakpoint_code_address], 
            [(conditional_breakpoint_code_address, "(" + conditions[0] + ") || (" + conditions[1] + ")")]
        )

        new_command = self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT,
            command=f"clear {regular_breakpoint_code_address}"
        )
        self.assertEqual(f"clear {regular_breakpoint_code_address}", new_command)
        self._assert_breakpoint_manager_has_breakpoints(
            [], [(conditional_breakpoint_code_address, "(" + conditions[0] + ") || (" + conditions[1] + ")")]
        )

        new_command = self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT,
            command=f"clear conditional {conditional_breakpoint_code_address}"
        )
        self.assertEqual(f"clear {conditional_breakpoint_code_address}", new_command)
        self._assert_breakpoint_manager_has_breakpoints([], [])

        # Test for shared command
        new_command = self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.SET_REGULAR_BREAKPOINT,
            command=f"stop at {shared_breakpoint_code_address}"
        )
        self.assertEqual(f"stop at {shared_breakpoint_code_address}", new_command)
        self._assert_breakpoint_manager_has_breakpoints([shared_breakpoint_code_address], [])

        new_command = self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT,
            command=f"stop at {shared_breakpoint_code_address} if {conditions[0]}"
        )
        self.assertIsNone(new_command)
        self._assert_breakpoint_manager_has_breakpoints(
            [shared_breakpoint_code_address], [(shared_breakpoint_code_address, conditions[0])]
        )

        new_command = self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT,
            command=f"clear {shared_breakpoint_code_address}"
        )
        self.assertIsNone(new_command)
        self._assert_breakpoint_manager_has_breakpoints([], [(shared_breakpoint_code_address, conditions[0])])

        new_command = self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT,
            command=f"clear conditional {shared_breakpoint_code_address}"
        )
        self.assertEqual(f"clear {shared_breakpoint_code_address}", new_command)
        self._assert_breakpoint_manager_has_breakpoints([], [])

    def test_handle_breakpoint_removals_using_breakpoint_ids(self):
        regular_breakpoint_code_address = "org.company.project.auth.AuthenticationLog:255"
        conditional_breakpoint_code_address = "org.company.project.auth.IPBlacklistedException:85"
        condition = "ipAddress.isPrivate()"
        self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.SET_REGULAR_BREAKPOINT,
            command=f"stop at {regular_breakpoint_code_address}"
        )
        self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.SET_CONDITIONAL_BREAKPOINT,
            command=f"stop at {conditional_breakpoint_code_address} if {condition}"
        )

        new_command = self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.REMOVE_REGULAR_BREAKPOINT,
            command="clear 1"
        )
        self.assertEqual(f"clear {regular_breakpoint_code_address}", new_command)
        self._assert_breakpoint_manager_has_breakpoints([], [(conditional_breakpoint_code_address, condition)])

        new_command = self.jdb_wrapper_input_interceptor._handle_breakpoint_related_command(
            matched_kind=BreakpointRelatedCommandKind.REMOVE_CONDITIONAL_BREAKPOINT,
            command=f"clear conditional 1"
        )
        self.assertEqual(f"clear {conditional_breakpoint_code_address}", new_command)
        self._assert_breakpoint_manager_has_breakpoints([], [])


if __name__ == "__main__":
    unittest.main()                           