if [[ $# -lt 1 ]]; then
    echo "This script requires at least one argument (relative test filepath)"
    exit 1
fi

arg=$1

if [[ $arg = "-h" || $arg = "--help" ]]; then
    echo """
This script is a wrapper which allows to run a python test file, 
passed as a relative filepath, as a file which is a part of a python
module. The script needs to be called from the same directory
where it is located (ie. root directory of the project).
The path cannot be preceeded with './'.
"""
fi

# The script is a relative path to a python file, so the .py file extension needs to be removed
path_with_ext_removed="$(echo $arg | tr '.' '\n' | head -n -1)"

module_path="$(echo $path_with_ext_removed | tr '/' '\.')"

python -m $module_path "${@:2}"
