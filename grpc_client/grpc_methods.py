from typing import Sequence, Iterable, TypedDict, Optional

import grpc
import json
from .server_pb2 import SaveName, SaveNameList, ServerOptions, SaveStat as SaveStatPB2, Status as StatusPB2
from .server_pb2_grpc import ServerManagerStub
from google.protobuf.empty_pb2 import Empty


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

    async def get_all_save_name(self) -> list[str]:
        async with grpc.aio.insecure_channel(self.address) as channel:
            save_list: SaveNameList = await ServerManagerStub(channel).GetAllSaveName(Empty())
            return [save_name.name for save_name in save_list.save_name]

    async def get_stat_by_name(self, save_name: str) -> SaveStat:
        async with grpc.aio.insecure_channel(self.address) as channel:
            save_stat: SaveStatPB2 = await ServerManagerStub(channel).GetStatByName(SaveName(name=save_name))
            return json.loads(save_stat.stat_json)

    async def start_server_by_name(self, save_name: str, extra_args: Sequence[str] = None) -> Status:
        async with grpc.aio.insecure_channel(self.address) as channel:
            server_options = ServerOptions(save_name=SaveName(name=save_name))
            if extra_args is not None:
                server_options.extra_args.extend(extra_args)
            status: StatusPB2 = await ServerManagerStub(channel).StartServerByName(server_options)
            return {"code": status.code, "message": status.message}

    async def stop_server(self) -> Status:
        async with grpc.aio.insecure_channel(self.address) as channel:
            status: StatusPB2 = await ServerManagerStub(channel).StopServer(Empty())
            return {"code": status.code, "message": status.message}

    async def restart_server(self, save_name: str = None, extra_args: Sequence[str] = None) -> Status:
        async with grpc.aio.insecure_channel(self.address) as channel:
            server_options = ServerOptions(save_name=SaveName(name=save_name))
            if extra_args is not None:
                server_options.extra_args.extend(extra_args)
            status: StatusPB2 = await ServerManagerStub(channel).RestartServer(server_options)
            return {"code": status.code, "message": status.message}
