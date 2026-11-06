import os

from typing import Optional, List

from src.data_structures.java_project_prefix_tree import JavaProjectPrefixTree


def maybe_translate_env_variables(file_path: str) -> str:
    if "$" not in file_path:
        return file_path

    file_path_separator = os.path.sep
    file_path_elements: List[str] = []
    n = len(file_path)
    i = 0
    while i < n:
        if file_path[i] == "$":
            i += 1
            env_var_name_chars: List[str] = []
            if file_path[i] == "{":
                i += 1
                while file_path[i] != "}":
                    env_var_name_chars.append(file_path[i])
                    i += 1
                i += 1    
            else:
                while file_path[i] != file_path_separator:
                    env_var_name_chars.append(file_path[i])
                    i += 1
            env_var_name = "".join(env_var_name_chars)
            evaluated_env_var = os.getenv(env_var_name)
            if evaluated_env_var is None:
                raise Exception(f"No env var with name: {env_var_name} exists")
            evaluated_env_var = evaluated_env_var.rstrip("/")
            file_path_elements.append(evaluated_env_var)
        else:
            file_path_elements.append(file_path[i])
            i += 1

    return "".join(file_path_elements)


def explore_local_directory_and_add_files_to_project_tree(project_tree: JavaProjectPrefixTree, local_dir_path: str, non_module_prefix_length: int) -> None:
    # print(f"Exploring directory: {local_dir_path}...")
    dir_contents = os.listdir(local_dir_path)
    for entry in dir_contents:
        if os.path.isdir(os.path.join(local_dir_path, entry)):
            explore_local_directory_and_add_files_to_project_tree(project_tree, os.path.join(local_dir_path, entry), non_module_prefix_length)
        elif entry.endswith(".java"):
            fully_qualified_java_filename = os.path.join(local_dir_path, entry).rstrip(".java").replace(os.path.sep, ".")
            fully_qualified_java_filename = fully_qualified_java_filename[non_module_prefix_length:]
            project_tree.add_node(fully_qualified_java_filename)


# PYJDB target list has to be either supplied or file `target.pyjdb` has to exist in the
# root of the project pointed to by `project_path`.
# NOTE: If both conditions are satisfied the list passed as an argument takes precedence.
def build_project_prefix_tree_for_local_java_project(project_path: str, optional_pyjdb_target_list: Optional[List[str]]) -> JavaProjectPrefixTree:
    project_path = maybe_translate_env_variables(project_path)

    pyjdb_target_list: List[str] = None
    if optional_pyjdb_target_list is not None:
        pyjdb_target_list = optional_pyjdb_target_list
    if pyjdb_target_list is None:
        pyjdb_target_file_exists = os.path.exists(os.path.join(project_path, "target.pyjdb"))
        if not pyjdb_target_file_exists:
            raise Exception(f"Cannot construct project prefix tree for Java project due to being unable to determine the target list")
        
        with open(os.path.join(project_path, "target.pyjdb"), "r") as jdb_target_file:
            pyjdb_target_list = jdb_target_file.readlines()
            n = len(pyjdb_target_list)
            for i in range(n):
                pyjdb_target_list[i] = pyjdb_target_list[i].strip()

    project_tree = JavaProjectPrefixTree()
    for target_dir in pyjdb_target_list:
        absolute_target_dir = os.path.join(project_path, target_dir)
        absolute_target_dir_length = len(absolute_target_dir)
        if not absolute_target_dir.endswith(os.path.sep):
            absolute_target_dir_length += 1
        explore_local_directory_and_add_files_to_project_tree(project_tree, absolute_target_dir, absolute_target_dir_length)

    return project_tree    

