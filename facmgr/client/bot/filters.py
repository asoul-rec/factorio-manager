from pyrogram import filters
from pyrogram.types import Message
from . import config


@filters.create
def admin(_, __, m: Message):
    return m.chat.id and m.chat.id == config.config.get("admin_id")


@filters.create
async def group_topic(_, __, m: Message):
    # REMOVE THIS after pyrofork fixed this bug
    if getattr(m, "topic", None) is None:
        m.topic = None
    if (group_id := config.config.get("chat_id")) is None:
        return False  # admin private chat only
    if group_id != m.chat.id:
        return False
    if (topic_id := config.config.get("topic_id")) is not None:
        return await filters.topic(topic_id)(None, m)
    else:
        return not m.is_topic_message  # only allow non-topic message if no topic id


def not_command(prefix='/'):
    return filters.create(lambda _, __, m: m.text is not None and not m.text.startswith(prefix))
