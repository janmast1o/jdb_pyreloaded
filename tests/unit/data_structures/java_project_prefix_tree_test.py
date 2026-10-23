import random
import unittest

from src.data_structures.java_project_prefix_tree import *
from src.utils.custom_exceptions import SequenceNotStoredInPrefixTreeException


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
        "Main", "log.ThreadSafeLogger", "log.Logger", "log.LoggerFactory",
        "logalg.BinSearch"
    ]

    @classmethod
    def setUpClass(cls):
        cls.project_tree: JavaProjectPrefixTree = JavaProjectPrefixTree()
        return super().setUpClass()

    def setUp(self):
        self.project_tree.clear_tree()
        return super().setUp()

    def test_only_top_level_modules(self):
        module_names = ["auth", "concurrency", "log", "service"]
        for module in module_names:
            self.project_tree.add_node(module)

        root_module_nodes_list = [(k, v[0], v[1]) for k, v in self.project_tree.root._children_nodes_map.items()]
        root_module_nodes_list.sort(key=lambda x: x[0])

        self.assertEqual(len(module_names), len(root_module_nodes_list))
        for i in range(len(module_names)):
            module_name = module_names[i]
            failed_assertion_message = f"Failed insertion for: {module_name}"
            l, word, node = root_module_nodes_list[i]
            self.assertEqual(module_name[0], l, failed_assertion_message)
            self.assertEqual(module_name, word, failed_assertion_message)
            self.assertEqual(JavaProjectPrefixTree.NodeType.PACKAGE_PART, node.get_type_enum_value(), failed_assertion_message)
            self.assertTrue(getattr(node, "dot_terminated"), failed_assertion_message)
            self.assertEqual(0, len(node._children_nodes_map), failed_assertion_message)

    def test_insertions_do_not_break_the_tree(self):
        module_names = ["auth", "concurrency", "log", "service"]
        for module in module_names:
            self.project_tree.add_node(module)

        def internal_run_assertions() -> None:
            root_module_nodes_list = [(k, v[0], v[1]) for k, v in self.project_tree.root._children_nodes_map.items()]
            root_module_nodes_list.sort(key=lambda x: x[0])

            self.assertEqual(len(module_names), len(root_module_nodes_list))
            for i in range(len(module_names)):
                module_name = module_names[i]
                failed_assertion_message = f"Failed insertion for: {module_name}"
                l, word, node = root_module_nodes_list[i]
                self.assertEqual(module_name[0], l, failed_assertion_message)
                self.assertEqual(module_name, word, failed_assertion_message)
                self.assertEqual(JavaProjectPrefixTree.NodeType.PACKAGE_PART, node.get_type_enum_value(), failed_assertion_message)
                self.assertTrue(getattr(node, "dot_terminated"), failed_assertion_message)
                self.assertEqual(0, len(node._children_nodes_map), failed_assertion_message)

        internal_run_assertions()
        for module in module_names:
            self.project_tree.add_node(module)        

    def test_only_one_file_per_top_level_module(self):
        fully_qualified_file_names = ["auth.A", "concurrency.C", "log.L", "service.S"]
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

            # Assert that the single child has been added properly
            self.assertEqual(1, len(node._children_nodes_map), failed_assertion_message)
            file_word: str = node._children_nodes_map.get(module_name[0].upper(), None)[0]
            self.assertEqual(word[0].upper(), file_word, failed_assertion_message)
            file_node: JavaProjectPrefixTree.FilePartNode = node._children_nodes_map.get(module_name[0].upper(), None)[1]
            self.assertIsNotNone(file_node, failed_assertion_message)
            self.assertEqual(JavaProjectPrefixTree.NodeType.FILE_PART, file_node.get_type_enum_value(), failed_assertion_message)
            self.assertEqual(word[0].upper(), file_node.word, failed_assertion_message)
            self.assertEqual(0, len(file_node._children_nodes_map), failed_assertion_message)

    def test_non_trivial_module_structure(self):
        module_names = [
            "api", "api.v1", "api.v2", "api.v3",
            "auth", "audit", "transaction", "threading",
            "threading.lock", "threading.async",
            "threading.async.lw", "threading.async.ll",
            "log", "logalg", "db", "db.index", "db.index.btree"
        ]
        random.shuffle(module_names)
        for module in module_names:
            self.project_tree.add_node(module)

        tree_list_representation = self.project_tree.get_list_representation()
        expected_list_representation: List[Tuple[int, str]] = [
            (0, f"PPN: word=<empty>, parent=None, dot_terminated=False"), # root
            (1, f"PPN: word=a, parent=<empty>, dot_terminated=False"),
            (2, f"PPN: word=pi, parent=a, dot_terminated=True"),
            (3, f"PPN: word=v, parent=pi, dot_terminated=False"),
            (4, f"PPN: word=1, parent=v, dot_terminated=True"),
            (4, f"PPN: word=2, parent=v, dot_terminated=True"),
            (4, f"PPN: word=3, parent=v, dot_terminated=True"),
            (2, f"PPN: word=u, parent=a, dot_terminated=False"),
            (3, f"PPN: word=dit, parent=u, dot_terminated=True"),
            (3, f"PPN: word=th, parent=u, dot_terminated=True"),
            (1, f"PPN: word=db, parent=<empty>, dot_terminated=True"),
            (2, f"PPN: word=index, parent=db, dot_terminated=True"),
            (3, f"PPN: word=btree, parent=index, dot_terminated=True"),
            (1, f"PPN: word=log, parent=<empty>, dot_terminated=False"),
            (2, f"PPN: word=<empty>, parent=log, dot_terminated=True"),
            (2, f"PPN: word=alg, parent=log, dot_terminated=True"),
            (1, f"PPN: word=t, parent=<empty>, dot_terminated=False"),
            (2, f"PPN: word=hreading, parent=t, dot_terminated=True"),
            (3, f"PPN: word=async, parent=hreading, dot_terminated=True"),
            (4, f"PPN: word=l, parent=async, dot_terminated=False"),
            (5, f"PPN: word=l, parent=l, dot_terminated=True"),
            (5, f"PPN: word=w, parent=l, dot_terminated=True"),
            (3, f"PPN: word=lock, parent=hreading, dot_terminated=True"),
            (2, f"PPN: word=ransaction, parent=t, dot_terminated=True")
        ]

        n = len(tree_list_representation)
        self.assertEqual(n, len(expected_list_representation))
        for i in range(n):
            tree_row = tree_list_representation[i]
            expected_row = expected_list_representation[i]
            failed_assertion_message = f"Failed assertion for: {expected_row}"
            self.assertEqual(expected_row[0], tree_row[0], failed_assertion_message)
            self.assertEqual(expected_row[1], str(tree_row[1]), failed_assertion_message)

    def test_non_trivial_full_project_structure(self):
        file_names = JavaProjectPrefixTreeTest.FULL_TREE_FILENAMES
        for file in file_names:
            self.project_tree.add_node(file)

        leaf_modules = [
            "auth", "log", "threading.lock"
        ]
        for module in leaf_modules:
            self.project_tree.add_node(module)

        tree_list_representation = self.project_tree.get_list_representation()
        for row in tree_list_representation:
            print(row)
        # for row in tree_list_representation:
        #     print(row)
        expected_list_representation: List[Tuple[int, str]] = [
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

        n = len(tree_list_representation)
        self.assertEqual(n, len(expected_list_representation))
        for i in range(n):
            tree_row = tree_list_representation[i]
            expected_row = expected_list_representation[i]
            failed_assertion_message = f"Failed assertion for: {expected_row}"
            self.assertEqual(expected_row[0], tree_row[0], failed_assertion_message)
            self.assertEqual(expected_row[1], str(tree_row[1]), failed_assertion_message)

    def test_try_find_prefixes_that_do_not_exist_in_tree(self):
        file_names = JavaProjectPrefixTreeTest.FULL_TREE_FILENAMES
        for file in file_names:
            self.project_tree.add_node(file)

        leaf_modules = [
            "auth", "log", "threading.lock"
        ]
        for module in leaf_modules:
            self.project_tree.add_node(module)

        non_existent_prefixes = [
            "dbc", "db.c", "db.indez", "db.indexes", "db.index.es", 
            "a.", "t.", "tr.", "threa.", "threading.asyn."
        ]
        for prefix in non_existent_prefixes:
            e: Exception = None
            try:
                self.project_tree.find_node_containing_prefix(prefix)
            except Exception as method_call_exception:
                e = method_call_exception
            finally:
                self.assertIsInstance(e, SequenceNotStoredInPrefixTreeException, f"Assertion failed for {prefix}")

    def test_empty_prefix_returns_root(self):
        file_names = JavaProjectPrefixTreeTest.FULL_TREE_FILENAMES
        for file in file_names:
            self.project_tree.add_node(file)

        matched_node, is_full_match = self.project_tree.find_node_containing_prefix("")
        self.assertIs(self.project_tree.root, matched_node)
        self.assertTrue(is_full_match)

    def test_try_find_prefixes_that_do_not_exist_in_tree(self):
        file_names = JavaProjectPrefixTreeTest.FULL_TREE_FILENAMES
        for file in file_names:
            self.project_tree.add_node(file)

        self.project_tree.add_node("log")
        self.project_tree.add_node("auth")




if __name__ == "__main__":
    unittest.main()            