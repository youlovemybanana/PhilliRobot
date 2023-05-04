from telethon import TelegramClient, events
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
    f1 = f"{msg.get('start_welcome')}! {msg.get('start_id')}: {event.sender_id}"
    if event.sender_id in config.admin_list:
        k_admin = helper.get_start_admin_buttons(msg)
        await event.respond(f1, buttons=k_admin)
    else:
        k_user = helper.get_start_user_buttons(msg)
        await event.respond(f1, buttons=k_user)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(data=b'admin_employees'))
async def admin_employees(event):
    text, buttons = helper.list_employees(db, msg)
    await event.respond(text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(data=b'admin_tasks'))
async def admin_tasks(event):
    text, buttons = helper.list_tasks(db, msg)
    await event.respond(text, buttons=buttons)
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
        insert_result = db.insert('employee', employee)
        text, buttons = helper.manage_employee(db, msg, employee_id=ObjectId(insert_result.inserted_id))
        await event.respond(msg.get('employee_saved') + ':\n\n' + text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'list_employees:*'))
async def list_employees(event):
    page = event.data.decode().split(':')[1]
    text, buttons = helper.list_employees(db, msg, page=page)
    await event.respond(text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'list_tasks:*'))
async def list_tasks(event):
    page = event.data.decode().split(':')[1]
    text, buttons = helper.list_tasks(db, msg, page=page)
    await event.respond(text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'manage_employee:*'))
async def manage_employee(event):
    employee_id = event.data.decode().split(':')[1]
    text, buttons = helper.manage_employee(db, msg, employee_id=employee_id)
    await event.respond(text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'manage_task:*'))
async def manage_task(event):
    task_id = event.data.decode().split(':')[1]
    text, buttons = helper.manage_task(db, msg, task_id=task_id)
    await event.respond(text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'admin_edit_employee:*'))
async def admin_edit_employee(event):
    employee_id = event.data.decode().split(':')[1]
    async with bot.conversation(event.sender_id) as conv:
        ask_name = f"{msg.get('enter_employee_name')}.\n{msg.get('ignore_entry')}."
        await conv.send_message(ask_name)
        response_name = await conv.get_response()
        if response_name.text != '.':
            db.update('employee', {'_id': ObjectId(employee_id)},
                      {'$set': {'name': response_name.text}})
        ask_number = f"{msg.get('enter_employee_number')}.\n{msg.get('ignore_entry')}."
        await conv.send_message(ask_number)
        response_number = await conv.get_response()
        if response_number.text != '.':
            new_number = input_validator.phone_number(response_number.text)
            db.update('employee', {'_id': ObjectId(employee_id)},
                      {'$set': {'number': new_number, 'telegram_id': 0}})
    text, buttons = helper.manage_employee(db, msg, employee_id=employee_id)
    await event.respond(msg.get('employee_saved') + ':\n\n' + text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'admin_delete_employee:*'))
async def admin_delete_employee(event):
    employee_id = event.data.decode().split(':')[1]
    async with bot.conversation(event.sender_id) as conv:
        db.delete('employee', {'_id': ObjectId(employee_id)})
        await conv.send_message(msg.get('employee_deleted'),
                                buttons=helper.get_main_menu_button(msg))
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
        # TODO check date exceptions
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
        insert_result = db.insert('task', task)
        page = 1
        checked_list = []
        text, buttons = helper.list_employees(db, msg, page=page,
                                              text=msg.get('task_saved') + '.\n\n' + msg.get('select_operators'),
                                              prefix='select_employee', list_prefix='page_employee')
        selection_message = await conv.send_message(text, buttons=buttons)
        while True:
            selection = await conv.wait_event(events.CallbackQuery())
            if selection.data.decode().startswith('select_employee'):
                employee_id = selection.data.decode().split(':')[1]
                if ObjectId(employee_id) in checked_list:
                    db.update('task', {'_id': ObjectId(insert_result.inserted_id)},
                              {'$pull': {'operators': {'id': ObjectId(employee_id)}}})
                    checked_list.remove(ObjectId(employee_id))
                else:
                    operator = {
                        'id': ObjectId(employee_id),
                        'status': 'assigned',
                        'comment': None,
                        'charge': 0
                    }
                    db.update('task', {'_id': ObjectId(insert_result.inserted_id)},
                              {'$push': {'operators': operator}})
                    checked_list.append(ObjectId(employee_id))
            elif selection.data.decode().startswith('page_employee'):
                page = selection.data.decode().split(':')[1]
            else:
                break
            text, buttons = helper.list_employees(db, msg, page=page, text=msg.get('select_operators'),
                                                  prefix='select_employee', checked=checked_list,
                                                  list_prefix='page_employee')
            text = msg.get('task_saved') + '.\n\n' + text + ': (' + str(len(checked_list)) + ')'
            await bot.edit_message(selection_message, text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'admin_edit_task:*'))
