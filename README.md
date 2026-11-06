# JDB Pyreloaded:

A wrapper around jdb implemented in python, supporting autocompletion and conditional breakpoints, among other features.

## Requirements:

- python (guaranteed to work with `>= 3.11.0`, might work on older versions, not tested)
- pip packages listed in `requirements.txt`
- unix operating system or a unix virtual machine

## Usage:

### Pre-requisites:

- ensure that your terminal has `onlcr` on (to check that you can run this command `stty -a | tr ' ' '\n' | grep onlcr` and verify that the output is `onlcr` and not `-onlcr`)

### Running the program:

To run the JDB Pyreloaded run this command in the terminal:

```bash
python -m src.run_jdb_debugger_wrapper --jvm_address=<ip_address>:<port>
```

For example if one wants to debug a local Java process which exposes debug port 5005: 

```bash
python -m src.run_jdb_debugger_wrapper --jvm_address=127.0.0.1:5005
```

To find out more about configurable flags of this program call, run: 

```bash
python -m src.run_jdb_debugger_wrapper --help
```

## Why use this project:

The goal of this project was to develop a tool which would be more convenient and efficient to use than JDB that comes with Java by default.

This section will describe what has been done to improve on the experience of using vanilla JDB.

### Arrow keys support:

Most terminal apps support using left/right arrow keys to move the cursor when writing the command and up/down arrow keys to inspect previously executed commands.
This is not the case for JDB (at least for older Java releases).
Instead of the above mentioned actions being performed one of `^[[A`, `^[[B`, `^[[C`, `^[[D` is appended to the end of the command.

This issue has been solved by building the interactable layer of the project on `prompt_toolkit` which supplies desired functionality out of the box.

### Conditional breakpoints:

When debugging we often only care about the state of the process if some specific conditions are met. Regular breakpoints do not accommodate such scenarios particularly well.

Suppose you want to debug a following piece of code:

```java
100   public void processUpdateRequest(UpdateRequest request) {
101       registerNewActivelyExecutedRequest(request, RequestType.UPDATE);
102       <update request logic>
103   }
```

The system starts to behave incorrectly after a certain threshold (for example 25) of update requests being concurrently executed is reached. 
Normally you would have to add a breakpoint in `processUpdateRequest` and instantly resume execution with `cont` upon hitting that breakpoint, until
you finally hit it when the condition (at least 25 update requests being executed concurrently) happens to be met.

JDB Pyreloaded enables the user to achieve this in a more convenient manner by setting a conditional breakpoint:

```jdb
stop at org.company.project.requests.processing.UpdateRequestProcessor:102 if (this.getActivelyExecutedUpdateRequestsCount() > 25)
```

This way JDB will actually only stop if the disclosed condition is met.

To find out more about how to use conditional breakpoints refer to [the conditional breakpoint manuals](manuals/conditional_breakpoints.md).

### Autocomplete for fully qualified class names:

One of the most inconvenient things about vanilla JDB is having to manually type fully qualified class names where breakpoints are meant to be inserted. 
It is not uncommon to have to type something as long as `org.company.project.auth.AuthenticationEvent` by hand if we want to insert a breakpoint in that
class or read its static field. 

To combat this tedium autocompletion for fully qualified has been introduced. When writing a fully qualified class name simply press `Tab` to perform
autocompletion and speed up typing. 

The autocompletion has been made to behave similarly to filesystem traversal autocompletion embedded in most modern day unix terminals.

To enable autocompletion in a JDB Pyreloaded session absolute filepath has to be supplied when running the command:

```bash
python -m src.run_jdb_debugger_wrapper --jvm_address=<ip_address>:<port> --local_project_path=<absolute_filepath_to_the_project_root>
```

For example if one is debugging a local Cassandra process, which exposes 5005 debug port, with the repository cloned at `home/ubuntu/OpenSourceProjects/cassandra`, the command would look as follows:

```bash
python -m src.run_jdb_debugger_wrapper --jvm_address=127.0.0.1:5005 --local_project_path=/home/ubuntu/OpenSourceProjects/cassandra
```

For autocomplete to work correctly a JDB Pyreloaded target list has to be specified for the project. Target directories in that list indicate where Java packages storing code are.
For example, for Cassandra (please refer to the [Cassandra github repository](https://github.com/apache/cassandra)) the target list would be as follows:

```
src/java
test/unit
```

One can notice that these directories directly store Java packages.

There are two ways of specifying JDB Pyreloaded target list. Firstly, it can be passed a script argument: 

```bash
python -m src.run_jdb_debugger_wrapper --jvm_address=<ip_address>:<port> --local_project_path=<absolute_filepath_to_the_project_root> --pyjdb_target_list=<list_of_directories_storing_java_packages>
```

To stick with the Cassandra example, the command would be as follows: 

```bash
python -m src.run_jdb_debugger_wrapper --jvm_address=127.0.0.1:5005 --local_project_path=/home/ubuntu/OpenSourceProjects/cassandra --pyjdb_target_list=src/java,test/unit
```

The other way of specifying the target list is to create a `target.pyjdb` file in the debugged project and paste the contents target list there.
In the example above one would create a file `/home/ubuntu/OpenSourceProjects/cassandra/target.pyjdb` and then paste following contents:

```
src/java
test/unit
```

After doing that JDB Pyreloaded with autocompletion can be run with such a command (`target.pyjdb` will be found in the project path and read it automatically): 

```bash
python -m src.run_jdb_debugger_wrapper --jvm_address=127.0.0.1:5005 --local_project_path=/home/ubuntu/OpenSourceProjects/cassandra
```

Do note that autocompletion for fully qualified class names is currently only supported for local processes. 
Should there be demand for it, the prospect of adding autocompletion support for remote processes shall be explored.
