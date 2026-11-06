# Conditional breakpoints:

### Creating a conditional breakpoint:

Creating a conditional breakpoint works similarly to creating a regular one, 
the only difference is the inclusion of the condition at the end of the statement.

```
Insert a regular breakpoint:

stop at org.company.project.module.SomeClass:<line_number>
stop at org.company.project.module.SomeClass.<method_name>

Insert a conditional breakpoint:

stop at org.company.project.module.SomeClass:<line_number> if <condition>
stop at org.company.project.module.SomeClass.<method_name> if <condition>
```

For example, suppose that while debugging Cassandra you want to insert a conditional breakpoint 
into the method `execute` of class `SelectStatement`, but you are only interested in how the method behaves
when functions are used. You could run such a command to run that point:

```
stop in org.apache.cassandra.cql3.statements.SelectStatement.execute if this.functions.size() > 0
```

or 

```
stop at org.apache.cassandra.cql3.statements.SelectStatement:372 if this.functions.size() > 0
```

### Inserting multiple conditional breakpoints on the same line:

When attempting to create more than one conditional breakpoint on the same line with different conditions
these conditions will be combined into a conjunctive statement:

```
stop in org.company.project.module.SomeClass.specificMethod if <condition_A>
stop in org.company.project.module.SomeClass.specificMethod if <condition_B>
```

is equivalent to: 

```
stop in org.company.project.module.SomeClass.specificMethod if (<condition_A> || <condition_B>)
```

### Removing a conditional breakpoint:

To remove a conditional breakpoint you need to begin your command with `clear conditional` instead of
`clear`, like in the case of a regular breakpoint.

```
clear conditional org.company.project.module.SomeClass:<line_number>
clear conditional org.company.project.module.SomeClass.<method_name>
```

For example, if you wanted to clean up the breakpoint set in the example above, such a command would have to be run:

```
clear conditional org.apache.cassandra.cql3.statements.SelectStatement.execute
```

### A regular and conditional breakpoints on the same line:

If a conditional and regular breakpoints are inserted on the same line, the regular one will always take precedence.