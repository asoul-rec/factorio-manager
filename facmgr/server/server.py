import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, Literal

import grpc
from ..protobuf.facmgr_pb2_grpc import add_ServerManagerServicer_to_server
from .grpc_methods import ServerManager


@dataclass
class Config:
    address: str
    saves_dir: str
    fac_exec: str
    fac_timeout: Optional[int]
    executable_is_wrapper: Optional[bool]
    stop_strategy: Optional[Literal['quit', 'interrupt']]


# Starting the server
async def run(config: Config):
    server = grpc.aio.server(compression=grpc.Compression.Deflate)
    manager_servicer = ServerManager(
        config.saves_dir, config.fac_exec, config.fac_timeout,
        executable_is_wrapper=config.executable_is_wrapper, stop_strategy=config.stop_strategy
    )
    add_ServerManagerServicer_to_server(manager_servicer, server)
    listen_addr = config.address
    server.add_insecure_port(listen_addr)
    await server.start()
    logging.warning(f'Start serving on {listen_addr}')
    try:
        await asyncio.Event().wait()  # run forever
    except asyncio.CancelledError:
        async with asyncio.timeout(30):
            await asyncio.gather(manager_servicer.daemon.stop(), server.stop(grace=None))
        raise
