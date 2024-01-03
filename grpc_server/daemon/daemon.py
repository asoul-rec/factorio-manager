import glob
import logging
import os
import asyncio
import subprocess
import sys
# import subprocess
from collections import namedtuple, deque, defaultdict
from dataclasses import dataclass
# import logging
from typing import Optional, TypedDict, Literal
from signal import SIGINT

from .monitor import AsyncStreamMonitor

__all__ = [
    'SUCCESS', 'STARTING', 'STOPPING', 'SATISFIED', 'BAD_ARG', 'EXIT_ERROR', 'EXIT_UNEXPECT',
    'Status', 'FactorioServerDaemon'
]

SUCCESS = 0
STARTING = 1
STOPPING = 2

SATISFIED = 101
BAD_ARG = 102
EXIT_ERROR = 103
EXIT_UNEXPECT = 104


class Status(TypedDict):
    code: int
    message: Optional[str]


def _cmd_path():
    # Windows-only, copied from python standard library subprocess.py
    _comspec = os.environ.get('ComSpec')
    if not _comspec:
        _system_root = os.environ.get('SystemRoot', '')
        _comspec = os.path.join(_system_root, 'System32', 'cmd.exe')
        if not os.path.isabs(_comspec):
            raise FileNotFoundError('shell not found: neither %ComSpec% nor %SystemRoot% is set')
    return _comspec


