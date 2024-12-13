from importlib.resources import files
from .. import bot
import json

ALL_REPLIES = json.loads(files(bot).joinpath('reply_template.json').read_text(encoding='utf-8'))
REPLIES = ALL_REPLIES['zh_cn'].copy()
