from .daemon import *

# Factorio exe on Windows seems always call AttachConsole(ATTACH_PARENT_PROCESS) to reset
# the StdHandle, so we have to start a child process without a console and start Factorio
# as the grandchild process. The child process can be another python with redirected stream,
# or simply cmd /C.
#
# Implementation 1: (easy, currently using)
# self.process = await asyncio.create_subprocess_exec(_cmd_path(), '/C', self.executable, *args, **kwargs)
#
# Implementation 2: (can be more flexible)
# self.process = await asyncio.create_subprocess_exec(
#     sys.executable, '-c',
#     f"import subprocess, sys\n"
#     f"p=subprocess.run({[self.executable, *args]}, "
#     f"  stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)\n"
#     f"exit(p.returncode)",
#     **kwargs
# )
