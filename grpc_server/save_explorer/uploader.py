import asyncio


class TelegramUploader:
    _cache = {}

    def __init__(self, session_string):
        import pyrogram  # delayed import
        try:
            self.client = self._cache[session_string]
        except KeyError:
            self.client = self._cache[session_string] = pyrogram.Client(
                '',
                session_string=session_string,
                no_updates=True
            )

    async def send(self, file, chat_id, reply_id):
        async def progress(*args):
            await q.put(args)

        q = asyncio.Queue()
        if not self.client.is_initialized:
            await self.client.start()
        task = asyncio.create_task(self.client.send_document(
            document=file, force_document=True, chat_id=chat_id, reply_to_message_id=reply_id, progress=progress
        ))
        task.add_done_callback(lambda _: q.put_nowait(None))
        while (qi := await q.get()) is not None:
            yield qi
        await task  # re-raise exception if any
