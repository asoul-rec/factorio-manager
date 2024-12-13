from pyrogram import raw, utils
import logging

_raw_parse_messages = utils.parse_messages


async def parse_messages_and_topic(*args, **kwargs):
    # super
    result = await _raw_parse_messages(*args, **kwargs)
    # patch: extract topic creation details
    messages = args[1] if len(args) >= 2 else kwargs['messages']
    if raw_list := messages.messages:
        for raw_m, parsed_m in zip(raw_list, result):
            if isinstance(topic_create := getattr(raw_m, 'action', None), raw.types.MessageActionTopicCreate):
                parsed_m.topic = topic_create
    return result

logging.warning("Pyrogram topic patch enabled")
utils.parse_messages = parse_messages_and_topic
