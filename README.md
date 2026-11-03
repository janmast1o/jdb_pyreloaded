# JDB Pyreloaded:

A wrapper around jdb implemented in python, supporting autocompletion and conditional breakpoints among others.

## Requirements:

- python (guaranteed to work with `>= 3.11.0`, might work on older versions, not tested)
- pip packages listed in `requirements.txt`
- unix operating system or a unix virtual machine

## Usage:

### Pre-requisites:

- ensure that your terminal has `onlcr` on (to check that you ran this command `stty -a | tr ' ' '\n' | grep onlcr` and verify that the output is `onlcr` and not `-onlcr`)

### Running the program:

To run the JDB Pyreloaded run this command in the terminal:

```bash
python -m src.run_jdb_debugger_wrapper --jvm_address=<ip_address>:<port>
```

For example if one wants to debug a local java process which exposes debug port 5005: 

```bash
python -m src.run_jdb_debugger_wrapper --jvm_address=127.0.0.1:5005
```

## Why use this project:

The goal of this project was to develop a tool which would be more convenient and efficient to use than JDB that comes with Java by default.

This section will describe what has been done to improve on the experience of using vanilla JDB.

### Arrow keys support:

JDB does not support using left/right arrow keys to move cursor when writing a command or up/down arrow keys to inspect previously inputted commands (at least for older Java versions).
Instead of the above mentioned actions being performed one of `^[[A`, `^[[B`, `^[[C`, `^[[D` is appended to the end of the command, which admittedly is not particularly useful most of the time.

This issue has been solved by building the interactable layer of the project on `prompt_toolkit` which supplies desired functionality out of the box.

### Conditional breakpoints:

When debugging we often only care about the state of the process if some specific conditions are met. Regular breakpoints do not accommodate such scenarios particularly well.

Suppose you want to debug such a piece of code:

```java
100   public void processUpdateRequest(InsertionRequest request) {
101       registerNewActivelyExecutedRequest(request, RequestType.UPDATE);
102       <update request logic>
103   }
```

The system starts to behave incorrectly after a certain threshold (for example 25) of update requests being concurrently executed is reached. 
Normally one would have to add a breakpoint in `processUpdateRequests` and instantly resume execution with `cont` upon hitting that breakpoint, until
they finally hit it when the condition (at least 25 update requests being executed concurrently) happens to be met.

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



