from abc import ABC as AbstractClass, abstractmethod
from typing import Optional, Dict, Tuple
from typing_extensions import override
from enum import Enum

from ..utils.util_functions import find_longest_common_prefix_of_two_words

class JavaProjectPrefixTree:

    class NodeType(Enum):
        PACKAGE_PART = 1
        FILE_PART = 2


    class Node(AbstractClass):
        EMPTY_KEY_MARKER = "<empty>"
        
        def __init__(self, word: str, parent_node: Optional["JavaProjectPrefixTree.Node"]):
            self.word: str = word
            self.parent_node: Optional["JavaProjectPrefixTree.Node"] = parent_node
            # Children nodes map: 
            #   - key: first character of a string associated with a branch to an existing child node
            #   - value: a tuple of the full string associated with the above mentioned branch and a child node 
            # 
            # Example: node is associated with path 'com.companyname.productname',
            # children nodes map: {'a' : <'auth', ...>, 'n' : <'net', ...>}
            # Conclusion: auth and net are subpackages in the project
            self._children_nodes_map: Dict[str, Tuple[str, "JavaProjectPrefixTree.Node"]] = {}

        @abstractmethod
        def get_type_enum_value(self) -> "JavaProjectPrefixTree.NodeType":
            pass

        def _move_children_map_from_other_node(self, other_node: "JavaProjectPrefixTree.Node") -> None:
            self._children_nodes_map = other_node._children_nodes_map
            other_node._children_nodes_map = None
            for _, child_node in self._children_nodes_map.values():
                child_node.parent_node = self

        def add_new_child(self, new_child_word: str, node_type: "JavaProjectPrefixTree.NodeType", **kwargs) -> "JavaProjectPrefixTree.Node":
            if len(new_child_word) == 0:
                raise Exception("Cannot append a child node with an empty associated word")
            
            # Get the first character of the new word
            c = new_child_word[0]
            if c not in self._children_nodes_map:
                child_node: JavaProjectPrefixTree.Node = None
                if node_type == JavaProjectPrefixTree.NodeType.PACKAGE_PART:
                    child_node = JavaProjectPrefixTree.PackagePartNode(new_child_word, self, kwargs["dot_terminated"])
                elif node_type == JavaProjectPrefixTree.NodeType.FILE_PART:
                    child_node = JavaProjectPrefixTree.FilePartNode(new_child_word, self)

                assert child_node is not None
                self._children_nodes_map[c] = (new_child_word, child_node)
                return child_node

            preexisting_child_word = self._children_nodes_map[c][0]
            # Do not modify the tree if the node preexists
            if preexisting_child_word == new_child_word:
                child_node = self._children_nodes_map[c][1]
                if child_node.get_type_enum_value() != node_type:
                    raise Exception("Node preexists, but is not of the same type")

            longest_common_prefix = find_longest_common_prefix_of_two_words(preexisting_child_word, new_child_word)
            n = len(longest_common_prefix)

            b_node = self._children_nodes_map[c][1]
            b_node_type = b_node.get_type_enum_value()

            if n < len(new_child_word) and n < len(preexisting_child_word):
                split_node: JavaProjectPrefixTree.Node = None
                if b_node == JavaProjectPrefixTree.NodeType.PACKAGE_PART:
                    self._children_nodes_map[c] = (
                        longest_common_prefix, 
                        split_node := JavaProjectPrefixTree.PackagePartNode(
                            word=longest_common_prefix, 
                            parent_node=self, 
                            dot_terminated=False
                        )
                    )
                    split_node.add_new_child(
                        preexisting_child_word[n:], b_node_type, b_node.dot_terminated
                    )._move_children_map_from_other_node(b_node)

                elif b_node == JavaProjectPrefixTree.NodeType.FILE_PART:
                    self._children_nodes_map[c] = (
                        longest_common_prefix, 
                        split_node := JavaProjectPrefixTree.FilePartNode(
                            word=longest_common_prefix, 
                            parent_node=self
                        )
                    )
                    split_node.add_new_child(
                        preexisting_child_word[n:], b_node_type
                    )._move_children_map_from_other_node(b_node)

                split_node.add_new_child(longest_common_prefix[n:], node_type, kwargs)    

            elif n < len(preexisting_child_word): # longest_common_prefix == new_child_word
                suffix = preexisting_child_word[n:]  
                new_node: JavaProjectPrefixTree.Node = None
                if node_type == JavaProjectPrefixTree.NodeType.PACKAGE_PART:
                    self._children_nodes_map[c] = (
                        longest_common_prefix, 
                        new_node := JavaProjectPrefixTree.PackagePartNode(
                            word=longest_common_prefix, 
                            parent_node=self, 
                            dot_terminated=False
                        )
                    )
                    if kwargs["dot_terminated"]:
                        new_node._children_nodes_map[self.EMPTY_KEY_MARKER] = JavaProjectPrefixTree.PackagePartNode(
                            "", new_node, True
                        )

                elif node_type == JavaProjectPrefixTree.NodeType.FILE_PART:
                    self._children_nodes_map[c] = (
                        longest_common_prefix, 
                        new_node := JavaProjectPrefixTree.FilePartNode(
                            word=longest_common_prefix, 
                            parent_node=self
                        )
                    )

                new_node._children_nodes_map[suffix[0]] = (suffix, b_node)
                b_node.word = suffix
                b_node.parent_node = new_node
                return new_node

            elif n < len(new_child_word): # longest_common_prefix == preexisting_child_word    
                suffix = new_child_word[n:]
                new_node = b_node.add_new_child(suffix, node_type, kwargs)
                if b_node_type == JavaProjectPrefixTree.NodeType.PACKAGE_PART and b_node.dot_terminated:
                    b_node.dot_terminated = False
                    b_node._children_nodes_map[self.EMPTY_KEY_MARKER] = JavaProjectPrefixTree.PackagePartNode(
                        "", b_node, True
                    )

                return new_node

            # This part of the code should never be reached
            assert False     


    class PackagePartNode(Node):
        def __init__(self,  word: str, parent_node: Optional["JavaProjectPrefixTree.Node"], dot_terminated: bool = True):
            super().__init__(word, parent_node)
            # Dot terminated - signifies that children are different package parts
            self.dot_terminated: bool = dot_terminated

        @override
        def get_type_enum_value(self) -> "JavaProjectPrefixTree.NodeType":
            return JavaProjectPrefixTree.NodeType.PACKAGE_PART


    class FilePartNode(Node):
        def __init__(self, word: str, parent_node: Optional["JavaProjectPrefixTree.Node"]):
            super().__init__(word, parent_node)

        @override
        def get_type_enum_value(self) -> "JavaProjectPrefixTree.NodeType":
            return JavaProjectPrefixTree.NodeType.FILE_PART


    def __init__(self):
        self.root: "JavaProjectPrefixTree.PackagePartNode" = JavaProjectPrefixTree.PackagePartNode("", None, False)

    def add_node(self, word: str) -> None:
        word_parts = word.split(sep=".")    
        last_index = len(word_parts) - 1
        word_index, letter_index = 0, 0

        node = self.root
        word = word_parts[word_index]
        word_length = len(word)

        while node is not None:
            candidate_word, candidate_node = node._children_nodes_map.get(word[letter_index], ("", None))[0]
            longest_common_prefix = find_longest_common_prefix_of_two_words(candidate_word, word[letter_index:])
            n = len(longest_common_prefix)
            if longest_common_prefix == candidate_word:
                if longest_common_prefix == word[letter_index:]:
                    ...