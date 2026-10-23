import unittest

from src.data_structures.java_project_prefix_tree import *


class JavaProjectPrefixTreeNodesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent_node = JavaProjectPrefixTree.PackagePartNode("something", None, True)
        return super().setUpClass()
    
    def setUp(self):
        self.parent_node._children_nodes_map.clear()
        return super().setUp()
    
    def test_empty_package_part_child(self):
        self.parent_node.add_empty_package_part_child()
        empty_package_part_child = self.parent_node._children_nodes_map.get(
            JavaProjectPrefixTree.Node.EMPTY_KEY_MARKER, (None, None)
        )[1]

        self.assertIsNotNone(empty_package_part_child)
        self.assertEqual(empty_package_part_child.parent_node, self.parent_node)
        self.assertEqual(empty_package_part_child.word, "")

        self.assertEqual(empty_package_part_child.get_type_enum_value(), JavaProjectPrefixTree.NodeType.PACKAGE_PART)
        self.assertTrue(empty_package_part_child.dot_terminated) 
    
    def test_add_non_colliding_children_nodes(self):
        self.parent_node.add_new_child(
            "auth", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True
        )
        self.parent_node.add_new_child(
            "concurrency", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True
        )
        self.parent_node.add_new_child(
            "file", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True
        )

        self.parent_node.add_new_child("Daemon", JavaProjectPrefixTree.NodeType.FILE_PART)
        self.parent_node.add_new_child("Shell", JavaProjectPrefixTree.NodeType.FILE_PART)

        children_key_set = {k for k in self.parent_node._children_nodes_map.keys()}
        full_word_key_set = {"auth", "concurrency", "file", "Daemon", "Shell"}

        self.assertEqual(children_key_set, {k[0] for k in full_word_key_set})

        for key in full_word_key_set:
            k = key[0]
            word, child_node = self.parent_node._children_nodes_map[k]
            self.assertEqual(word, key)
            self.assertEqual(child_node.parent_node, self.parent_node)
            self.assertEqual(child_node.word, word)

            if k == k.lower():
                self.assertTrue(getattr(child_node, "dot_terminated"))

    def test_add_word_lambda_colliding_with_word_delta_with_common_prefix_shorter_than_both(self):
        delta_node = self.parent_node.add_new_child(
            "audit", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True
        )     

        delta_node.add_new_child("log", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True)
        delta_node.add_new_child("DirectorySetup", JavaProjectPrefixTree.NodeType.FILE_PART)

        auth_node = self.parent_node.add_new_child(
            "auth", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True
        ) 

        # Assert that the 'a' node has been properly split
        split_node_word, split_node = self.parent_node._children_nodes_map["a"] 
        self.assertEqual("au", split_node_word)
        self.assertEqual("au", split_node.word)
        self.assertEqual(self.parent_node, split_node.parent_node)
        self.assertEqual(split_node.get_type_enum_value(), JavaProjectPrefixTree.NodeType.PACKAGE_PART)
        self.assertFalse(getattr(split_node, "dot_terminated"))  

        # Assert that the split node points to 'dit' and 'th' nodes as children
        self.assertEqual({k for k in split_node._children_nodes_map.keys()}, {"d", "t"})
        self.assertEqual(\
            {word for word, _ in split_node._children_nodes_map.values()}, 
            {"dit", "th"}
        )  

        # Assert that the node correctly returned the newly inserted node ('auth' node)
        self.assertEqual(auth_node, split_node._children_nodes_map["t"][1])

        auth_node_word, auth_node = split_node._children_nodes_map["t"]
        audit_node_word, audit_node = split_node._children_nodes_map["d"]

        # Assert that 'auth' node correctly constructed
        self.assertEqual("th", auth_node_word)
        self.assertEqual("th", auth_node.word)
        self.assertEqual(split_node, auth_node.parent_node)
        self.assertEqual(auth_node.get_type_enum_value(), JavaProjectPrefixTree.NodeType.PACKAGE_PART)
        self.assertEqual(0, len(auth_node._children_nodes_map))
        self.assertTrue(getattr(auth_node, "dot_terminated"))

        # Assert that 'audit' node correctly constructed after splitting
        self.assertEqual("dit", audit_node_word)
        self.assertEqual("dit", audit_node.word)
        self.assertEqual(split_node, audit_node.parent_node)
        self.assertEqual(audit_node.get_type_enum_value(), JavaProjectPrefixTree.NodeType.PACKAGE_PART)
        self.assertEqual({k for k in audit_node._children_nodes_map.keys()}, {"l", "D"})
        self.assertEqual(
            {word for word, _ in audit_node._children_nodes_map.values()},
            {"log", "DirectorySetup"}
        )
        self.assertTrue(getattr(audit_node, "dot_terminated"))

    def test_add_word_lambda_colliding_with_word_delta_and_lambda_is_prefix_of_delta_with_dot_terminated(self):
        delta_node = self.parent_node.add_new_child(
            "concurrency", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True
        )

        thread_pool_node = delta_node.add_new_child("ThreadPool", JavaProjectPrefixTree.NodeType.FILE_PART)
        async_task_node = delta_node.add_new_child("AsyncTask", JavaProjectPrefixTree.NodeType.FILE_PART)

        con_node = self.parent_node.add_new_child(
            "con", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True
        )

        # Asset that 'con' node has been added correctly as the child of the parent node
        self.assertEqual(con_node, self.parent_node._children_nodes_map["c"][1])
        self.assertEqual("con", self.parent_node._children_nodes_map["c"][0])
        self.assertEqual("con", con_node.word)
        self.assertEqual(self.parent_node, con_node.parent_node)
        self.assertEqual(con_node.get_type_enum_value(), JavaProjectPrefixTree.NodeType.PACKAGE_PART)

        # 'con' node should have two children - one for 'concurrency' and one empty to denote dot termination
        self.assertFalse(getattr(con_node, "dot_terminated"))
        self.assertEqual({"c", JavaProjectPrefixTree.Node.EMPTY_KEY_MARKER}, {k for k in con_node._children_nodes_map.keys()})
        self.assertEqual(
            {"currency", ""}, {word for word, _ in con_node._children_nodes_map.values()}
        )

        # Assert that the empty dot terminated node has been constructed correctly
        empty_dot_terminated_node_word, empty_dot_terminated_node = con_node._children_nodes_map[JavaProjectPrefixTree.Node.EMPTY_KEY_MARKER]
        self.assertEqual("", empty_dot_terminated_node_word)
        self.assertEqual("", empty_dot_terminated_node.word)
        self.assertEqual(con_node, empty_dot_terminated_node.parent_node)
        self.assertEqual(con_node.get_type_enum_value(), JavaProjectPrefixTree.NodeType.PACKAGE_PART)
        self.assertTrue(getattr(empty_dot_terminated_node, "dot_terminated"))
        self.assertEqual(0, len(empty_dot_terminated_node._children_nodes_map))

        # Assert that 'concurrency' node has been correctly split and 'currency' has been pushed down the tree
        concurrency_node_word, concurrency_node = con_node._children_nodes_map["c"]
        self.assertEqual("currency", concurrency_node_word)
        self.assertEqual("currency", concurrency_node.word)
        self.assertEqual(con_node, concurrency_node.parent_node)
        self.assertEqual(concurrency_node.get_type_enum_value(), JavaProjectPrefixTree.NodeType.PACKAGE_PART)
        self.assertTrue(getattr(concurrency_node, "dot_terminated"))
        self.assertTrue({k for k in concurrency_node._children_nodes_map.keys()}, {"T", "A"})
        self.assertEqual(
            {word for word, _ in concurrency_node._children_nodes_map.values()},
            {"ThreadPool", "AsyncTask"}
        )

        # Assert that the children nodes of concurrency got correctly pushed down the tree with it
        self.assertEqual(thread_pool_node, concurrency_node._children_nodes_map["T"][1])
        self.assertEqual(async_task_node, concurrency_node._children_nodes_map["A"][1])

    def test_add_word_lambda_colliding_with_word_delta_and_lambda_is_prefix_of_delta_without_dot_termination(self):
        delta_node = self.parent_node.add_new_child(
            "concurrency", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True
        )

        thread_pool_node = delta_node.add_new_child("ThreadPool", JavaProjectPrefixTree.NodeType.FILE_PART)
        async_task_node = delta_node.add_new_child("AsyncTask", JavaProjectPrefixTree.NodeType.FILE_PART)

        con_node = self.parent_node.add_new_child(
            "con", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=False
        )

        # Asset that 'con' node has been added correctly as the child of the parent node
        self.assertEqual(con_node, self.parent_node._children_nodes_map["c"][1])
        self.assertEqual("con", self.parent_node._children_nodes_map["c"][0])
        self.assertEqual("con", con_node.word)
        self.assertEqual(self.parent_node, con_node.parent_node)
        self.assertEqual(con_node.get_type_enum_value(), JavaProjectPrefixTree.NodeType.PACKAGE_PART)

        # 'con' node should have two children - one for 'concurrency'
        self.assertFalse(getattr(con_node, "dot_terminated"))
        self.assertEqual({"c"}, {k for k in con_node._children_nodes_map.keys()})
        self.assertEqual(
            {"currency"}, {word for word, _ in con_node._children_nodes_map.values()}
        )

        # Assert that 'concurrency' node has been correctly split and 'currency' has been pushed down the tree
        concurrency_node_word, concurrency_node = con_node._children_nodes_map["c"]
        self.assertEqual("currency", concurrency_node_word)
        self.assertEqual("currency", concurrency_node.word)
        self.assertEqual(con_node, concurrency_node.parent_node)
        self.assertEqual(concurrency_node.get_type_enum_value(), JavaProjectPrefixTree.NodeType.PACKAGE_PART)
        self.assertTrue(getattr(concurrency_node, "dot_terminated"))
        self.assertTrue({k for k in concurrency_node._children_nodes_map.keys()}, {"T", "A"})
        self.assertEqual(
            {word for word, _ in concurrency_node._children_nodes_map.values()},
            {"ThreadPool", "AsyncTask"}
        )

        # Assert that the children nodes of concurrency got correctly pushed down the tree with it
        self.assertEqual(thread_pool_node, concurrency_node._children_nodes_map["T"][1])
        self.assertEqual(async_task_node, concurrency_node._children_nodes_map["A"][1])    

    def test_add_lambda_colliding_with_word_delta_and_delta_is_prefix_of_lambda(self):
        log_node = self.parent_node.add_new_child(
            "log", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True
        )    

        audit_noe = log_node.add_new_child(
            "audit", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True
        )
        directory_setup_node = log_node.add_new_child("DirectorySetup", JavaProjectPrefixTree.NodeType.FILE_PART)

        login_and_auth_utils_node = self.parent_node.add_new_child(
            "login_and_auth_utils", JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True
        )

        # Assert that `log` node is no longer node terminated and has "login_and_auth_utils" node as child 
        self.assertFalse(getattr(log_node, "dot_terminated"))
        self.assertIn(login_and_auth_utils_node, [child_node for _, child_node in log_node._children_nodes_map.values()])

        # Assert that 'log_and_auth_utils_node' has been correctly added
        self.assertEqual("in_and_auth_utils", login_and_auth_utils_node.word)
        self.assertEqual(log_node, login_and_auth_utils_node.parent_node)
        self.assertEqual(login_and_auth_utils_node.get_type_enum_value(), JavaProjectPrefixTree.NodeType.PACKAGE_PART)
        self.assertTrue(getattr(login_and_auth_utils_node, "dot_terminated"))
        self.assertEqual(0, len(login_and_auth_utils_node._children_nodes_map))

        # Assert other children of 'log' remain the same and also an empty dot terminated child has been added
        self.assertEqual(
            {k for k in log_node._children_nodes_map.keys()},
            {"i", "a", "D", JavaProjectPrefixTree.Node.EMPTY_KEY_MARKER}
        )
        self.assertEqual(
            {word for word, _ in log_node._children_nodes_map.values()}, 
            {"in_and_auth_utils", "audit", "DirectorySetup", ""}
        )

        empty_dot_terminated_node_word, empty_dot_terminated_node = log_node._children_nodes_map[JavaProjectPrefixTree.Node.EMPTY_KEY_MARKER]
        self.assertEqual("", empty_dot_terminated_node_word)
        self.assertEqual("", empty_dot_terminated_node.word)
        self.assertTrue(getattr(empty_dot_terminated_node, "dot_terminated"))


if __name__ == "__main__":
    unittest.main()