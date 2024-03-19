import asyncio
import logging

import grpc
from . import server_pb2_grpc
from .grpc_methods import ServerManager


# Starting the server
async def run(config):
    server = grpc.aio.server(compression=grpc.Compression.Deflate)
    manager_servicer = ServerManager(config.saves_dir, config.fac_exec, fac_timeout=30)
    server_pb2_grpc.add_ServerManagerServicer_to_server(manager_servicer, server)
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
