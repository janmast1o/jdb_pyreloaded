import sys
import os
import select
import termios
import tty

fd = sys.stdin.fileno()

print("fd =", fd)
print("isatty =", os.isatty(fd))
print("tty =", os.ttyname(fd))

original = termios.tcgetattr(fd)

print("Entering cbreak")

try:
    tty.setcbreak(fd)

    while True:
        ready, _, _ = select.select([fd], [], [], 0.1)

        if ready:
            data = os.read(fd, 1)

            print("READ:", repr(data))

            if data == b"q":
                break

finally:
    print("RESTORING")

    termios.tcsetattr(
        fd,
        termios.TCSANOW,
        original,
    )

    print("RESTORED")