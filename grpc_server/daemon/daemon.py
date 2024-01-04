import logging
import os
import asyncio
import subprocess
from collections import deque
from contextlib import contextmanager
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

ABORTED = 100
SATISFIED = 101
NOT_AVAILABLE = 102
STARTING = 103
STOPPING = 104

BAD_ARG = 111

EXIT = 120
EXIT_UNEXPECT = 121
EXIT_ERROR = 122


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
    """
    Act as a daemon for Factorio server process management.
    Note: Factorio doesn't allow running multiple instances simultaneously, so in this implementation,
    we must wait until the old process is fully stopped before starting a new one
    """

    @dataclass
    class Info:
        args: Optional[list[str]] = None
        daemon: Optional[asyncio.Task] = None
        error: Optional[Status] = None
        changing: Optional[int] = None
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
        # starting
        kwargs = {'stdin':  asyncio.subprocess.PIPE,
                  'stdout': asyncio.subprocess.PIPE,
                  'stderr': asyncio.subprocess.PIPE}
        try:
            if os.name == 'nt':
                logging.debug(f"starting the server with detached cmd as wrapper, cmd={_cmd_path()}")
                kwargs["creationflags"] = subprocess.DETACHED_PROCESS
                self.process = await asyncio.create_subprocess_exec(_cmd_path(), '/C', self.executable, *args, **kwargs)
            else:
                logging.debug("starting the server as a subprocess directly")
                self.process = await asyncio.create_subprocess_exec(self.executable, *args, **kwargs)
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
            self.process.kill()  # note: kill() seems NOT working for the cmd wrapper solution
        finally:
            if self.process.returncode is None:
                self.process.kill()

        stdout = self._stream_history('stdout', 128)
        stderr = self._stream_history('stderr', 128)
        out_streams = f'{stdout=!s}, {stderr=!s}'
        # exiting (note that these error info may never be used if the next operation do not need it)
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

    @contextmanager
    def _changing_state(self, code):
        """similar to a lock, but fail rather than wait for release when occupied"""
        if (old_code := self._process_info.changing) is None:
            self._process_info.changing = code
            yield
            self._process_info.changing = None
        else:
            yield {"code":    old_code,
                   "message": {STARTING: "The server is starting.", STOPPING: "The server is stopping"}[old_code]}

    async def start(self, args) -> Status:
        with self._changing_state(STARTING) as error:
            # abort in invalid states
            if error is not None:
                return error
            if self.process is not None:
                if (error := self._process_info.error) is not None:
                    return error
                return {"code": SATISFIED, "message": "The server is already running."}
            # prepare for starting
            logging.info(f"start Factorio server with {args=}")
            self._process_info.changing = STARTING
            self._process_info.args = args
            self._process_info.error = None
            if self._process_info.daemon is not None:
                self._process_info.daemon.cancel()
            # start server
            self._monitor['stdout'].stream = None  # clear the old stream to monitor the keyword correctly
            wait_in_game = asyncio.create_task(
                self._monitor['stdout'].wait_for(b'changing state from(CreatingGame) to(InGame)')
            )
            self._process_info.daemon = asyncio.create_task(self._daemon(args))
            done, pending = await asyncio.wait(
                [wait_in_game, self._process_info.daemon],
                timeout=self.global_timeout, return_when=asyncio.FIRST_COMPLETED
            )
            # detect the result
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
        with self._changing_state(STOPPING) as error:
            # abort in invalid states
            if error is not None:
                return error
            if self.process is None or self.process.returncode:  # do nothing if stopped
                if (error := self._process_info.error) is not None:
                    return error
                return {"code": SATISFIED, "message": "The server is already stopped."}
            # exit gracefully with saving
            if os.name == 'nt':
                # /quit command also work for Linux
                logging.info("stopping the server by /quit command")
                self.in_game_command("/quit")
                self.process.stdin.write_eof()
            else:
                # SIGINT not work for Windows and I don't know how to use CTRL_C_EVENT correctly
                logging.info("stopping the server by signal.SIGINT")
                self.process.send_signal(SIGINT)
            # wait_closed = asyncio.create_task(
            #     self._monitor['stdout'].wait_for(b'changing state from(Disconnected) to(Closed)')
            # )
            await asyncio.wait([self._process_info.daemon], timeout=self.global_timeout)
            # detect the result
            self._process_info.error = None
            if not self._process_info.daemon.done():
                self._process_info.daemon.cancel()
                return {"code": EXIT_ERROR, "message": f"Force stop after {self.global_timeout}s"}
            return {"code": SUCCESS, "message": None}

    async def restart(self, args=None) -> Status:
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

    def in_game_command(self, cmd: str) -> Status:
        if self.process is None:
            return {"code": NOT_AVAILABLE, "message": "The server is not running."}
        cmd = cmd.splitlines()
        cmd.append('')
        cmd = os.linesep.join(cmd).encode()
        self.process.stdin.write(cmd)
        # we cannot easily detect whether the server get the message and run it successfully,
        # so leave this detection work for high-level code
        return {"code": 0, "message": None}

