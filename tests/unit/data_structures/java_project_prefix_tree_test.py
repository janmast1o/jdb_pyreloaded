import unittest

from src.data_structures.java_project_prefix_tree import *


class JavaProjectPrefixTreeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_tree: JavaProjectPrefixTree = JavaProjectPrefixTree()
        return super().setUpClass()

    def setUp(self):
        self.project_tree.clear_tree()
        return super().setUp()

    def test_only_one_file_per_top_level_module(self):
        fully_qualified_file_names = ["auth.A", "concurrency.B", "log.C", "service.D"]
        for fully_qualified_file_name in fully_qualified_file_names:
            self.project_tree.add_node(fully_qualified_file_name)

        root_module_nodes_list = [(k, v[0], v[1]) for k, v in self.project_tree.root._children_nodes_map.items()]
        root_module_nodes_list.sort(key=lambda x: x[0])

        module_names = [f.split(".")[0] for f in fully_qualified_file_names]
        self.assertEqual(len(module_names), len(root_module_nodes_list))
        for i in range(len(fully_qualified_file_names)):
            module_name = module_names[i]
            failed_assertion_message = f"Failed insertion for: {module_name}"
            l, word, node = root_module_nodes_list[i]
            self.assertEqual(module_name[0], l, failed_assertion_message)
            self.assertEqual(module_name, word, failed_assertion_message)
            self.assertEqual(JavaProjectPrefixTree.NodeType.PACKAGE_PART, node.get_type_enum_value(), failed_assertion_message)
            self.assertTrue(getattr(node, "dot_terminated"), failed_assertion_message)


if __name__ == "__main__":
    unittest.main()            