import argparse
import asyncio
import logging

from pyrogram import Client, filters, idle
from pyrogram.enums import ParseMode

from grpc_client import bot

logging.basicConfig(format='%(asctime)s [%(levelname).1s] [%(name)s] %(message)s', level=logging.DEBUG)
logging.getLogger('pyrogram').setLevel(logging.INFO)

parser = argparse.ArgumentParser(description="Factorio headless server manager client [v240108]")
parser.add_argument('--bot_config', default="./bot_config.json")

parser.add_argument('--api_id')
parser.add_argument('--api_hash')
parser.add_argument('--bot_token')
parser.add_argument('--admin_id')

cli_args = parser.parse_args()

bot.config.load(cli_args.bot_config)

cfgs_from_file = bot.config.config

api_id    = cli_args.api_id or cfgs_from_file.get('api_id')
api_hash  = cli_args.api_hash or cfgs_from_file.get('api_hash')
bot_token = cli_args.bot_token or cfgs_from_file.get('bot_token')
admin_id  = cli_args.admin_id or cfgs_from_file.get('admin_id')

# bot.config.config.update(api_id=api_id, api_hash=api_hash, bot_token=bot_token, admin_id=admin_id)
# this may not work as expected since we use systemd credential management.
# bot.config.write(cli_args.bot_config)

app = Client('Factorio Bot', api_id=api_id, api_hash=api_hash, bot_token=bot_token,
             parse_mode=ParseMode.DISABLED, in_memory=True)


async def run_app():
    logging.info("start Factorio bot")
    async with app:
        try:
            if await bot.utils.first_run(app):
                bot.utils.add_handlers(app)
                await idle()
            else:
                logging.error("config error. exiting")
        except Exception as e:
            logging.error(f"initialization failed, error: {e}. exiting")


@app.on_message(filters=filters.command("help"))
async def help_command(_, message):
    await message.reply("no help")


def start():
    loop = asyncio.get_event_loop()
    run = loop.run_until_complete(run_app())


if __name__ == '__main__':
    start()
