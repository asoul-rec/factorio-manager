import logging
from typing import Optional

from . import config, handlers, filters as my_filters
from .replies import REPLIES
from asyncio import Event
from pyrogram.handlers import MessageHandler
from pyrogram import Client, filters
from pyrogram.errors import BadRequest


async def first_run(client: Client) -> bool:
    async def wait_first_message(*_):
        finish_step.set()

    async def wait_chat_id(*args):
        await handlers.set_chat_id(*args)
        if config.config.get('chat_id'):
            finish_step.set()

    async def wait_address(*args):
        await handlers.set_address(*args)
        if config.config.get('address'):
            finish_step.set()

    admin_id = config.config['admin_id']
    if config.config.get('chat_id') and config.config.get('address'):
        await client.send_message(admin_id, REPLIES["done"]["welcome"])
        return True

    if admin_id < 0:
        logging.warning("admin is not a user. all admin features are disabled")
        await client.send_message(admin_id, REPLIES["err"]["admin_not_user"])
        return False

    finish_step = Event()
    try:
        await client.resolve_peer(admin_id)
    except BadRequest:
        logging.warning("Do not recognize admin. Waiting for the first message from admin")
        finish_step.clear()
        first_handler = client.add_handler(MessageHandler(wait_first_message, filters=my_filters.admin))
        await finish_step.wait()
        client.remove_handler(*first_handler)

    await client.send_message(admin_id, REPLIES["done"]["first"])
    if not config.config.get('chat_id'):
        finish_step.clear()
        chat_id_handler = client.add_handler(MessageHandler(wait_chat_id, filters=my_filters.admin))
        await client.send_message(admin_id, REPLIES["set"]["chat"])
        await finish_step.wait()
        client.remove_handler(*chat_id_handler)

    if not config.config.get("address"):
        finish_step.clear()
        address_handler = client.add_handler(MessageHandler(wait_address, filters=my_filters.admin))
        await client.send_message(admin_id, REPLIES["set"]["address"])
        await finish_step.wait()
        client.remove_handler(*address_handler)

    return True


def add_handlers(client: Client):
    admin_commands = [
        ['group', handlers.set_chat_id],
        ['server', handlers.set_address],
        ['startarg', handlers.set_extra_args],
        ['getconf', handlers.get_config]
    ]
    for name, func in admin_commands:
        client.add_handler(MessageHandler(func, filters=my_filters.admin & filters.command(name)))

    fac_handlers = handlers.FactorioHandler()
    game_commands = [
        ['start', fac_handlers.start_server],
        ['stop', fac_handlers.stop_server],
        ['restart', fac_handlers.restart_server],
        ['status', fac_handlers.running_status],
        ['run', fac_handlers.run_command],
        ['savelist', fac_handlers.saves_list]
    ]

    for name, func in game_commands:
        client.add_handler(MessageHandler(
            func, filters=(my_filters.admin | my_filters.group_topic) & filters.command(name)
        ))

    client.add_handler(MessageHandler(
        fac_handlers.run_command, filters=my_filters.group_topic & my_filters.not_command()
    ))
    fac_handlers.push_info = {"client": client, "chat_id": config.config["chat_id"]}
    return fac_handlers
