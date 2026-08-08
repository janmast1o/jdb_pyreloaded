from abc import ABC as AbstractClass, abstractmethod
from typing import Optional, Dict, Tuple
from typing_extensions import override
from enum import Enum

from src.utils.util_functions import find_longest_common_prefix_of_two_words

# TODO: Add node/word removal support. 
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

        def add_empty_package_part_child(self):
            self._children_nodes_map[self.EMPTY_KEY_MARKER] = ("", JavaProjectPrefixTree.PackagePartNode("", self, True))   

        def add_new_child(self, new_child_word: str, node_type: "JavaProjectPrefixTree.NodeType", **kwargs) -> "JavaProjectPrefixTree.Node":
            if len(new_child_word) == 0:
                raise Exception("Cannot append a file part child node with an empty associated word")
            
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

            # print("Longest common prefix:", longest_common_prefix)
            # print(new_child_word, preexisting_child_word)

            if n < len(new_child_word) and n < len(preexisting_child_word):
                split_node: JavaProjectPrefixTree.Node = None
                if b_node_type == JavaProjectPrefixTree.NodeType.PACKAGE_PART:
                    self._children_nodes_map[c] = (
                        longest_common_prefix, 
                        split_node := JavaProjectPrefixTree.PackagePartNode(
                            word=longest_common_prefix, 
                            parent_node=self, 
                            dot_terminated=False
                        )
                    )
                    split_node.add_new_child(
                        preexisting_child_word[n:], b_node_type, 
                        dot_terminated=b_node.dot_terminated
                    )._move_children_map_from_other_node(b_node)

                elif b_node_type == JavaProjectPrefixTree.NodeType.FILE_PART:
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

                return split_node.add_new_child(new_child_word[n:], node_type, **kwargs)    

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
                        new_node.add_empty_package_part_child()

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
                if b_node_type == JavaProjectPrefixTree.NodeType.PACKAGE_PART and b_node.dot_terminated:
                    b_node.dot_terminated = False
                    b_node.add_empty_package_part_child()
                return b_node.add_new_child(suffix, node_type, kwargs)

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

    def add_node(self, fully_qualified_filename: str) -> None:
        word_parts = fully_qualified_filename.split(sep=".")    
        last_word_index = len(word_parts) - 1
        word_index, letter_index = 0, 0

        node = self.root

        while word_index <= last_word_index:
            word = word_parts[word_index]
            candidate_word, candidate_node = node._children_nodes_map.get(word[letter_index], ("", None))
            longest_common_prefix = find_longest_common_prefix_of_two_words(candidate_word, word[letter_index:])

            if longest_common_prefix == candidate_word:
                if (longest_common_prefix == word[letter_index:] and word_index != last_word_index and
                    not candidate_node.dot_terminated):
                    
                    candidate_node.add_empty_package_part_child()
                    word_index += 1
                    letter_index = 0
                else:
                    letter_index += len(longest_common_prefix)
                node = candidate_node    
            else:
                if word_index == last_word_index:
                    node_type = JavaProjectPrefixTree.NodeType.FILE_PART
                    new_node = node.add_new_child(word[letter_index:], node_type)        
                else:
                    node_type = JavaProjectPrefixTree.NodeType.PACKAGE_PART   
                    new_node = node.add_new_child(word[letter_index:], node_type, dot_terminated=True)

                node = new_node
                word_index += 1
                letter_index = 0

    def find_node_containing_prefix(self, word: str) -> "JavaProjectPrefixTree.Node":
        word_parts = word.split(sep=".")
        if word_parts[-1] == "":
            word_parts.pop(index=-1)

        last_word_index = len(word_parts) - 1
        word_index, letter_index = 0, 0

        node = self.root

        while word_index <= last_word_index:
            word = word_parts[word_index]
            candidate_word, candidate_node = node._children_nodes_map.get(word[letter_index], ("", None))
            if candidate_node is None:
                raise Exception(f"Word {word} is not stored in the data structure")
            
            longest_common_prefix = find_longest_common_prefix_of_two_words(candidate_word, word[letter_index:])
            n = len(longest_common_prefix)

            if n < len(candidate_word) and n < len(word):
                raise Exception(f"Word {word} is not stored in the data structure")
            
            letter_index += n
            if n == len(candidate_word):
                node = candidate_node
            if letter_index == len(word):    
                word_index += 1
                letter_index = 0

            if word_index == last_word_index and word[-1] == ".":
                if node.get_type_enum_value() == JavaProjectPrefixTree.NodeType.FILE_PART:
                    raise Exception(f"Word {word} is not stored in the data structure")
                elif not node.dot_terminated and JavaProjectPrefixTree.Node.EMPTY_KEY_MARKER in node._children_nodes_map:
                    node = node._children_nodes_map[JavaProjectPrefixTree.Node.EMPTY_KEY_MARKER][1]

        return node        

