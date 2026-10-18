from abc import ABC as AbstractClass, abstractmethod
from typing import Optional, Dict, Tuple, List
from typing_extensions import override
from enum import Enum

from src.utils.util_functions import find_longest_common_prefix_of_two_words


DEFAULT_EMPTY_MARKER = "<empty>"


def add_subtree_rooted_at_node_to_array_representation(node: "JavaProjectPrefixTree.Node",
                                                       destination_array: List[Tuple[int, "JavaProjectPrefixTree.Node"]], 
                                                       depth=0) -> None:
    destination_array.append((depth, node))
    child_edges = [l for l in node._children_nodes_map.keys()]
    child_edges.sort(key=lambda x: 0 if x == DEFAULT_EMPTY_MARKER else ord(x.lower()))

    for l in child_edges:
        child_node = node._children_nodes_map[l][1]
        add_subtree_rooted_at_node_to_array_representation(child_node, destination_array, depth+1)


# TODO: Add node/word removal support. 
# TODO: Decide if `Node` classes should be moved outside the class for clarity
class JavaProjectPrefixTree:

    class NodeType(Enum):
        PACKAGE_PART = 1
        FILE_PART = 2


    class Node(AbstractClass):
        EMPTY_KEY_MARKER = DEFAULT_EMPTY_MARKER
        
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

        @override
        def __eq__(self, other_object) -> bool:
            return self is other_object

        @abstractmethod
        def get_type_enum_value(self) -> "JavaProjectPrefixTree.NodeType":
            pass

        def _move_children_map_from_other_node(self, other_node: "JavaProjectPrefixTree.Node") -> None:
            self._children_nodes_map = other_node._children_nodes_map
            other_node._children_nodes_map = None
            for _, child_node in self._children_nodes_map.values():
                child_node.parent_node = self        

        def add_empty_package_part_child(self) -> "JavaProjectPrefixTree.PackagePartNode":
            self._children_nodes_map[self.EMPTY_KEY_MARKER] = ("", JavaProjectPrefixTree.PackagePartNode("", self, True))
            return self._children_nodes_map[self.EMPTY_KEY_MARKER][1]

        @abstractmethod
        def maybe_self_dot_terminate(self) -> "JavaProjectPrefixTree.PackagePartNode":
            pass

        # Handles splitting.
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
                else:
                    return child_node

            longest_common_prefix = find_longest_common_prefix_of_two_words(preexisting_child_word, new_child_word)
            n = len(longest_common_prefix)

            b_node = self._children_nodes_map[c][1]
            b_node_type = b_node.get_type_enum_value()

            if n < len(new_child_word) and n < len(preexisting_child_word): # Case (A)
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

            elif n < len(preexisting_child_word): # Case (B): longest_common_prefix == new_child_word
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

            elif n < len(new_child_word): # Case (C): longest_common_prefix == preexisting_child_word    
                suffix = new_child_word[n:]
                if b_node_type == JavaProjectPrefixTree.NodeType.PACKAGE_PART and b_node.dot_terminated:
                    b_node.dot_terminated = False
                    b_node.add_empty_package_part_child()
                return b_node.add_new_child(suffix, node_type, **kwargs)

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

        @override
        def maybe_self_dot_terminate(self) -> "JavaProjectPrefixTree.PackagePartNode":
            if self.dot_terminated:
                return self
            return self.add_empty_package_part_child()

        def __str__(self):
            parent_word: Optional[str] = "None"
            if self.parent_node is not None:
                parent_word = self.parent_node.word
                parent_word = parent_word if len(parent_word) > 0 else "<empty>"
            word = self.word if len(self.word) > 0 else "<empty>"
            return f"PPN: word={word}, parent={parent_word}, dot_terminated={self.dot_terminated}"

        def __repr__(self):
            return self.__str__()


    class FilePartNode(Node):
        def __init__(self, word: str, parent_node: Optional["JavaProjectPrefixTree.Node"]):
            super().__init__(word, parent_node)

        @override
        def get_type_enum_value(self) -> "JavaProjectPrefixTree.NodeType":
            return JavaProjectPrefixTree.NodeType.FILE_PART

        @override
        def maybe_self_dot_terminate(self) -> "JavaProjectPrefixTree.PackagePartNode":
            raise Exception("Cannot self dot-terminate on a file part node")

        def __str__(self):
            parent_word: Optional[str] = "None"
            if self.parent_node is not None:
                parent_word = self.parent_node.word
                parent_word = parent_word if len(parent_word) > 0 else "<empty>"
            word = self.word if len(self.word) > 0 else "<empty>"
            return f"FPN: word={word}, parent={parent_word}"

        def __repr__(self):
            return self.__str__()


    def __init__(self):
        self.root: "JavaProjectPrefixTree.PackagePartNode" = JavaProjectPrefixTree.PackagePartNode("", None, False)

    def add_node(self, fully_qualified_filename: str) -> None:
        word_parts = fully_qualified_filename.split(sep=".")
        if word_parts[-1] == "":
            word_parts.pop(-1)  
        last_word_index = len(word_parts) - 1
        node = self.root

        for word_index in range(0, last_word_index+1):
            word = word_parts[word_index]
            candidate_word, candidate_node = node._children_nodes_map.get(word[0], ("", None))
            # Based on an assumption that the file names start with upper case.
            is_current_word_file_part = (word_index == last_word_index) and (word[0] == word[0].upper())

            if candidate_node is None:
                new_node: JavaProjectPrefixTree.Node = None
                if is_current_word_file_part:
                    new_node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.FILE_PART)
                else:
                    new_node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True)

                node = new_node
                continue

            longest_common_prefix = find_longest_common_prefix_of_two_words(candidate_word, word)
            if longest_common_prefix == word:
                # If the longest common prefix is equal to both `word_suffix` and `candidate_word`
                # then we only need to maybe add dot termination (if we are inserting a package word)
                if longest_common_prefix == candidate_word:
                    node = candidate_node
                    if not is_current_word_file_part:
                        node = candidate_node.maybe_self_dot_terminate()
                else:
                    # Since nodes can handle splitting on their own, and this would be 
                    # case (B) in `Node.add_new_child` logic we can just use that method.
                    if is_current_word_file_part:
                        node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.FILE_PART)
                    else:
                        node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True)
            else: # This will be either case (A) or case (C)
                if is_current_word_file_part:
                    node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.FILE_PART)
                else:
                    node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True) 

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

    def get_list_representation(self) -> List[Tuple[int, "JavaProjectPrefixTree.Node"]]:
        destination_array: List[Tuple[int, JavaProjectPrefixTree.Node]] = []
        add_subtree_rooted_at_node_to_array_representation(self.root, destination_array, 0)
        return destination_array

    def clear_tree(self) -> None:
        self.root._children_nodes_map.clear()
        self.root.word = ""

