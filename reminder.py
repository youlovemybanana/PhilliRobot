from telethon import TelegramClient, sync
from telethon.tl.types import PeerChat, PeerChannel
from env import env
from mongo import Mongo
import polib
import reporting


# Environment detection
if env == 'live':
    import config_live
    config = config_live
elif env == 'dev':
    import config_dev
    config = config_dev
else:
    import config_test
    config = config_test

# Load message file
msg = {}
for entry in polib.pofile('msg_' + config.language + '.po'):
    msg[entry.msgid] = entry.msgstr

# Connect to database
db = Mongo(config.db_host, config.db_port, config.db_name)

# Initialize Telegram client
if config.proxy:
    bot = TelegramClient(session=config.session_name, api_id=config.api_id, api_hash=config.api_hash,
                         proxy=(config.proxy_protocol, config.proxy_host, config.proxy_port))
else:
    bot = TelegramClient(session=config.session_name, api_id=config.api_id, api_hash=config.api_hash)

bot.start(bot_token=config.bot_token)

if config.module_reminder:
    for g in config.reminder_groups:
        try:
            bot.send_message(PeerChat(g), reporting.report_today(db, msg, config))
        except:
            print(g)
        try:
            bot.send_message(PeerChannel(g), reporting.report_today(db, msg, config))
        except:
            print(g)

bot.disconnect()
