import random
import re
import unittest

from src.data_structures.java_project_prefix_tree import *
from src.utils.custom_exceptions import SequenceNotStoredInPrefixTreeException


NodeType = JavaProjectPrefixTree.NodeType
Node = JavaProjectPrefixTree.Node
PackagePartNode = JavaProjectPrefixTree.PackagePartNode
FilePartNode = JavaProjectPrefixTree.FilePartNode


random.seed(12345)


class JavaProjectPrefixTreeTest(unittest.TestCase):
    FULL_TREE_FILENAMES = [
        "api.v1.Parser", "api.v2.Parser", "api.v3.Parser",
        "audit.AuditLog", "audit.AuditEvent",
        "transaction.TransactionEvent",
        "db.index.IndexFactory", 
        "db.index.Trie", "db.index.btree.BTree", "db.index.btree.BPlusTree", 
        "threading.async.lw.Future", "threading.async.lw.FutureFactory",
        "threading.async.ll.NamedThreadFactory",
        "threading.async.ll.NamedThread", 
        "logalg.BinSearch",
        "Main", "log.ThreadSafeLogger", "log.Logger", "log.LoggerFactory",
        # Also includes modules without files
        "auth", "threading.lock"
    ]

    EXPECTED_TREE_REPRESENTATION: List[Tuple[int, str]] = [
        (0, f"PPN: word=<empty>, parent=None, dot_terminated=False"), # root
        (1, f"PPN: word=a, parent=<empty>, dot_terminated=False"),
        (2, f"PPN: word=pi, parent=a, dot_terminated=True"),
        (3, f"PPN: word=v, parent=pi, dot_terminated=False"),
        (4, f"PPN: word=1, parent=v, dot_terminated=True"),
        (5, f"FPN: word=Parser, parent=1"),
        (4, f"PPN: word=2, parent=v, dot_terminated=True"),
        (5, f"FPN: word=Parser, parent=2"),
        (4, f"PPN: word=3, parent=v, dot_terminated=True"),
        (5, f"FPN: word=Parser, parent=3"),
        (2, f"PPN: word=u, parent=a, dot_terminated=False"),
        (3, f"PPN: word=dit, parent=u, dot_terminated=True"),
        (4, f"FPN: word=Audit, parent=dit"),
        (5, f"FPN: word=Event, parent=Audit"),
        (5, f"FPN: word=Log, parent=Audit"),
        (3, f"PPN: word=th, parent=u, dot_terminated=True"),
        (1, f"PPN: word=db, parent=<empty>, dot_terminated=True"),
        (2, f"PPN: word=index, parent=db, dot_terminated=True"),
        (3, f"PPN: word=btree, parent=index, dot_terminated=True"),
        (4, f"FPN: word=B, parent=btree"),
        (5, f"FPN: word=PlusTree, parent=B"),
        (5, f"FPN: word=Tree, parent=B"),
        (3, f"FPN: word=IndexFactory, parent=index"),
        (3, f"FPN: word=Trie, parent=index"),
        (1, f"PPN: word=log, parent=<empty>, dot_terminated=False"),
        (2, f"PPN: word=<empty>, parent=log, dot_terminated=True"),
        (3, f"FPN: word=Logger, parent=<empty>"),
        (4, f"FPN: word=Factory, parent=Logger"),
        (3, f"FPN: word=ThreadSafeLogger, parent=<empty>"),
        (2, f"PPN: word=alg, parent=log, dot_terminated=True"),
        (3, f"FPN: word=BinSearch, parent=alg"),
        (1, f"FPN: word=Main, parent=<empty>"),
        (1, f"PPN: word=t, parent=<empty>, dot_terminated=False"),
        (2, f"PPN: word=hreading, parent=t, dot_terminated=True"),
        (3, f"PPN: word=async, parent=hreading, dot_terminated=True"),
        (4, f"PPN: word=l, parent=async, dot_terminated=False"),
        (5, f"PPN: word=l, parent=l, dot_terminated=True"),
        (6, f"FPN: word=NamedThread, parent=l"),
        (7, f"FPN: word=Factory, parent=NamedThread"),
        (5, f"PPN: word=w, parent=l, dot_terminated=True"),
        (6, f"FPN: word=Future, parent=w"),
        (7, f"FPN: word=Factory, parent=Future"),
        (3, f"PPN: word=lock, parent=hreading, dot_terminated=True"),
        (2, f"PPN: word=ransaction, parent=t, dot_terminated=True"),
        (3, f"FPN: word=TransactionEvent, parent=ransaction")
    ]

    @classmethod
    def setUpClass(cls):
        cls.project_tree: JavaProjectPrefixTree = JavaProjectPrefixTree()
        return super().setUpClass()

    def setUp(self):
        self.project_tree.clear_tree()
        return super().setUp()

    def build_project_tree_manually(self):
        expected_tree_representation = JavaProjectPrefixTreeTest.EXPECTED_TREE_REPRESENTATION
        node = self.project_tree.root
        current_depth = 0

        # Returns node type, word, parent word and if is dot-terminated.
        def internal_extract_node_data_from_string_metadata(metadata: str) -> Tuple[NodeType, str, str, bool]:
            node_type: NodeType = None
            if metadata.startswith("PPN"):
                node_type = NodeType.PACKAGE_PART
                metadata = metadata.lstrip("PPN: ")
            elif metadata.startswith("FPN"):
                node_type = NodeType.FILE_PART
                metadata = metadata.lstrip("FPN: ")

            word: str = None
            parent_word: str = None
            dot_terminated: bool = False
            properties: Tuple[str, str] = [tuple(p_text.split("=")) for p_text in metadata.split()]
            for property, value in properties:
                value = value.rstrip(",")
                if property == "word": 
                    word = value
                elif property == "parent":
                    parent_word = value
                elif property == "dot_terminated":
                    dot_terminated = True if value == "True" else False

            return node_type, word, parent_word, dot_terminated        

        for new_node_depth, new_node_metadata in expected_tree_representation:
            new_node_type, new_word, new_node_parent_word, new_node_dot_terminated = internal_extract_node_data_from_string_metadata(new_node_metadata)
            if new_node_depth == 0:
                # Skipping root construction.
                continue
            elif new_node_depth > current_depth+1:
                raise Exception(f"Implementation error or malformed static class variable, caught error at: {(new_word, new_node_depth)}")
            while new_node_depth < current_depth+1:
                node = node.parent_node
                current_depth -= 1

            failed_assertion_message = f"Failed insertion for: {(new_word, new_node_parent_word, new_node_depth)}"
            # Only should be executed when `new_node_depth == current_depth+1`
            self.assertEqual(node.word, new_node_parent_word if (current_depth > 0 and new_node_parent_word != "<empty>") else "", failed_assertion_message)
            if new_node_type == NodeType.PACKAGE_PART:
                if new_word == "<empty>":
                    node = node.add_empty_package_part_dot_terminated_child()
                else:
                    node = node.add_new_child(new_word, NodeType.PACKAGE_PART, dot_terminated=new_node_dot_terminated)
            else:
                node = node.add_new_child(new_word, NodeType.FILE_PART)
            current_depth += 1

        list_representation = self.project_tree.get_list_representation()
        self.assertEqual(len(expected_tree_representation), len(list_representation))
        n = len(list_representation)

        for i in range(n):
            row = (list_representation[i][0], str(list_representation[i][1]))
            expected_row = expected_tree_representation[i]
            failed_assertion_message = f"Failed assertion for {expected_row}"
            self.assertEqual(expected_row, row, failed_assertion_message)

    def test_find_longest_common_prefix_with_the_tree(self):
        self.build_project_tree_manually()

        def internal_run_assertions(node: Node, word_index: int, 
                                    letter_index: int, package_part_matched: bool,
                                    expected_node_word: str,
                                    expected_word_index: int, expected_letter_index: int,
                                    expected_package_part_matched: bool) -> None:
            self.assertEqual(expected_node_word, node.word)
            self.assertEqual(expected_word_index, word_index)
            self.assertEqual(expected_letter_index, letter_index)
            self.assertEqual(expected_package_part_matched, package_part_matched)

        node, word_index, letter_index, _ = self.project_tree.find_longest_common_prefix_with_word("")
        self.assertIs(node, self.project_tree.root)
        self.assertEqual(0, word_index)
        self.assertEqual(-1, letter_index)

        node, word_index, letter_index, _ = self.project_tree.find_longest_common_prefix_with_word("zebra")
        self.assertIs(node, self.project_tree.root)
        self.assertEqual(0, word_index)
        self.assertEqual(-1, letter_index)


        node, word_index, letter_index, package_part_matched = self.project_tree.find_longest_common_prefix_with_word("api")
        internal_run_assertions(node, word_index, letter_index, package_part_matched, "pi", 0, 2, True)

        node, word_index, letter_index, package_part_matched = self.project_tree.find_longest_common_prefix_with_word("api.")
        internal_run_assertions(node, word_index, letter_index, package_part_matched, "pi", 0, 2, True)

        node, word_index, letter_index, package_part_matched = self.project_tree.find_longest_common_prefix_with_word("api.v")
        internal_run_assertions(node, word_index, letter_index, package_part_matched, "v", 1, 0, False)

        node, word_index, letter_index, package_part_matched = self.project_tree.find_longest_common_prefix_with_word("api.v4")
        internal_run_assertions(node, word_index, letter_index, package_part_matched, "v", 1, 0, False)

        node, word_index, letter_index, package_part_matched = self.project_tree.find_longest_common_prefix_with_word("api.v256")
        internal_run_assertions(node, word_index, letter_index, package_part_matched, "2", 1, 1, False)

        # Case (4)
        node, word_index, letter_index, package_part_matched = self.project_tree.find_longest_common_prefix_with_word("threading.asyxyz.lock")
        internal_run_assertions(node, word_index, letter_index, package_part_matched, "async", 1, 2, False)

        # Case (3)
        node, word_index, letter_index, package_part_matched = self.project_tree.find_longest_common_prefix_with_word("threading.asyncxyz.lock")
        internal_run_assertions(node, word_index, letter_index, package_part_matched, "async", 1, 4, False)

        # Case (2)
        node, word_index, letter_index, package_part_matched = self.project_tree.find_longest_common_prefix_with_word("threading.as")
        internal_run_assertions(node, word_index, letter_index, package_part_matched, "async", 1, 1, False)

        node, word_index, letter_index, package_part_matched = self.project_tree.find_longest_common_prefix_with_word("log")
        internal_run_assertions(node, word_index, letter_index, package_part_matched, "log", 0, 2, False)

        node, word_index, letter_index, package_part_matched = self.project_tree.find_longest_common_prefix_with_word("log.")
        internal_run_assertions(node, word_index, letter_index, package_part_matched, "", 0, 2, True)

        node, word_index, letter_index, package_part_matched = self.project_tree.find_longest_common_prefix_with_word("log.Formatter")
        internal_run_assertions(node, word_index, letter_index, package_part_matched, "", 0, 2, True)
    
    def test_build_project_tree(self):
        full_tree_filenames = JavaProjectPrefixTreeTest.FULL_TREE_FILENAMES
        for fully_qualified_filename in full_tree_filenames:
            self.project_tree.add_node(fully_qualified_filename)

        list_representation = self.project_tree.get_list_representation()
        for row in list_representation:
            print(row) 
        expected_list_representation = JavaProjectPrefixTreeTest.EXPECTED_TREE_REPRESENTATION
        self.assertEqual(len(list_representation), len(expected_list_representation))
        n = len(list_representation)

        for i in range(n):
            row = (list_representation[i][0], str(list_representation[i][1]))
            expected_row = expected_list_representation[i]
            failed_assertion_message = f"Failed assertion for: {row}"
            self.assertEqual(row, expected_row, failed_assertion_message)

if __name__ == "__main__":
    unittest.main()            