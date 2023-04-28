from telethon import TelegramClient, events
from env import env


# environment detection
if env == 'live':
    import config_live
    config = config_live
elif env == 'dev':
    import config_dev
    config = config_dev
else:
    import config_test
    config = config_test

# Initialize Telegram client
bot = TelegramClient(session=config.session_name, api_id=config.api_id, api_hash=config.api_hash)


@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(event.stringify())
    raise events.StopPropagation


@bot.on(events.NewMessage(pattern='/add_employee', from_users=config.admin_list))
async def add_employee(event):
    # TODO number, name
    await event.respond(event)
    raise events.StopPropagation

# Connect to Telegram and run in a loop
bot.start(bot_token=config.bot_token)
bot.run_until_disconnected()
