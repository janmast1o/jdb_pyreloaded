from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completer, CompleteEvent, Completion
from typing import Optional, List, Iterable
from typing_extensions import override

from src.data_structures.java_project_prefix_tree import JavaProjectPrefixTree
from src.data_structures.usage.build_project_prefix_tree_for_real_project import build_project_prefix_tree_for_local_java_project
from src.utils.custom_exceptions import SequenceNotStoredInPrefixTreeException


class JDBWrapperCompleter(Completer):
    def __init__(self, local_project_path: str, optional_pyjdb_target_list: Optional[List[str]]):
        self.project_prefix_tree = build_project_prefix_tree_for_local_java_project(local_project_path, optional_pyjdb_target_list)
        super().__init__()  

    @override
    def get_completions(self, document: Document, unimportant_complete_event: CompleteEvent) -> Iterable[Completion]:
        text_after_cursor = document.text_after_cursor
        # The library behaves differently than intuitively expected
        # when `document.get_word_before_cursor()` is called, therefore we have to 
        # use this weird workaround.
        word_before_cursor = document.text_before_cursor.split()[-1]
        # print(f"In get completions: {document.text_before_cursor}; {document.text_after_cursor}")

        if len(text_after_cursor) == 0 or text_after_cursor[0].isspace():
            node_containing_word: Optional[JavaProjectPrefixTree.Node] = None
            try:
                node_containing_word = self.project_prefix_tree.find_node_containing_prefix(word_before_cursor)
            except SequenceNotStoredInPrefixTreeException:
                node_containing_word = None

            if node_containing_word is None:
                # print("AA!")
                yield Completion("", start_position=0)
                return

            node_full_sequence_from_root = node_containing_word.get_full_sequence_from_the_root(include_possible_trailing_dot=True)
            # print(f"NFSFR: {node_full_sequence_from_root}")
            # print(f"word before cursor: {word_before_cursor}")
            if len(node_full_sequence_from_root) > len(word_before_cursor):
                # print("BB!")
                yield Completion(node_full_sequence_from_root, start_position=-len(word_before_cursor))
            else:
                node_children_map = node_containing_word.get_children_nodes_map()
                for _, child_node in node_children_map.values():
                    child_node_word = child_node.word
                    if getattr(child_node, "dot_terminated", False):
                        child_node_word = child_node_word + "."

                    yield Completion(child_node_word, start_position=0)         