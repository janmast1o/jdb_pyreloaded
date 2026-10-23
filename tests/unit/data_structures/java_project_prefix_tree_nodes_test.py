import unittest

from src.data_structures.java_project_prefix_tree import *


NodeType = JavaProjectPrefixTree.NodeType
Node = JavaProjectPrefixTree.Node
PackagePartNode = JavaProjectPrefixTree.PackagePartNode
FilePartNode = JavaProjectPrefixTree.FilePartNode


class JavaProjectPrefixTreeNodesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent_node = PackagePartNode("something", None, True)
        return super().setUpClass()
    
    def setUp(self):
        self.parent_node._children_nodes_map.clear()
        return super().setUp()
    
    def test_get_node_type(self):
        package_part_node = PackagePartNode("somegpackage", NodeType.PACKAGE_PART, dot_terminated=True)
        self.assertEqual(NodeType.PACKAGE_PART, package_part_node.get_type_enum_value())
        file_part_node = FilePartNode("Somefile", NodeType.FILE_PART)
        self.assertEqual(NodeType.FILE_PART, file_part_node.get_type_enum_value())

    def test_add_new_children(self):
        expected_new_children_names_and_types: List[Tuple[str, NodeType]] = [
            ("concurrency", NodeType.PACKAGE_PART), ("threading", NodeType.PACKAGE_PART),
            ("Main", NodeType.FILE_PART), ("ActivityMonitor", NodeType.FILE_PART)
        ]

        for child_name, child_node_type in expected_new_children_names_and_types:
            if child_node_type == NodeType.PACKAGE_PART:
                self.parent_node.add_new_child(child_name, child_node_type, dot_terminated=True)
            else:
                self.parent_node.add_new_child(child_name, child_node_type)

        actual_parent_node_children = [(l, child_item) for l, child_item in self.parent_node._children_nodes_map.items()]
        expected_new_children_names_and_types.sort(key=lambda x: x[0])
        actual_parent_node_children.sort(key=lambda x: x[0])

        self.assertEqual(len(expected_new_children_names_and_types), len(actual_parent_node_children))
        n = len(expected_new_children_names_and_types)
        for i in range(n):
            expected_child_word, expected_child_node_type = expected_new_children_names_and_types[i]
            expected_child_letter_key = expected_child_word[0]
            actual_child_letter_key, (actual_child_word, actual_child_node) = actual_parent_node_children[i]

            assertion_failed_message = f"Assertion failed for {expected_new_children_names_and_types[i]}"
            self.assertEqual(expected_child_letter_key, actual_child_letter_key, assertion_failed_message)
            self.assertEqual(expected_child_word, actual_child_word, assertion_failed_message)
            self.assertEqual(expected_child_node_type, actual_child_node.get_type_enum_value(), assertion_failed_message)

    def test_new_child_addition_blocked_on_collision(self):
        self.parent_node.add_new_child("transactions", NodeType.PACKAGE_PART, dot_terminated=True)
        e: Exception = None

        try:
            self.parent_node.add_new_child("threading", NodeType.PACKAGE_PART, dot_terminated=True)
        except Exception as surfaced_exception:
            e = surfaced_exception

        self.assertIsNotNone(e)
        self.assertIsInstance(e, Exception)                 

    def test_move_children_from_other_node(self):
        transfer_source_node = self.parent_node
        transfer_source_node.add_new_child("concurrency", NodeType.PACKAGE_PART, dot_terminated=True)
        transfer_source_node.add_new_child("logging", NodeType.PACKAGE_PART, dot_terminated=True)
        transfer_source_node.add_new_child("Main", NodeType.FILE_PART)
        nodes_map = transfer_source_node._children_nodes_map

        transfer_destination_node = PackagePartNode(word="", parent_node=None)
        transfer_destination_node._move_children_map_from_other_node(transfer_source_node)
        self.assertIs(nodes_map, transfer_destination_node._children_nodes_map)
        self.assertEqual(3, len(transfer_destination_node._children_nodes_map))
        self.assertEqual(0, len(transfer_source_node._children_nodes_map))

        for _, child_node in transfer_destination_node._children_nodes_map.values():
            self.assertEqual(transfer_destination_node, child_node.parent_node)

    def test_add_empty_package_part_dot_terminated_child(self):
        empty_package_part_dot_terminated_node = self.parent_node.add_empty_package_part_dot_terminated_child()
        self.assertTrue(Node.EMPTY_KEY_MARKER in self.parent_node._children_nodes_map)
        self.assertIsInstance(empty_package_part_dot_terminated_node, PackagePartNode)
        self.assertEqual("", empty_package_part_dot_terminated_node.word)
        self.assertTrue(getattr(empty_package_part_dot_terminated_node, "dot_terminated", False))

    def test_split_node(self):
        node = self.parent_node.add_new_child("company", NodeType.PACKAGE_PART, dot_terminated=True)
        node.add_new_child("concurrency", NodeType.PACKAGE_PART, dot_terminated=True)
        node.add_new_child("threading", NodeType.PACKAGE_PART, dot_terminated=True) 
        node.add_new_child("Main", NodeType.FILE_PART)
        children_nodes = node._children_nodes_map
        prefix_node, suffix_node = node.split_node(2)

        self.assertEqual("com", prefix_node.word)
        self.assertEqual(self.parent_node, prefix_node.parent_node)
        self.assertFalse(prefix_node.dot_terminated)
        self.assertEqual({"p" : ("pany", suffix_node)}, prefix_node._children_nodes_map)
        self.assertEqual({"c" : ("com", prefix_node)}, self.parent_node._children_nodes_map)

        self.assertEqual("pany", suffix_node.word)
        self.assertTrue(suffix_node.dot_terminated)
        self.assertEqual(prefix_node, suffix_node.parent_node)
        self.assertIs(children_nodes, suffix_node._children_nodes_map)


if __name__ == "__main__":
    unittest.main()