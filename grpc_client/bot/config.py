import json
import logging
import os

_file_name: str  # or path?
config = {}


def load(cfg):
    global config, _file_name
    _file_name = cfg
    if os.path.isfile(_file_name):
        with open(_file_name, 'r') as f:
            config = json.load(f)
    else:
        config = {"api_id": None, "api_hash": None, "bot_token": None}
        write()


def write():
    logging.info(f"saving new config to {_file_name}")
    try:
        with open(_file_name, 'w') as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        logging.error(f"failed to save config: {e}")
