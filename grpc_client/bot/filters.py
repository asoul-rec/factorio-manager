from pyrogram import filters
from pyrogram.types import Message
from . import config


@filters.create
def admin(_, __, m: Message):
    return m.chat.id and m.chat.id == config.config.get("admin_id")


@filters.create
def group_topic(_, __, m: Message):
    if (group_id := config.config.get("chat_id")) is None:
        return False
    if (topic_id := config.config.get("topic_id")) is None:
        return m.chat.id == group_id
    if topic_id == 1:
        return m.reply_to_message_id is None  # todo: correctly process reply message in general
    if m.reply_to_top_message_id:  # this mean a reply in reply or reply in topic
        return topic_id == m.reply_to_top_message_id
    return topic_id == m.reply_to_message_id


def not_command(prefix='/'):
    return filters.create(lambda _, __, m: m.text is not None and not m.text.startswith(prefix))
