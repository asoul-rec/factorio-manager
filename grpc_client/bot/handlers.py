import asyncio
import io
import json
import logging
import shlex
from collections import namedtuple
from typing import Optional
import re
import functools

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.errors import BadRequest
from pyrogram.raw.types import InputPeerChannel
from grpc_client.bot import config
from grpc_client.grpc_methods import ServerManagerClient
import grpc
from .replies import REPLIES

SUCCESS = 0

ABORTED = 100
SATISFIED = 101
NOT_AVAILABLE = 102
STARTING = 103
STOPPING = 104

BAD_ARG = 111

EXIT = 120
EXIT_UNEXPECT = 121
EXIT_ERROR = 122


def _strip_command(s: str) -> str:
    s = s.strip()
    if s.startswith('/'):
        s = ''.join(s.split(maxsplit=1)[1:])
    return s


async def set_chat_id(client: Client, message: Message):
    text = _strip_command(message.text)

    if text.lower() == 'no':  # set as private only
        config.config['chat_id'] = config.config['admin_id']
        config.write()
        await message.reply(REPLIES["done"]["private"])
        return

    match = re.fullmatch(r"https://t\.me/(c/(?P<gid>\d+)|(?P<name>[^/]+))"
                         r"(/(?P<mid1>\d+))?(/(?P<mid2>\d+))?", text)
    if not match:
        await message.reply(REPLIES["set"]["chat"])
        return
    info = match.groupdict()
    try:
        if name := info['name']:
            peer = await client.resolve_peer(name)
        else:
            peer = await client.resolve_peer(int('-100' + info['gid']))
    except BadRequest:  # wrong name or id never seen
        await message.reply(REPLIES["err"]["id_invalid"])
        return
    if not isinstance(peer, InputPeerChannel):
        await message.reply(REPLIES["err"]["not_channel"])
        return
    chat_id = int('-100' + str(peer.channel_id))
    config.config['chat_id'] = chat_id
    chat = await client.get_chat(chat_id)
    if info['mid2']:
        from . import topic_patch  # noqa, a monkey-patch to 'get_messages'
        topic_id = int(info['mid1'])
        topic_message = await client.get_messages(chat_id, int(info['mid1']))
        if topic_create := getattr(topic_message, 'topic', None):
            topic_title = topic_create.title
        else:
            topic_title = "General"
            topic_id = 1
        config.config['topic_id'] = topic_id
        await message.reply(REPLIES["done"]["chat_topic"].format(chat.title, topic_title))
    else:
        del config.config['topic_id']
        await message.reply(REPLIES["done"]["chat"].format(chat.title))
    config.write()


async def set_address(_, message: Message):
    address = _strip_command(message.text)
    if not address:
        await message.reply(REPLIES["set"]["address"])
        return
    client = ServerManagerClient(address)
    try:
        _, welcome = await client.get_manager_status()
        config.config["address"] = address
        config.write()
        await message.reply(REPLIES["done"]["grpc_connect"].format(address, welcome))
    except grpc.aio.AioRpcError as e:
        logging.error(f"{type(e).__name__}: {e.debug_error_string()}")
        await message.reply(REPLIES["err"]["bad_manager"].format(address))


async def set_extra_args(_, message: Message):
    args = _strip_command(message.text)
    args = shlex.split(args)
    old_args = config.config.get("extra_args", [])
    config.config["extra_args"] = args
    config.write()
    old_mono = '`' + shlex.join(old_args) + '`'
    new_mono = '`' + shlex.join(args) + '`'
    await message.reply(REPLIES["done"]["extra_args"].format(old_mono, new_mono), parse_mode=ParseMode.MARKDOWN)


async def get_config(_, message: Message):
    conf = config.config.copy()
    for sensitive in ["api_id", "api_hash", "bot_token"]:
        if sensitive in conf:
            del conf[sensitive]
    await message.reply(REPLIES["done"]["all_conf"].format(json.dumps(conf, indent=2)))