class FactorioServerDaemon:
    @dataclass
    class Info:
        args: Optional[list[str]] = None
        daemon: Optional[asyncio.Task] = None
        error: Optional[Status] = None
        # reset = super().__init__  # method

    _process_info: Info
    process: Optional[asyncio.subprocess.Process] = None
    _monitor: dict[Literal['stdout', 'stderr'], AsyncStreamMonitor]

    def __init__(self, executable, timeout=10, logs_maxlen=None):
        self._process_info = self.Info()
        self.executable = executable
        self.global_timeout = timeout
        self._monitor = {
            stream_name: AsyncStreamMonitor(
                history_maxlen=logs_maxlen,
                logger_callback=lambda s, _predix=f"factorio {stream_name}: ": logging.debug(_predix + str(s))
            )
            for stream_name in ['stdout', 'stderr']
        }

    async def _daemon(self, args):
        # start
        self._process_info.error = {"code": STARTING, "message": "The server is starting but not ready yet."}
        kwargs = {'stdin':  asyncio.subprocess.PIPE,
                  'stdout': asyncio.subprocess.PIPE,
                  'stderr': asyncio.subprocess.PIPE}
        try:
            if os.name == 'nt':
                logging.info("starting the server with detached cmd wrapper")
                # Factorio exe on Windows seems always call AttachConsole(ATTACH_PARENT_PROCESS) to reset
                # the StdHandle, so we have to start a child process without a console and start Factorio
                # as the grandchild process. The child process can be another python with redirected stream,
                # or simply cmd /C.
                kwargs["creationflags"] = subprocess.DETACHED_PROCESS
                # self.process = await asyncio.create_subprocess_exec(
                #     sys.executable, '-c',
                #     f"import subprocess, sys\n"
                #     f"p=subprocess.run({[self.executable, *args]}, "
                #     f"  stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)\n"
                #     f"exit(p.returncode)",
                #     **kwargs
                # )
                self.process = await asyncio.create_subprocess_exec(_cmd_path(), '/C', self.executable, *args, **kwargs)
            else:
                logging.info("starting the server as subprocess")
                self.process = await asyncio.create_subprocess_exec(self.executable, *args, **kwargs)

            # self.process = await asyncio.create_subprocess_exec(self.executable, *args, **kwargs)
        except OSError as e:
            self._process_info.error = {"code": BAD_ARG, "message": f"Cannot start server. {type(e).__name__}: {e}"}
            return

        self._process_info.error = None
        self._monitor['stdout'].stream = self.process.stdout
        self._monitor['stderr'].stream = self.process.stderr
        # running
        try:
            await self.process.wait()
            await self._monitor['stdout'].wait_eof()
            await self._monitor['stderr'].wait_eof()
        except asyncio.CancelledError:
            self.process.kill()
        finally:
            if self.process.returncode is None:
                self.process.kill()

        stdout = self._stream_history('stdout', 128)
        stderr = self._stream_history('stderr', 128)
        out_streams = f'{stdout=!s}, {stderr=!s}'
        # exit
        if exit_code := self.process.returncode:
            self._process_info.error = {
                "code":    EXIT_ERROR,
                "message": f"The server finished with {exit_code=}, " + out_streams
            }
            logging.warning(f"the server exited with error {exit_code=}, " + out_streams)
        else:
            self._process_info.error = {
                "code":    EXIT_UNEXPECT,
                "message": f"The server exited unexpectedly without error, " + out_streams}
            logging.info(f"the server exited normally, " + out_streams)
        self.process = None

    async def start(self, args) -> Status:
        if self.process:
            if (error := self._process_info.error) is not None:
                return error
            return {"code": SATISFIED, "message": "The server is already running."}
        self._process_info.args = args
        self._process_info.error = None
        if self._process_info.daemon is not None:
            self._process_info.daemon.cancel()
        self._process_info.daemon = asyncio.create_task(self._daemon(args))
        self._monitor['stdout'].stream = None  # clear the old stream to monitor the keyword correctly
        wait_in_game = asyncio.create_task(
            self._monitor['stdout'].wait_for(b'changing state from(CreatingGame) to(InGame)')
        )
        done, pending = await asyncio.wait(
            [wait_in_game, self._process_info.daemon],
            timeout=self.global_timeout, return_when=asyncio.FIRST_COMPLETED
        )
        if wait_in_game in done:
            return {"code": SUCCESS, "message": None}
        wait_in_game.cancel()
        if not done:
            self._process_info.daemon.cancel()
            return {"code": EXIT_ERROR, "message": f"Starting is aborted after {self.global_timeout}s"}
        if (error := self._process_info.error) is not None:
            self._process_info.error = None
            return error
        return {"code": EXIT_UNEXPECT, "message": "The daemon exit unexpectedly without setting an error"}

    async def stop(self) -> Status:
        if not self.process or self.process.returncode:  # do nothing if stopped
            if (error := self._process_info.error) is not None:
                return error
            return {"code": SATISFIED, "message": "The server is already stopped."}
        # exit gracefully with saving
        if os.name == 'nt':
            logging.info("stopping the server by /quit command")
            self.process.stdin.write(b"/quit\r\n")
            self.process.stdin.write_eof()
        else:
            logging.info("stopping the server by signal.SIGINT")
            self.process.send_signal(SIGINT)
        # wait_closed = asyncio.create_task(
        #     self._monitor['stdout'].wait_for(b'changing state from(Disconnected) to(Closed)')
        # )
        await asyncio.wait([self._process_info.daemon], timeout=self.global_timeout)
        self._process_info.error = None
        if not self._process_info.daemon.done():
            self._process_info.daemon.cancel()
            return {"code": EXIT_ERROR, "message": f"Force stop after {self.global_timeout}s"}
        return {"code": SUCCESS, "message": None}

    def _reset(self):
        self._process_info.__init__()

    async def restart(self, args=None) -> Status:
        # Factorio doesn't allow running multiple instances simultaneously, so we must wait until the old process
        # is fully stopped before starting a new one
        old_args = self._process_info.args
        stop_status = await self.stop()
        if (stop_code := stop_status["code"]) and (stop_code != SATISFIED):
            stop_status["message"] = "Encountered an error while stopping:" + stop_status["message"]
            return stop_status
        if args is None:
            if old_args is None:
                return {"code": BAD_ARG, "message": "Must provide starting arguments at the beginning"}
        return await self.start(old_args if args is None else args)

    def _stream_history(self, stream_name, limit=None):
        # it's better to read from the tail until reaching limit
        history = repr(b''.join(self._monitor[stream_name].history).decode(errors='replace'))
        if limit is not None and (l := len(history)) > limit:
            history = f"'...[{l - limit} chars]" + history[-limit:]
        return history

# def is_running(self):
#     return self._process_info is not None and self._process_info.process is not None
