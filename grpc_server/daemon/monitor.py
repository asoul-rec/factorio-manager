import asyncio
from collections import deque, defaultdict
from typing import Optional, TypedDict, Callable


class AsyncStreamMonitor:
    _stream: asyncio.StreamReader = None
    stream: asyncio.StreamReader
    history: deque
    logger_callback: Optional[Callable[[bytes], None]] = None
    _KeywordInfo = TypedDict('_KeywordInfo', {'count': int, 'found': asyncio.Event, 'result': Optional[bytes]})
    _keywords: defaultdict[bytes, _KeywordInfo]
    _task: asyncio.Task

    def __init__(self, initial_stream=None, *, history_maxlen=None, logger_callback=None):
        self._keywords = defaultdict(lambda: {'count': 0, 'found': asyncio.Event(), 'result': None})
        self.history = deque(maxlen=history_maxlen)
        self.logger_callback = logger_callback
        self.stream = initial_stream

    # use stream as property to avoid inconsistency of setting value directly
    @property
    def stream(self):
        return self._stream

    @stream.setter
    def stream(self, new_stream):
        old_stream, self._stream = self._stream, new_stream
        if old_stream is not None:
            self.history.clear()
            self._keywords.clear()
            self._task.cancel()
        if new_stream is not None:
            self._task = asyncio.create_task(self._run())

    async def _run(self):
        async for line in self._stream:
            assert isinstance(line, bytes)
            self.history.append(line)
            if self.logger_callback is not None:
                self.logger_callback(line)
            for pattern, info in self._keywords.items():
                if not info['found'].is_set() and pattern in line:
                    info['result'] = line
                    info['found'].set()

    async def wait_for(self, keyword: bytes):
        """
        Wait until the keyword found in stream.
            1. Re-entrant in asyncio level: can handle multiple (even the same) keyword;
            2. It will never finish if the stream is finished or changed, so use asyncio.wait_for for timeout if needed;
            3. It can wait for the keyword even if the stream is not available yet

        :param keyword: the bytes string to search for (only within a single line)
        :return: the line containing the keyword
        """
        kw_info = self._keywords[keyword]
        kw_info['count'] += 1
        await kw_info['found'].wait()
        kw_info['count'] -= 1
        if not kw_info['count']:
            del self._keywords[keyword]
        return kw_info['result']

    async def wait_eof(self):
        await self._task
