from telethon import TelegramClient, events, Button
from env import env
from mongo import Mongo
import polib
import helper
from bson.objectid import ObjectId
from persian_calendar import Persian
import input_validator

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


@bot.on(events.NewMessage(pattern='/start', incoming=True))
@bot.on(events.CallbackQuery(data=b'main_menu'))
async def start(event):
    # Create welcome message
    f1 = f"{msg.get('start_welcome')}! {msg.get('start_id')}: {event.sender_id}"

    # Check if sender is admin
    if event.sender_id in config.admin_list:
        # Create admin keyboard
        k_admin = [
            [Button.inline(msg.get('start_keyboard_admin_employees'), b'admin_employees'),
             Button.inline(msg.get('admin_employees_keyboard_add_employee'), b'admin_add_employee')],
            [Button.inline(msg.get('start_keyboard_admin_tasks'), b'admin_tasks'),
             Button.inline(msg.get('new_task'), b'new_task')]
        ]
        await event.respond(f1, buttons=k_admin)
    else:
        # Create user keyboard
        k_user = [
            [Button.request_phone(msg.get('share_phone_number')),
             Button.inline(msg.get('new_task'), b'new_task')]
        ]
        await event.respond(f1, buttons=k_user)

    raise events.StopPropagation


@bot.on(events.CallbackQuery(data=b'admin_employees'))
async def admin_employees(event):
    text, buttons = helper.list_employees(db, msg)
    await event.respond(text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(data=b'admin_tasks'))
async def admin_tasks(event):
    raise events.StopPropagation


@bot.on(events.CallbackQuery(data=b'admin_add_employee'))
async def admin_add_employee(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message(msg.get('enter_employee_name'))
        response_name = await conv.get_response()
        name = response_name.text
        await conv.send_message(msg.get('enter_employee_number'))
        response_number = await conv.get_response()
        number = input_validator.phone_number(response_number.text)
        employee = {
            'name': name,
            'number': number,
            'telegram_id': 0,
            'rating': 0,
            'groups': []
        }
        db.insert('employee', employee)
        await conv.send_message(msg.get('employee_saved'))
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'list_employees:*'))
async def list_employees(event):
    page = event.data.decode().split(':')[1]
    text, buttons = helper.list_employees(db, msg, page=page)
    await event.respond(text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'manage_employee:*'))
async def manage_employee(event):
    employee_id = event.data.decode().split(':')[1]
    text, buttons = helper.manage_employee(db, msg, employee_id=employee_id)
    await event.respond(text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'admin_edit_employee:*'))
async def admin_edit_employee(event):
    employee_id = event.data.decode().split(':')[1]
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message(msg.get('enter_employee_name'))
        response_name = await conv.get_response()
        name = response_name.text
        db.update('employee', {'_id': ObjectId(employee_id)}, {'$set': {'name': name}})
        await conv.send_message(msg.get('employee_saved'))
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'admin_delete_employee:*'))
async def admin_delete_employee(event):
    employee_id = event.data.decode().split(':')[1]
    async with bot.conversation(event.sender_id) as conv:
        db.delete('employee', {'_id': ObjectId(employee_id)})
        await conv.send_message(msg.get('employee_deleted'))
    raise events.StopPropagation


@bot.on(events.CallbackQuery(data=b'new_task'))
async def new_task(event):
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message(msg.get('enter_task_title'))
        response_title = await conv.get_response()
        title = response_title.text
        await conv.send_message(msg.get('enter_task_description'))
        response_description = await conv.get_response()
        description = response_description.text
        await conv.send_message(msg.get('enter_task_start_date'))
        response_start_date = await conv.get_response()
        start_date = Persian(response_start_date.text).gregorian_datetime()
        await conv.send_message(msg.get('enter_task_deadline'))
        response_deadline = await conv.get_response()
        deadline = Persian(response_deadline.text).gregorian_datetime()
        task = {
            'title': title,
            'description': description,
            'start_date': start_date,
            'deadline': deadline,
            'operators': [],
            'status': 'new'
        }
        db.insert('task', task)
        await conv.send_message(msg.get('task_saved'))
        # TODO select operators
    raise events.StopPropagation


# Connect to Telegram and run in a loop
try:
    print('bot starting...')
    bot.start(bot_token=config.bot_token)
    print('bot started')
    bot.run_until_disconnected()
finally:
    print('never runs!')
