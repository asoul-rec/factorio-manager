from contextlib import asynccontextmanager
from typing import Sequence, TypedDict, Optional, Literal, AsyncIterator
import json

import grpc
from google.protobuf.empty_pb2 import Empty
from .server_pb2 import (
    Ping, SaveName, SaveNameList, ServerOptions, SaveStat as SaveStatPB2, Status as StatusPB2,
    Command, UpdateInquiry, GameUpdates, ManagerStat, OutputStreams, UploadTelegramInfo, TelegramClient
)
from .server_pb2_grpc import ServerManagerStub


class SaveStat(TypedDict):
    version: str
    scenario: str
    mods: list
    startup_settings: list
    ticks: tuple[int, int, int]
    play_time: str
    total_time: str
    unknowns: list


class Status(TypedDict):
    code: int
    message: Optional[str]


class ServerManagerClient:
    def __init__(self, address):
        self.address = address

    @asynccontextmanager
    async def _channel_stub(self):
        async with grpc.aio.insecure_channel(self.address) as channel:
            yield ServerManagerStub(channel)

    async def get_manager_status(self, verbose=False) -> ManagerStat:
        async with self._channel_stub() as stub:
            return await stub.GetManagerStatus(Ping(verbose=verbose))

    async def get_all_save_name(self) -> list[str]:
        async with self._channel_stub() as stub:
            save_list: SaveNameList = await stub.GetAllSaveName(Empty())
            return [save_name.name for save_name in save_list.save_name]

    async def get_stat_by_name(self, save_name: str) -> SaveStat:
        async with self._channel_stub() as stub:
            save_stat: SaveStatPB2 = await stub.GetStatByName(SaveName(name=save_name))
            return json.loads(save_stat.stat_json)

    async def start_server_by_name(self, save_name: str, extra_args: Sequence[str] = None) -> Status:
        async with self._channel_stub() as stub:
            server_options = ServerOptions(save_name=SaveName(name=save_name))
            if extra_args is not None:
                server_options.extra_args.extend(extra_args)
            status: StatusPB2 = await stub.StartServerByName(server_options)
            return {"code": status.code, "message": status.message}

    async def stop_server(self) -> Status:
        async with self._channel_stub() as stub:
            status: StatusPB2 = await stub.StopServer(Empty())
            return {"code": status.code, "message": status.message}

    async def restart_server(self, save_name: str = None, extra_args: Sequence[str] = None) -> Status:
        async with self._channel_stub() as stub:
            save_name = None if save_name is None else SaveName(name=save_name)
            server_options = ServerOptions(save_name=save_name)
            if extra_args is not None:
                server_options.extra_args.extend(extra_args)
            status: StatusPB2 = await stub.RestartServer(server_options)
            return {"code": status.code, "message": status.message}

    async def in_game_command(self, cmd: str) -> Status:
        async with self._channel_stub() as stub:
            status: StatusPB2 = await stub.InGameCommand(Command(cmd=cmd))
            return {"code": status.code, "message": status.message}

    async def get_message(self, from_offset=None) -> tuple[int, Sequence[bytes]]:
        async with self._channel_stub() as stub:
            update: GameUpdates = await stub.WaitForUpdates(UpdateInquiry(from_offset=from_offset))
            return update.latest_offset, update.updates

    async def get_output_streams(self) -> dict[Literal['stdout', 'stderr'], bytes]:
        async with self._channel_stub() as stub:
            streams: OutputStreams = await stub.GetOutputStreams(Empty())
            return {'stdout': streams.stdout, 'stderr': streams.stderr}

    async def upload_to_telegram(self, save_name: str, session_string: str,
                                 chat_id: int, reply_id: Optional[int] = None) -> AsyncIterator[Status]:
        async with self._channel_stub() as stub:
            status_stream: AsyncIterator[StatusPB2] = stub.UploadToTelegram(UploadTelegramInfo(
                save_name=SaveName(name=save_name),
                client=TelegramClient(session_string=session_string, chat_id=chat_id, reply_id=reply_id)
            ))
            async for status in status_stream:
                yield {"code": status.code, "message": status.message}
