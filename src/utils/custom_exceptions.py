class ShellProcessWrapperInterruptException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class CommandMalformedException(Exception):
    def __init__(self, *args):
        super().__init__(*args)