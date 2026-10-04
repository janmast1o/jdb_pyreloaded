import unittest

from src.process.debug.breakpoints import *


class BreakpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.breakpoint_manager: BreakpointManager = BreakpointManager()
        return super().setUpClass()

    def setUp(self):
        self.breakpoint_manager.remove_all_breakpoints_and_reset_counters()
        return super().setUp()

    def test_breakpoint_kinds(self):
        code_address = "org.company.project.logging.ThreadSafeLogger:57"
        regular_breakpoint = BaseBreakpoint(code_address)
        conditional_breakpoint = ConditionalBreakpoint(code_address, condition="className.length() > 5")
        self.assertEqual(BreakpointKind.REGULAR, regular_breakpoint.get_kind())
        self.assertEqual(BreakpointKind.CONDITIONAL, conditional_breakpoint.get_kind())

    def test_merge_another_condition_disjunctive_in_conditional_breakpoint(self):
        previous_condition = "className.length() > 5"
        code_address = "org.company.project.logging.ThreadSafeLogger:57"
        conditional_breakpoint = ConditionalBreakpoint(code_address, previous_condition)
        new_condition = "this.classBlacklist.contains(fullyQualifiedClassName)"
        conditional_breakpoint.merge_other_condition_disjunctive(new_condition)

        self.assertEqual(
            "(" + previous_condition + ") || (" + new_condition + ")",
            conditional_breakpoint.condition
        )

    def test_merge_another_condition_conjunctive_in_conditional_breakpoint(self):
        previous_condition = "className.length() > 5"
        code_address = "org.company.project.logging.ThreadSafeLogger:57"
        conditional_breakpoint = ConditionalBreakpoint(code_address, previous_condition)
        new_condition = "this.classBlacklist.contains(fullyQualifiedClassName)"
        conditional_breakpoint.merge_other_condition_conjunctive(new_condition)
        
        self.assertEqual(
            "(" + previous_condition + ") && (" + new_condition + ")",
            conditional_breakpoint.condition
        )

    def test_add_regular_breakpoints(self):
        code_addresses = {
            "org.company.project.logging.ThreadSafeLogger:57",
            "org.company.project.metrics.AuthOperationCounter:135",
            "org.company.project.db.DatabaseConnector:300"
        }

        for code_address in code_addresses:
            self.breakpoint_manager.add_regular_breakpoint(code_address)

        self.assertEqual(3, len(self.breakpoint_manager._regular_breakpoints_id_map))
        self.assertEqual(3, len(self.breakpoint_manager._regular_breakpoints_code_address_map))    
        self.assertEqual(0, len(self.breakpoint_manager._conditional_breakpoints_id_map))    
        self.assertEqual(0, len(self.breakpoint_manager._conditional_breakpoints_code_address_map))

        self.assertEqual(
            {b.code_address for _, b in self.breakpoint_manager._regular_breakpoints_code_address_map.values()},
            code_addresses
        )

    def test_add_non_colliding_conditional_breakpoints(self):
        code_addresses_and_conditions = {
            ("org.company.project.logging.ThreadSafeLogger:57", "className.length() > 5"),
            ("org.company.project.metrics.AuthOperationCounter:135", "!sourceIPAddress.isPrivate()"),
            ("org.company.project.db.DatabaseConnector:300", "query.isFiltering()")
        }

        for code_address, condition in code_addresses_and_conditions:
            self.breakpoint_manager.add_conditional_breakpoint(code_address, condition)

        self.assertEqual(0, len(self.breakpoint_manager._regular_breakpoints_id_map))
        self.assertEqual(0, len(self.breakpoint_manager._regular_breakpoints_code_address_map))    
        self.assertEqual(3, len(self.breakpoint_manager._conditional_breakpoints_id_map))    
        self.assertEqual(3, len(self.breakpoint_manager._conditional_breakpoints_code_address_map))

        self.assertEqual(
            {(b.code_address, b.condition) for _, b in self.breakpoint_manager._conditional_breakpoints_code_address_map.values()},
            code_addresses_and_conditions
        )

    def test_add_colliding_conditional_breakpoints(self):
        code_address = "org.company.project.db.DatabaseConnector:300"
        code_addresses_and_conditions = [
            (code_address, "query.isFiltering()"), 
            (code_address, "query.entailsDeletion()"), 
            (code_address, "this.isStable()")
        ]

        for code_address, condition in code_addresses_and_conditions:
            self.breakpoint_manager.add_conditional_breakpoint(code_address, condition)

        self.assertEqual(0, len(self.breakpoint_manager._regular_breakpoints_id_map))
        self.assertEqual(0, len(self.breakpoint_manager._regular_breakpoints_code_address_map))    
        self.assertEqual(1, len(self.breakpoint_manager._conditional_breakpoints_id_map))    
        self.assertEqual(1, len(self.breakpoint_manager._conditional_breakpoints_code_address_map))   

        conditional_breakpoint = self.breakpoint_manager._conditional_breakpoints_code_address_map[code_address][1]
        target_merged_condition = ""
        for _, c in code_addresses_and_conditions:
            if len(target_merged_condition) == 0:
                target_merged_condition += c
            else:
                target_merged_condition = f"({target_merged_condition}) || ({c})"    
        
        self.assertEqual(
            target_merged_condition,
            conditional_breakpoint.condition
        )

    def test_add_conjunction_to_conditional_breakpoint(self):
        # Test implementation for referencing by `code_address`
        code_address = "org.company.project.db.DatabaseConnector:300"
        starting_condition = "true"
        code_addresses_and_conditions = [
            (code_address, "query.isFiltering()"), 
            (code_address, "query.entailsDeletion()"), 
            (code_address, "this.isStable()")
        ]

        def internal_run_assertions():
            self.assertEqual(0, len(self.breakpoint_manager._regular_breakpoints_id_map))
            self.assertEqual(0, len(self.breakpoint_manager._regular_breakpoints_code_address_map))    
            self.assertEqual(1, len(self.breakpoint_manager._conditional_breakpoints_id_map))    
            self.assertEqual(1, len(self.breakpoint_manager._conditional_breakpoints_code_address_map))   

            conditional_breakpoint = self.breakpoint_manager._conditional_breakpoints_code_address_map[code_address][1]
            target_merged_condition = starting_condition
            for _, c in code_addresses_and_conditions:
                target_merged_condition = f"({target_merged_condition}) && ({c})"    
            
            self.assertEqual(
                target_merged_condition,
                conditional_breakpoint.condition
            )

        self.breakpoint_manager.add_conditional_breakpoint(code_address, starting_condition)
        for code_address, condition in code_addresses_and_conditions:
            self.breakpoint_manager.add_conjunction_to_conditional_breakpoint(code_address, condition)

        internal_run_assertions()

        # Test implementation for referencing by `breakpoint_id`
        self.breakpoint_manager.remove_all_breakpoints_and_reset_counters()
        self.breakpoint_manager.add_conditional_breakpoint(code_address, starting_condition)
        for code_address, condition in code_addresses_and_conditions:
            self.breakpoint_manager.add_conjunction_to_conditional_breakpoint(1, condition)

        internal_run_assertions()

    def test_regular_breakpoint_removal(self):
        def internal_run_assertions():
            self.assertEqual(0, len(self.breakpoint_manager._regular_breakpoints_id_map))
            self.assertEqual(0, len(self.breakpoint_manager._regular_breakpoints_code_address_map))    
            self.assertEqual(0, len(self.breakpoint_manager._conditional_breakpoints_id_map))    
            self.assertEqual(0, len(self.breakpoint_manager._conditional_breakpoints_code_address_map))  

        code_address = "org.company.project.concurrency.ThreadSafeQueue:101"
        # Testing `code_address` overload
        self.breakpoint_manager.add_regular_breakpoint(code_address)
        self.breakpoint_manager.remove_regular_breakpoint(code_address)
        internal_run_assertions()
        # Testing `breakpoint_id` overload
        self.breakpoint_manager.add_regular_breakpoint(code_address)
        self.breakpoint_manager.remove_regular_breakpoint(2)
        internal_run_assertions()

    def test_conditional_breakpoint_removal(self):
        def internal_run_assertions():
            self.assertEqual(0, len(self.breakpoint_manager._regular_breakpoints_id_map))
            self.assertEqual(0, len(self.breakpoint_manager._regular_breakpoints_code_address_map))    
            self.assertEqual(0, len(self.breakpoint_manager._conditional_breakpoints_id_map))    
            self.assertEqual(0, len(self.breakpoint_manager._conditional_breakpoints_code_address_map))  

        code_address = "org.company.project.concurrency.ThreadSafeQueue:101"
        condition = "operation.usesMutex()"
        # Testing `code_address` overload
        self.breakpoint_manager.add_conditional_breakpoint(code_address, condition)
        self.breakpoint_manager.remove_conditional_breakpoint(code_address)
        internal_run_assertions()
        # Testing `breakpoint_id` overload
        self.breakpoint_manager.add_conditional_breakpoint(code_address, condition)
        self.breakpoint_manager.remove_conditional_breakpoint(2)
        internal_run_assertions() 

    def test_get_condition_type_for_code_address(self):
        regular_code_address = "org.company.project.concurrency.ThreadSafeQueue:101"
        conditional_code_address = "org.company.project.auth.AuthorizationManager:107"
        colliding_code_address = "org.company.project.Start:244"

        self.breakpoint_manager.add_regular_breakpoint(regular_code_address)
        self.breakpoint_manager.add_conditional_breakpoint(conditional_code_address, "ipAddress.isWhitelisted()")
        self.breakpoint_manager.add_conditional_breakpoint(colliding_code_address, 'loggingConfig.level.equals("trace")')
        self.breakpoint_manager.add_regular_breakpoint(colliding_code_address)

        self.assertEqual(
            BreakpointKind.REGULAR, 
            self.breakpoint_manager.get_condition_type_for_code_address(regular_code_address)
        )

        self.assertEqual(
            BreakpointKind.CONDITIONAL, 
            self.breakpoint_manager.get_condition_type_for_code_address(conditional_code_address)
        )

        self.assertEqual(
            BreakpointKind.REGULAR, # Regular should override conditional
            self.breakpoint_manager.get_condition_type_for_code_address(colliding_code_address)
        )

        self.breakpoint_manager.remove_regular_breakpoint(colliding_code_address)
        self.assertEqual(
            BreakpointKind.CONDITIONAL, # Upon removing regular the conditional one should remain
            self.breakpoint_manager.get_condition_type_for_code_address(colliding_code_address)
        )
    


if __name__ == "__main__":
    unittest.main()        