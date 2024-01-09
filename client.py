import argparse
import asyncio
import logging

from pyrogram import Client, filters, idle
from pyrogram.enums import ParseMode

from grpc_client import bot

logging.basicConfig(format='%(asctime)s [%(levelname).1s] [%(name)s] %(message)s', level=logging.DEBUG)
logging.getLogger('pyrogram').setLevel(logging.INFO)

bot.config.load()
api_id = bot.config.config.get('api_id')
api_hash = bot.config.config.get('api_hash')
bot_token = bot.config.config.get('bot_token')
admin_id = bot.config.config.get('admin_id')
parser = argparse.ArgumentParser(description="Factorio headless server manager client [v240108]")
parser.add_argument('--api_id', default=api_id, required=api_id is None)
parser.add_argument('--api_hash', default=api_hash, required=api_hash is None)
parser.add_argument('--bot_token', default=bot_token, required=bot_token is None)
parser.add_argument('--admin_id', type=int, default=admin_id, required=admin_id is None)
cli_args = parser.parse_args()
api_id, api_hash, bot_token, admin_id = cli_args.api_id, cli_args.api_hash, cli_args.bot_token, cli_args.admin_id
bot.config.config.update(api_id=api_id, api_hash=api_hash, bot_token=bot_token, admin_id=admin_id)
bot.config.write()

app = Client('Factorio Bot', api_id=api_id, api_hash=api_hash, bot_token=cli_args.bot_token,
             parse_mode=ParseMode.DISABLED)


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


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    run = loop.run_until_complete(run_app())
