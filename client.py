import argparse
import logging

from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode

from grpc_client import ServerManagerClient

logging.basicConfig(format='%(asctime)s [%(levelname).1s] [%(name)s] %(message)s', level=logging.DEBUG)
logging.getLogger('pyrogram').setLevel(logging.WARNING)

parser = argparse.ArgumentParser(description="Factorio headless server manager client [v231230]")
parser.add_argument('address')
parser.add_argument('--api_id')
parser.add_argument('--api_hash')
parser.add_argument('--bot_token')
cli_args = parser.parse_args()

app = Client('Factorio Bot', api_id=cli_args.api_id, api_hash=cli_args.api_hash,
             bot_token=cli_args.bot_token, parse_mode=ParseMode.DISABLED)
manager = ServerManagerClient(cli_args.address)


@app.on_message(filters=filters.command("help"))
async def help_command(_, message):
    await message.reply(
        """
        This is the help message.
        """
    )


@app.on_message(filters=filters.command("allsaves"))
async def allsaves_command(_, message):
    await message.reply(str(await manager.get_all_save_name()))


@app.on_message(filters=filters.command("detail"))
async def detail_command(_, message):
    name = message.text.split(maxsplit=1)[1:]
    if not name:
        await message.reply("must have name to get")
    else:
        await message.reply(str(await manager.get_stat_by_name(name[0])))


@app.on_message(filters=filters.command("start"))
async def start_command(_, message):
    name = message.text.split(maxsplit=1)[1:]
    if not name:
        await message.reply("must have arg to start")
    else:
        await message.reply(str(await manager.start_server_by_name(name[0])))


@app.on_message(filters=filters.command("stop"))
async def stop_command(_, message):
    await message.reply(str(await manager.stop_server()))


@app.on_message(filters=filters.command("restart"))
async def restart_command(_, message):
    name = message.text.split(maxsplit=1)[1:]
    if not name:
        name = None
    else:
        name = name[0]
    await message.reply(str(await manager.restart_server(name)))


if __name__ == '__main__':
    app.run()