class FactorioHandler:
    manager: Optional[ServerManagerClient] = None
    _push_info: Optional[dict] = None
    _push_task: asyncio.Task = None

    # _push_wakeup: asyncio.Event

    def __init__(self):
        # self._push_wakeup = asyncio.Event()
        if address := config.config.get('address'):
            self.manager = ServerManagerClient(address)

    @property
    def push_info(self):
        if self._push_info is not None:
            # prevent modification
            return namedtuple("PushInfo", self._push_info)(**self.push_info)

    @push_info.setter
    def push_info(self, new_info):
        if new_info is None:
            self._push_info = None
        else:
            self._push_info = new_info.copy()
        if self._push_info and (self._push_task is None or self._push_task.done()):
            self._push_task = asyncio.create_task(self.push_update(**self._push_info))
        # self._push_wakeup.set()

    @staticmethod
    def check_manager(func):
        @functools.wraps(func)
        async def wrapper(self: "FactorioHandler", client, message):
            if self.manager is None:
                if address := config.config.get('address'):
                    self.manager = ServerManagerClient(address)
                else:
                    await message.reply(REPLIES["err"]["no_manager"])
                    return
            # passively activate the push task
            if self._push_info and (self._push_task is None or self._push_task.done()):
                self._push_task = asyncio.create_task(self.push_update(**self._push_info))
            try:
                await func(self, client, message)
            except grpc.aio.AioRpcError as e:
                logging.error(f"{type(e).__name__}: {e.debug_error_string()}")
                await message.reply(REPLIES["err"]["bad_manager"].format(self.manager.address))

        return wrapper

    @check_manager
    async def start_server(self, client: Client, message: Message):
        name = _strip_command(message.text)
        if not name:
            await message.reply(REPLIES["err"]["no_savename"])
            return
        result = await self.manager.start_server_by_name(name, config.config.get('extra_args'))
        if code := result['code']:
            logging.warning(f"starting failed, status: {result}")
            if code == SATISFIED:
                await message.reply(REPLIES["err"]["started"])
            else:
                await message.reply(REPLIES["err"]["unknown_failed"])
                await self.send_output_admin(client)
        else:
            logging.info(f"server started successfully")
            await message.reply(REPLIES["done"]["start"])

    @check_manager
    async def stop_server(self, client: Client, message: Message):
        result = await self.manager.stop_server()
        if code := result['code']:
            logging.warning(f"stopping failed, status: {result}")
            if code == SATISFIED:
                await message.reply(REPLIES["err"]["stopped"])
            else:
                running, _ = await self.manager.get_manager_status()
                if not running:  # don't care why it's stopped on client side
                    await message.reply(REPLIES["err"]["stopped"])
                else:
                    await message.reply(REPLIES["err"]["unknown_failed"])
                    await self.send_output_admin(client)
        else:
            logging.info(f"server stopped successfully")
            await message.reply(REPLIES["done"]["stop"])

    @check_manager
    async def restart_server(self, client: Client, message: Message):
        name = _strip_command(message.text)
        if name:
            result = await self.manager.restart_server(name, config.config.get('extra_args'))
        else:
            result = await self.manager.restart_server()
        if code := result['code']:
            logging.warning(f"restarting failed, status: {result}")
            if code == BAD_ARG:
                await message.reply(REPLIES["err"]["no_savename"])
            else:
                await message.reply(REPLIES["err"]["unknown_failed"])
                await self.send_output_admin(client)
        else:
            logging.info(f"server restarted successfully")
            await message.reply(REPLIES["done"]["restart"])

    @check_manager
    async def running_status(self, _, message: Message):
        running, _ = await self.manager.get_manager_status()
        await message.reply(REPLIES["done"]["running" if running else "not_running"])

    @check_manager
    async def run_command(self, _, message: Message):
        cmd = _strip_command(message.text)
        auto_fwd = not message.text.startswith('/')
        if auto_fwd:
            user = message.from_user
            name = ' '.join([nm for nm in [user.first_name, user.last_name] if nm is not None])
            cmd = f"{name if name else '<unknown>'}: {cmd}"
        result = await self.manager.in_game_command(cmd)
        if code := result["code"]:
            logging.warning(f"run command failed, status: {result}")
            if not auto_fwd and code == NOT_AVAILABLE:  # always True
                await message.reply(REPLIES["err"]["stopped"])
        else:
            if not auto_fwd:
                await message.reply(REPLIES["done"]["command"])

    @check_manager
    async def saves_list(self, _, message: Message):
        names = await self.manager.get_all_save_name()
        infos = await asyncio.gather(*[self.manager.get_stat_by_name(name) for name in names])
        result = '\n'.join([f"{name}: {info.get('play_time', 'unknown')}" for name, info in zip(names, infos)])
        await message.reply(REPLIES["done"]["savelist"].format(result))

    async def push_update(self, client: Client, chat_id):
        offset = None
        info_pattern = re.compile(r"(?P<datetime>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)"
                                  r" \[(?P<type>[A-Z]+)] (?P<message>.*)")
        while True:
            message_buffer = []
            last_offset, messages = await self.manager.get_message(offset)
            for message in messages:
                message = message.rstrip(b'\r\n').decode(errors='replace')
                if (match := info_pattern.fullmatch(message)) is None:
                    continue
                tp, msg = match.group("type"), match.group("message")
                if tp == "CHAT":
                    name, body = re.fullmatch(r"(.+?): (.*)", msg).groups()
                    if name == "<server>":  # ignore outgoing messages
                        continue
                    else:
                        message_buffer.append(REPLIES["game"]["chat"].format(name, body))
                elif tp == "JOIN":
                    name = re.fullmatch(r"(.+?) joined the game", msg).group(1)
                    message_buffer.append(REPLIES["game"]["join"].format(name))
                elif tp == "LEAVE":
                    name = re.fullmatch(r"(.+?) left the game", msg).group(1)
                    message_buffer.append(REPLIES["game"]["leave"].format(name))
                else:
                    message_buffer.append(message)
                await client.send_message(
                    chat_id, text=''.join(message_buffer)[:4000],
                    reply_to_message_id=config.config.get("topic_id")
                )
                await asyncio.sleep(3)  # simple throttling for 20/min
            offset = last_offset + 1

    async def send_output_admin(self, client: Client):
        admin_id = config.config['admin_id']
        output = await self.manager.get_output_streams()
        if s := output['stdout']:
            await client.send_document(admin_id, io.BytesIO(s), file_name="stdout.txt")
        else:
            await client.send_message(admin_id, "stdout is empty")
        if s := output['stderr']:
            await client.send_document(admin_id, io.BytesIO(s), file_name="stderr.txt")
        else:
            await client.send_message(admin_id, "stderr is empty")

    # async def _push_watchdog(self):
    #     while True:
    #         if self.push_info:
    #
    #             task = self.push_update(**self.push_info)
