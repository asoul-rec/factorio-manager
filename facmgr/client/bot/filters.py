from pyrogram import filters
from pyrogram.types import Message
from . import config


@filters.create
def admin(_, __, m: Message):
    return m.chat.id and m.chat.id == config.config.get("admin_id")


@filters.create
def group_topic(_, __, m: Message):
    if (group_id := config.config.get("chat_id")) is None:
        return False  # admin private chat only
    if group_id != m.chat.id:
        return False
    if (topic_id := config.config.get("topic_id")) is None:
        return not m.is_topic_message  # no topic id, only allow non-topic message
    return topic_id == m.topic.id


def not_command(prefix='/'):
    return filters.create(lambda _, __, m: m.text is not None and not m.text.startswith(prefix))
