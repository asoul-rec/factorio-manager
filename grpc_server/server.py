import asyncio

import grpc
from . import server_pb2_grpc
from .grpc_methods import ServerManager


# Starting the server
async def run(config):
    server = grpc.aio.server(compression=grpc.Compression.Deflate)
    server_pb2_grpc.add_ServerManagerServicer_to_server(ServerManager(config.saves_dir, config.fac_exec), server)
    listen_addr = config.address
    server.add_insecure_port(listen_addr)
    await server.start()
    print(f'Serving on {listen_addr}')
    await server.wait_for_termination()
