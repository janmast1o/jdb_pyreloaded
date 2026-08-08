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

        # Assert that the split node does not have 'audit' children as its own
        self.assertEqual({k for k in split_node._children_nodes_map.keys()}, {"d", "t"})
        self.assertEqual(\
            {word for word, _ in split_node._children_nodes_map.values()}, 
            {"dit", "th"}
        )  


if __name__ == "__main__":
    unittest.main()