async def admin_edit_task(event):
    task_id = event.data.decode().split(':')[1]
    old_task_from_db = db.find('task', {'_id': ObjectId(task_id)})
    old_task = old_task_from_db.next()
    task = {}
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message(f"{msg.get('enter_task_title')}.\n{msg.get('ignore_entry')}")
        response_title = await conv.get_response()
        if response_title.text != '.':
            task['title'] = response_title.text
        await conv.send_message(f"{msg.get('enter_task_description')}.\n{msg.get('ignore_entry')}")
        response_description = await conv.get_response()
        if response_description.text != '.':
            task['description'] = response_description.text
        await conv.send_message(f"{msg.get('enter_task_start_date')}.\n{msg.get('ignore_entry')}")
        response_start_date = await conv.get_response()
        if response_start_date.text != '.':
            # TODO check date exceptions
            task['start_date'] = Persian(response_start_date.text).gregorian_datetime()
        await conv.send_message(f"{msg.get('enter_task_deadline')}.\n{msg.get('ignore_entry')}")
        response_deadline = await conv.get_response()
        if response_deadline.text != '.':
            task['deadline'] = Persian(response_deadline.text).gregorian_datetime()
        if len(task) > 0:
            db.update('task', {'_id': ObjectId(task_id)}, {'$set': task})
        page = 1
        full_checked_list = old_task.get('operators')
        checked_list = []
        for op in full_checked_list:
            checked_list.append(op.get('id'))
        text, buttons = helper.list_employees(db, msg, page=page, text=msg.get('select_operators'),
                                              prefix='select_employee', checked=checked_list,
                                              list_prefix='page_employee')
        text = msg.get('task_saved') + '.\n\n' + text + ': (' + str(len(checked_list)) + ')'
        selection_message = await conv.send_message(text, buttons=buttons)
        while True:
            selection = await conv.wait_event(events.CallbackQuery())
            if selection.data.decode().startswith('select_employee'):
                employee_id = selection.data.decode().split(':')[1]
                if ObjectId(employee_id) in checked_list:
                    db.update('task', {'_id': ObjectId(task_id)},
                              {'$pull': {'operators': {'id': ObjectId(employee_id)}}})
                    checked_list.remove(ObjectId(employee_id))
                else:
                    operator = {
                        'id': ObjectId(employee_id),
                        'status': 'assigned',
                        'comment': None,
                        'charge': 0
                    }
                    db.update('task', {'_id': ObjectId(task_id)},
                              {'$push': {'operators': operator}})
                    checked_list.append(ObjectId(employee_id))
            elif selection.data.decode().startswith('page_employee'):
                page = selection.data.decode().split(':')[1]
            else:
                break
            text, buttons = helper.list_employees(db, msg, page=page, text=msg.get('select_operators'),
                                                  prefix='select_employee', checked=checked_list,
                                                  list_prefix='page_employee')
            text = msg.get('task_saved') + '.\n\n' + text + ': (' + str(len(checked_list)) + ')'
            await bot.edit_message(selection_message, text, buttons=buttons)
    raise events.StopPropagation


@bot.on(events.CallbackQuery(pattern=b'admin_delete_task:*'))
async def admin_delete_task(event):
    task_id = event.data.decode().split(':')[1]
    async with bot.conversation(event.sender_id) as conv:
        db.delete('task', {'_id': ObjectId(task_id)})
        await conv.send_message(msg.get('task_deleted'),
                                buttons=helper.get_main_menu_button(msg))
    raise events.StopPropagation


# Connect to Telegram and run in a loop
try:
    print('bot starting...')
    bot.start(bot_token=config.bot_token)
    print('bot started')
    bot.run_until_disconnected()
finally:
    print('never runs!')
