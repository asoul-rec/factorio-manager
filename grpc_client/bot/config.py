import json
import logging
import os

config: dict


def load(cfg):
    global config
    if os.path.isfile(cfg):
        with open(cfg, 'r') as f:
            config = json.load(f)
    else:
        config = {"api_id": None, "api_hash": None, "bot_token": None}
        write(cfg)


def write(cfg):
    logging.info(f"saving new config to {cfg}")
    with open(cfg, 'w') as f:
        json.dump(config, f, indent=2)
