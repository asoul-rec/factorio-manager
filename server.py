import argparse
import asyncio
import logging
import os
import glob

import grpc_server

logging_level = logging.DEBUG if os.environ.get('FACTORIO_MANAGER_DEBUG', False) else logging.INFO
logging.basicConfig(format='%(asctime)s [%(levelname).1s] [%(name)s] %(message)s', level=logging_level)

parser = argparse.ArgumentParser(description="Factorio headless server manager [v231230]")
parser.add_argument('-E', '--app-dir', help="Factorio application directory which contains 'bin', etc.", required=True)
parser.add_argument('-D', '--data-dir', help="Factorio user data directory which contains 'saves', 'mods', etc."
                    " (default the same as app-dir)")
parser.add_argument('-p', '--port', type=int, default=50051, help="grpc server port to listen on (default 50051)")
parser.add_argument('-H', '--host', default='[::]', help="grpc server ip to listen on (default [::] for all)")
cli_args = parser.parse_args()
app_dir = cli_args.app_dir
data_dir = cli_args.data_dir
if data_dir is None:
    data_dir = app_dir
grpc_address = f'{cli_args.host}:{cli_args.port}'

exec_glob = os.path.join("bin", "*", "factorio")
if os.name == 'nt':
    exec_glob += '.exe'
glob_result = glob.glob(exec_glob, root_dir=app_dir)
if not glob_result:
    raise FileNotFoundError(f"cannot locate Factorio executable in the application directory {app_dir}")
if len(glob_result) > 1:
    logging.warning(f"find multiple Factorio executables: {glob_result}")
fac_exec = os.path.join(app_dir, glob_result[0])
logging.info(f"Using factorio executable: {fac_exec}")
fac_save = os.path.join(data_dir, 'saves')
if not os.path.isdir(fac_save):
    logging.warning(f"no 'saves' dir in the user data directory")


config = type("", (), {'address': grpc_address, 'saves_dir': fac_save, 'fac_exec': fac_exec})
asyncio.run(grpc_server.run(config))
