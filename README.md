# jdb_pyreloaded
A wrapper around jdb implemented in python, supporting autocompletion and conditional breakpoints among others.

### Requirements:

- python (guaranteed to work with >=3.11.0, might work on older versions, not tested)
- pip packages listed in `requirements.txt`

### Usage: 

To run the JDB Pyreloaded run this command in the terminal:

```bash
python -m src.run_jdb_debugger_wrapper --jvm_address=<ip_address>:<port>
```

For example if one wants to debug a local java process which exposes debug port 5005: 

```bash
python -m src.run_jdb_debugger_wrapper --jvm_address=127.0.0.1:5005
```
