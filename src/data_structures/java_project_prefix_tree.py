from abc import ABC as AbstractClass, abstractmethod
from typing import Optional, Dict, Tuple, List, Union
from typing_extensions import override, overload
from enum import Enum

from src.utils.custom_exceptions import SequenceNotStoredInPrefixTreeException
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

        def get_full_sequence_from_the_root(self) -> str:
            predecessor_words: List[str] = [self.word]
            predecessor = self.parent_node
            while predecessor is not None:
                w = predecessor.word
                if getattr(predecessor, "dot_terminated", False):
                    w = w + "."
                predecessor_words.append(w)
                predecessor = predecessor.parent_node

            predecessor_words.reverse()
            return "".join(predecessor_words)   

        def _move_children_map_from_other_node(self, other_node: "JavaProjectPrefixTree.Node") -> None:
            self._children_nodes_map = other_node._children_nodes_map
            other_node._children_nodes_map = None
            for _, child_node in self._children_nodes_map.values():
                child_node.parent_node = self
            other_node._children_nodes_map = {}    

        def _try_get_empty_package_part_dot_terminated_child(self) -> Optional["JavaProjectPrefixTree.PackagePartNode"]:
            return self._children_nodes_map.get(JavaProjectPrefixTree.Node.EMPTY_KEY_MARKER, ("", None))[1]

        def add_empty_package_part_dot_terminated_child(self) -> "JavaProjectPrefixTree.PackagePartNode":
            self._children_nodes_map[self.EMPTY_KEY_MARKER] = ("", JavaProjectPrefixTree.PackagePartNode("", self, True))
            return self._children_nodes_map[self.EMPTY_KEY_MARKER][1]

        def is_an_empty_package_part_dot_terminated_node(self) -> bool:
            if (self.get_type_enum_value() == JavaProjectPrefixTree.NodeType.PACKAGE_PART and self.word == "" and
                self.parent_node is not None and self is self.parent_node._children_nodes_map.get(self.EMPTY_KEY_MARKER, ("", None))[1]):
                return True

            return False    

        @abstractmethod
        def maybe_self_dot_terminate(self) -> "JavaProjectPrefixTree.PackagePartNode":
            pass

        @abstractmethod
        def try_push_down_dot_termination(self) -> "JavaProjectPrefixTree.PackagePartNode":
            pass

        # Handles splitting.
        def add_new_child(self, new_child_word: str, node_type: "JavaProjectPrefixTree.NodeType", **kwargs) -> "JavaProjectPrefixTree.Node":
            if len(new_child_word) == 0:
                raise Exception("Cannot append a file part child node with an empty associated word")
            
            # Get the first character of the new word
            c = new_child_word[0]
            if c in self._children_nodes_map:
                raise Exception(f"Cannot add new child for word {new_child_word}, as {self._children_nodes_map[c][1]} already preexists")

            if node_type == JavaProjectPrefixTree.NodeType.PACKAGE_PART:
                if "dot_terminated" not in kwargs:
                    raise Exception(f"Invalid new child insertion call - package part always has to have the flag 'dot_terminated'")
                self._children_nodes_map[c] = (new_child_word, JavaProjectPrefixTree.PackagePartNode(new_child_word, self, kwargs["dot_terminated"]))
            else:
                self._children_nodes_map[c] = (new_child_word, JavaProjectPrefixTree.FilePartNode(new_child_word, self))

            return self._children_nodes_map[c][1]

        # Returns the prefix node (self) and the suffix node (newly created one).
        # Prefix word is described with an interval `[0, split_index]`, the suffix node `[split_index+1, len(word))`
        def split_node(self, split_index: int) -> Tuple["JavaProjectPrefixTree.Node", "JavaProjectPrefixTree.Node"]:
            word_prefix, word_suffix = self.word[:split_index+1], self.word[split_index+1:]
            self.word = word_prefix
            if self.parent_node is not None:
                self.parent_node._children_nodes_map[word_prefix[0]] = (word_prefix, self)

            suffix_child_node: JavaProjectPrefixTree.Node = None
            if self.get_type_enum_value() == JavaProjectPrefixTree.NodeType.PACKAGE_PART:
                suffix_child_node = JavaProjectPrefixTree.PackagePartNode(word_suffix, self, dot_terminated=getattr(self, "dot_terminated"))
                setattr(self, "dot_terminated", False)
            else:
                suffix_child_node = JavaProjectPrefixTree.FilePartNode(word_suffix, self)

            suffix_child_node._move_children_map_from_other_node(self)
            self._children_nodes_map[word_suffix[0]] = (word_suffix, suffix_child_node)

            return self, suffix_child_node         


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
            return self.add_empty_package_part_dot_terminated_child()

        @override
        def try_push_down_dot_termination(self) -> "JavaProjectPrefixTree.PackagePartNode":
            if not self.dot_terminated:
                raise Exception("Cannot push down dot-termination as the node is not dot-terminated")
            self.dot_terminated = False
            dot_terminated_child = JavaProjectPrefixTree.PackagePartNode("", self, True)
            dot_terminated_child._move_children_map_from_other_node(self)
            self._children_nodes_map[self.EMPTY_KEY_MARKER] = ("", dot_terminated_child)
            return dot_terminated_child

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

        @override
        def try_push_down_dot_termination(self) -> "JavaProjectPrefixTree.PackagePartNode":
            raise Exception("Cannot push down dot-termination on a file part node")

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

    # Returns a tuple:
    #   - first, `Node`: returns the node which marks the end of the longest common prefix
    #   - second: the index of the word `w` in `fully_qualified_word` where the longest common prefix ends
    #   - third: the letter index `l_i` of `w` where the longest common prefix ends
    #   - fourth: True if the end of the longest common prefix is '.' (dot marking the end of the package name).
    #             This value is only useful if `len(w) - 1 == l_i`, otherwise should be discarded, as anything may be returned (including `None`).
    # Does not mutate the input as a side effect.
    # Returning 0 and -1 as the second and third values respectively means that the prefix does not exist in the tree.
    @overload
    def find_longest_common_prefix_with_word(self, fully_qualified_word: str) -> Tuple["JavaProjectPrefixTree.Node", int, int, bool]:
        pass

    @overload
    def find_longest_common_prefix_with_word(self, words: List[str]) -> Tuple["JavaProjectPrefixTree.Node", int, int, bool]:
        pass

    def find_longest_common_prefix_with_word(self, word: Union[str, List[str]]) -> Tuple["JavaProjectPrefixTree.Node", int, int, bool]:
        words: List[str] = None
        full_word_dot_terminated: bool = False
        if isinstance(word, str):
            words = word.split(sep=".")
            if word.endswith("."):
                full_word_dot_terminated = True
                words.pop(-1)
        elif isinstance(word, list):
            words = word
            if words[-1] == "":
                full_word_dot_terminated = True
                # Creating new array instead of modifying, as we do not want to mutate the input.
                words = words[:-1]

        if len(words) == 1 and words[0] == "": # ie. word == ""
            return self.root, 0, -1, True    
        elif len(words) > 1 and ("" in words): # at least two consecutive dots or word == "." 
            return SequenceNotStoredInPrefixTreeException("Malformed input")

        node = self.root
        word_index, letter_index = 0, 0
        last_word_index = len(words)-1

        while word_index <= last_word_index:
            word = words[word_index]
            candidate_word, candidate_node = node._children_nodes_map.get(word[letter_index], ("", None))
            # Enforcing type hinting in editor.
            candidate_word: str = candidate_word
            candidate_node: JavaProjectPrefixTree.Node = candidate_node

            if candidate_node is None:
                # The longest common prefix of the word and the tree is empty.
                # It doesn't really matter what we return as the fourth value.
                if word_index == 0 and letter_index == 0:
                    return self.root, 0, -1, False
                # Since we moved onto the subsequent word, we must have found a full match for the package name.
                elif letter_index == 0:
                    previous_word_index = word_index-1
                    previous_word = words[previous_word_index]
                    return node, previous_word_index, len(previous_word)-1, True
                else:
                    return node, word_index, letter_index-1, False

            word_suffix = word[letter_index:]
            longest_common_prefix = find_longest_common_prefix_of_two_words(word_suffix, candidate_word)
            is_package_part_node = (word_index < last_word_index) or (word[0] == word[0].lower())

            if len(longest_common_prefix) == len(word_suffix): # ie. `longest_common_prefix == w_suffix`    
                # Case (1)
                if len(longest_common_prefix) == len(candidate_word): # the same reworded condition as above, will not write this every time
                    node = candidate_node
                    if is_package_part_node and (not getattr(node, "dot_terminated", False)):
                        dot_terminated_node = node._try_get_empty_package_part_dot_terminated_child()
                        if dot_terminated_node is not None:
                            node = dot_terminated_node
                        else:
                            # We matched the full node word, but that node is neither dot terminated nor has a dot terminated child,
                            # so we have to signify with the last item in the returned value that we did not get
                            # a package match.
                            return node, word_index, len(word)-1, False
                    word_index += 1
                    letter_index = 0
                # Case (2)
                else:
                    # This is the end of the match: the match could only be longer
                    # if the word in the tree was dot-terminated here, but since the word
                    # stored in the node is longer than `word_suffix` that cannot happen.
                    return candidate_node, word_index, len(word)-1, False
            else: # ie. `len(longest_common_prefix) < len(word_suffix)`
                letter_index += len(longest_common_prefix)
                node = candidate_node
                # Case (3)
                if len(longest_common_prefix) == len(candidate_word):
                    if is_package_part_node and getattr(node, "dot_terminated", False):
                        # For there to be a longer prefix we would need for there to be words
                        # longer than already found, which is impossible if the node is dot-terminated.
                        return node, word_index, letter_index-1, False
                    # If the node is not dot-terminated it is impossible that we will find a longer match so we continue.
                # Case (4)
                else:
                    # This one should be pretty self-explanatory.
                    return node, word_index, letter_index-1, False

        # We should only really reach the point if correctly match the whole word.
        if (words[-1][0] == words[-1][0].lower()): # The last one was package part, not file part.
            node_dot_terminated = getattr(node, "dot_terminated", False)
            if (not full_word_dot_terminated) and node_dot_terminated and node.is_an_empty_package_part_dot_terminated_node():
                node = node.parent_node
                node_dot_terminated = False
            return node, last_word_index, len(words[-1])-1, node_dot_terminated

        # The last one was file part, so we don't care about the last returned value.
        return node, last_word_index, len(words[-1]), None      

    def find_node_containing_prefix(self, fully_qualified_word: str) -> "JavaProjectPrefixTree.Node":
        words = fully_qualified_word.split(sep=".")
        node, word_index, letter_index, _ = self.find_longest_common_prefix_with_word(words)

        if word_index == len(words)-1 and letter_index == len(words[-1])-1:
            return node
        else:
            raise SequenceNotStoredInPrefixTreeException(f"{fully_qualified_word} not stored in the tree")

    # This implementation is extremely chaotic (but it seems to work), I'm considering just rewriting
    # the implementation of `find_longest_common_prefix_with_word` and appropriating it
    # for insertions.
    def add_node(self, fully_qualified_filename: str) -> None:
        words = fully_qualified_filename.split(sep=".")
        last_word_index = len(words)-1
        # LCP - short for 'longest common prefix'
        node, lcp_word_index, lcp_letter_index, package_part_matched = self.find_longest_common_prefix_with_word(words)

        # Empty prefix with the tree.
        if lcp_word_index == 0 and lcp_letter_index == -1:
            node = self.root
            for i in range(last_word_index+1):
                word = words[i]
                is_file_part = (i == last_word_index) and (word[0] == word[0].upper())
                if is_file_part:
                    node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.FILE_PART)
                else:
                    node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True)
            return

        last_lcp_word = words[lcp_word_index]
        last_lcp_word_suffix = last_lcp_word[lcp_letter_index+1:]
        if package_part_matched:
            # Sanity check assertion
            if lcp_letter_index != len(last_lcp_word)-1:
                raise Exception("Possible implementation error in JavaProjectPrefixTree::find_longest_common_prefix_with_tree")
            for i in range(lcp_word_index+1, last_word_index+1):
                word = words[i]
                is_file_part = i == last_word_index and (word[0] == word[0].upper())
                if is_file_part:
                    node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.FILE_PART)
                else:
                    node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True)
            return            

        found_prefix = ".".join(words[:lcp_word_index]) + "." + last_lcp_word[:lcp_letter_index+1]
        found_prefix = found_prefix.lstrip(".")
        node_full_sequence = node.get_full_sequence_from_the_root()
        is_last_lcp_word_file_part = (lcp_word_index == last_word_index) and (last_lcp_word[0] == last_lcp_word[0].upper())

        if found_prefix == node_full_sequence:
            if lcp_letter_index < len(last_lcp_word)-1:
                if not is_last_lcp_word_file_part and getattr(node, "dot_terminated", False):
                    node.try_push_down_dot_termination()
                if is_last_lcp_word_file_part:
                    node = node.add_new_child(last_lcp_word_suffix, JavaProjectPrefixTree.NodeType.FILE_PART)
                else:
                    node = node.add_new_child(last_lcp_word_suffix, JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True)
            elif not is_last_lcp_word_file_part: # and by inference `... and lcp_letter_index == len(last_lcp_word)-1`
                # We did not get package part matched, so we need to manually dot-terminate the node.
                node = node.maybe_self_dot_terminate()
        else:
            length_difference = len(node_full_sequence) - len(found_prefix)
            if length_difference == 1 and node_full_sequence[-1] == ".": # and by inference `... and node.dot_terminated`
                node.try_push_down_dot_termination()    
            else:
                node_full_sequence = node_full_sequence.rstrip(".")
                length_difference = len(node_full_sequence) - len(found_prefix)
                prefix_node, _ = node.split_node(len(node.word) - length_difference - 1)
                node = prefix_node
                if not is_last_lcp_word_file_part and lcp_letter_index == len(last_lcp_word)-1:
                    node = node.add_empty_package_part_dot_terminated_child()
            
            if lcp_letter_index < len(last_lcp_word)-1:
                if is_last_lcp_word_file_part:
                    node = prefix_node.add_new_child(last_lcp_word_suffix, JavaProjectPrefixTree.NodeType.FILE_PART)
                else:
                    node = prefix_node.add_new_child(last_lcp_word_suffix, JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True)

        for i in range(lcp_word_index+1, last_word_index+1):
            word = words[i]
            is_file_part = i == last_word_index and (word[0] == word[0].upper())
            if is_file_part:
                node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.FILE_PART)
            else:
                node = node.add_new_child(word, JavaProjectPrefixTree.NodeType.PACKAGE_PART, dot_terminated=True)

    def get_list_representation(self) -> List[Tuple[int, "JavaProjectPrefixTree.Node"]]:
        destination_array: List[Tuple[int, JavaProjectPrefixTree.Node]] = []
        add_subtree_rooted_at_node_to_array_representation(self.root, destination_array, 0)
        return destination_array

    def clear_tree(self) -> None:
        self.root._children_nodes_map.clear()
        self.root.word = ""

