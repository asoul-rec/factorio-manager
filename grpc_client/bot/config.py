import json
import logging
import os

_file_name = "./bot_config.json"
config: dict


def load():
    global config
    if os.path.isfile(_file_name):
        with open(_file_name, 'r') as f:
            config = json.load(f)
    else:
        config = {"api_id": None, "api_hash": None, "bot_token": None}
        write()


def write():
    logging.info(f"saving new config to {_file_name}")
    with open(_file_name, 'w') as f:
        json.dump(config, f, indent=2)
