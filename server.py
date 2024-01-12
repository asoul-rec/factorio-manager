import argparse
import asyncio
import logging
import os
import glob

import grpc_server

logging_level = logging.DEBUG if os.environ.get('FACTORIO_MANAGER_DEBUG', False) else logging.INFO
logging.basicConfig(format='%(asctime)s [%(levelname).1s] [%(name)s] %(message)s', level=logging_level)

parser = argparse.ArgumentParser(description="Factorio headless server manager [v240105]")
parser.add_argument('-E', '--executable', help="Factorio binary", required=True)
parser.add_argument('-D', '--data-dir', help="Factorio user data directory which contains 'saves', 'mods', etc.")
parser.add_argument('-p', '--port', type=int, default=50051, help="grpc server port to listen on (default 50051)")
parser.add_argument('-H', '--host', default='[::]', help="grpc server ip to listen on (default [::] for all)")
cli_args = parser.parse_args()
bin = cli_args.executable
data_dir = cli_args.data_dir
if data_dir is None:
    data_dir = app_dir
grpc_address = f'{cli_args.host}:{cli_args.port}'

if os.name == 'nt':
    exec_glob += '.exe'
if not os.path.exists(bin):
    raise FileNotFoundError(f"cannot locate Factorio executable {bin}")

logging.info(f"Using factorio executable: {bin}")
fac_save = os.path.join(data_dir, 'saves')
if not os.path.isdir(fac_save):
    logging.warning(f"no 'saves' dir in the user data directory")


config = type("", (), {'address': grpc_address, 'saves_dir': fac_save, 'fac_exec': bin})

def start():
  asyncio.run(grpc_server.run(config))

if __name__ == '__main__':
    start()
