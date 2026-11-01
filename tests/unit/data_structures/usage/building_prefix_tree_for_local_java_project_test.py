import pathlib
import shutil
import tempfile
import unittest

from typing import List, Tuple

from src.data_structures.usage.build_project_prefix_tree_for_real_project import *


class BuildingPrefixTreeForLocalJavaProjectTest(unittest.TestCase):
    FULL_TREE_FILENAMES = [
        "api/v1/Parser.java", "api/v2/Parser.java", "api/v3/Parser.java",
        "audit/AuditLog.java", "audit/AuditEvent.java",
        "transaction/TransactionEvent.java",
        "db/index/IndexFactory.java", 
        "db/index/Trie.java", "db/index/btree/BTree.java", "db/index/btree/BPlusTree.java", 
        "threading/async/lw/Future.java", "threading/async/lw/FutureFactory.java",
        "threading/async/ll/NamedThreadFactory.java",
        "threading/async/ll/NamedThread.java", 
        "logalg/BinSearch.java",
        "Main.java", "log/ThreadSafeLogger.java", "log/Logger.java", "log/LoggerFactory.java",
        "auth/AuthEvent.java", "threading/lock/NamedLock.java"
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
        (4, f"FPN: word=AuthEvent, parent=th"),
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
        (4, f"FPN: word=NamedLock, parent=lock"),
        (2, f"PPN: word=ransaction, parent=t, dot_terminated=True"),
        (3, f"FPN: word=TransactionEvent, parent=ransaction")
    ]

    JAVA_PROJECT_ROOT_PATH = None

    @classmethod
    def setUpClass(cls):
        project_root = tempfile.mkdtemp()
        print(f"Created temporary directory: {project_root}")
        BuildingPrefixTreeForLocalJavaProjectTest.JAVA_PROJECT_ROOT_PATH = project_root
        for fully_qualified_filename in BuildingPrefixTreeForLocalJavaProjectTest.FULL_TREE_FILENAMES:
            file_path = pathlib.Path(os.path.join(project_root, fully_qualified_filename))
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as _:
                pass

        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(BuildingPrefixTreeForLocalJavaProjectTest.JAVA_PROJECT_ROOT_PATH)
        return super().tearDownClass()

    def test_env_variable_translation(self):
        home_dir = os.getenv("HOME")
        home_dir = home_dir.rstrip("/")
        os.environ["SOMEDIR"] = "some_dir"
        file_path = "$HOME/abc/${SOMEDIR}/def/xyz/"
        expected_file_path = f"{home_dir}/abc/some_dir/def/xyz/"
        self.assertEqual(expected_file_path, maybe_translate_env_variables(file_path))

    def test_real_java_project_tree_built_correctly(self):
        project_tree = build_project_prefix_tree_for_local_java_project(
            project_path=BuildingPrefixTreeForLocalJavaProjectTest.JAVA_PROJECT_ROOT_PATH,
            optional_pyjdb_target_list=[""]
        )
        list_representation = project_tree.get_list_representation()
        expected_list_representation = BuildingPrefixTreeForLocalJavaProjectTest.EXPECTED_TREE_REPRESENTATION
        self.assertEqual(len(expected_list_representation), len(list_representation))
        n = len(list_representation)

        for i in range(n):
            row = (list_representation[i][0], str(list_representation[i][1]))
            expected_row = expected_list_representation[i]
            failed_assertion_message = f"Failed assertion for: {row}, (expected={expected_row})"
            self.assertEqual(expected_row, row, failed_assertion_message)


if __name__ == "__main__":
    unittest.main()        
