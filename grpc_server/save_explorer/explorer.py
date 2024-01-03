import asyncio

from .parser import load_metadata, json_stringify
import os


class SavesExplorer:
    _CACHE_MAX = 200
    _CACHE_MIN = 20

    def __init__(self, path):
        self.path = path
        self._cache = {}

    def _full_path(self, *names):
        return os.path.join(self.path, *names)

    async def load(self, name, flush_cache=False):
        full_name = self._full_path(name)
        file_stat = os.stat(full_name)
        key = file_stat.st_mtime, file_stat.st_size
        if not flush_cache:
            try:
                return self._cache[key]
            except KeyError:
                pass
        self._cache[key] = result = await asyncio.to_thread(load_metadata, full_name)
        if len(self._cache) > self._CACHE_MAX:
            # sort from new to old, keep the first CACHE_MIN items
            for key in sorted(self._cache, reverse=True)[self._CACHE_MIN:]:
                del self._cache[key]
        return result

    async def load_json(self, name, flush_cache=False):
        return json_stringify(await self.load(name, flush_cache=flush_cache))

    async def load_all(self):
        return {
            name.rsplit('.', maxsplit=1)[0]: await self.load(name)
            for name in await self.get_names()
        }

    async def get_names(self):
        return [name
                for name in await asyncio.to_thread(os.listdir, self.path)
                if name.endswith('.zip')]
