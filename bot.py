from telethon import TelegramClient, events
from telethon.tl.types import PeerUser
from env import env
from mongo import Mongo
import polib
import helper
from bson.objectid import ObjectId
import auth
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


@bot.on(events.NewMessage(pattern='/start', incoming=True))
@bot.on(events.CallbackQuery(data=b'main_menu'))
async def start(event):
    if event.sender_id in config.admin_list:
        welcome_msg = reporting.welcome_admin(db, msg, config)
        k_admin = helper.get_start_admin_buttons(msg, config)
        await event.respond(welcome_msg, buttons=k_admin)
    else:
        k_user = []
        welcome_msg = f"{msg.get('start_welcome')}! {msg.get('start_id')}: {event.sender_id}"
        if config.module_employee:
            employee = list(db.find('employee', {'telegram_id': event.sender_id}))
            if len(employee) > 0:
                welcome_msg = reporting.welcome_employee(msg, config, employee[0])
                k_user = helper.get_start_user_buttons(msg, config, employee[0].get('_id'))
            else:
                k_user = helper.get_start_user_buttons(msg, config)
        await event.respond(welcome_msg, buttons=k_user)
    raise events.StopPropagation

if config.module_employee:
    @bot.on(events.CallbackQuery(data=b'admin_employees'))
    @auth.event_access(db, config, admin_only=True)
    async def admin_employees(event):
        text, buttons = helper.list_employees(db, msg)
        await event.respond(text, buttons=buttons)
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(data=b'admin_add_employee'))
    @auth.event_access(db, config, admin_only=True)
    async def admin_add_employee(event):
        async with bot.conversation(event.sender_id) as conv:
            await conv.send_message(msg.get('enter_employee_name'))
            response_name = await conv.get_response()
            name = response_name.text
            await conv.send_message(msg.get('enter_employee_number'))
            response_number = await conv.get_response()
            number = auth.phone_number(response_number.text)
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

    @bot.on(events.CallbackQuery(pattern=b'admin_edit_employee:*'))
    @auth.event_access(db, config, admin_only=True)
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
                new_number = auth.phone_number(response_number.text)
                db.update('employee', {'_id': ObjectId(employee_id)},
                          {'$set': {'number': new_number, 'telegram_id': 0}})
        text, buttons = helper.manage_employee(db, msg, employee_id=employee_id)
        await event.respond(msg.get('employee_saved') + ':\n\n' + text, buttons=buttons)
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(pattern=b'admin_delete_employee:*'))
    @auth.event_access(db, config, admin_only=True)
    async def admin_delete_employee(event):
        employee_id = event.data.decode().split(':')[1]
        async with bot.conversation(event.sender_id) as conv:
            db.delete('employee', {'_id': ObjectId(employee_id)})
            await conv.send_message(msg.get('employee_deleted'),
                                    buttons=helper.get_main_menu_button(msg))
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(pattern=b'list_employees:*'))
    @auth.event_access(db, config, admin_only=True)
    async def list_employees(event):
        page = event.data.decode().split(':')[1]
        text, buttons = helper.list_employees(db, msg, page=page)
        await event.respond(text, buttons=buttons)
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(pattern=b'manage_employee:*'))
    @auth.event_access(db, config, admin_only=True)
    async def manage_employee(event):
        employee_id = event.data.decode().split(':')[1]
        text, buttons = helper.manage_employee(db, msg, employee_id=employee_id)
        await event.respond(text, buttons=buttons)
        raise events.StopPropagation

    @bot.on(events.NewMessage(incoming=True, forwards=False, func=lambda e: e.message.media))
    async def check_phone_number(event):
        print(event.message)
        if type(event.message.peer_id) == PeerUser:
            if event.message.media.phone_number and event.message.media.user_id:
                if event.message.peer_id.user_id == event.message.media.user_id:
                    phone_number = event.message.media.phone_number
                    if not phone_number.startswith('+'):
                        phone_number = '+' + phone_number
                    res = db.update('employee', {'number': phone_number},
                                    {'$set': {'telegram_id': event.message.media.user_id}})
                    if res.matched_count > 0:
                        await event.respond(msg.get('account_auth_successful'),
                                            buttons=helper.get_clear_button())
                    else:
                        await event.respond(msg.get('account_auth_failed'),
                                            buttons=helper.get_main_menu_button(msg))

if config.module_task:
    @bot.on(events.CallbackQuery(data=b'admin_tasks'))
    @auth.event_access(db, config, admin_only=True)
    async def admin_tasks(event):
        text, buttons = helper.list_tasks(db, msg)
        await event.respond(text, buttons=buttons)
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(pattern=b'list_tasks:*'))
    @auth.event_access(db, config)
    async def list_tasks(event):
        page, status, employee_id = None, None, None
        split = event.data.decode().split(':')
        prefix = 'admin_manage_task'
        if len(split) == 2:
            if event.sender_id not in config.admin_list:
                return
            page = split[1]
        elif len(split) == 3:
            if event.sender_id not in config.admin_list:
                return
            status = split[1]
            page = split[2]
        elif len(split) == 4:
            status = split[1]
            employee_id = split[2]
            page = split[3]
            if event.sender_id not in config.admin_list:
                employee = db.find('employee', {'telegram_id': event.sender_id}).next()
                if employee.get('_id') != ObjectId(employee_id):
                    return
            prefix = 'manage_task'
        else:
            return
        text, buttons = helper.list_tasks(db, msg, page=page, prefix=prefix,
                                          status=status, employee=employee_id)
        await event.respond(text, buttons=buttons)
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(pattern=b'admin_manage_task:*'))
    @auth.event_access(db, config, admin_only=True)
    async def admin_manage_task(event):
        task_id = event.data.decode().split(':')[1]
        text, buttons = helper.manage_task(db, msg, task_id=task_id)
        await event.respond(text, buttons=buttons)
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(pattern=b'manage_task:*'))
    @auth.event_access(db, config)
    async def manage_task(event):
        task_id = event.data.decode().split(':')[1]
        employee = db.find('employee', {'telegram_id': event.sender_id}).next()
        text, buttons = helper.manage_task(db, msg, task_id=task_id,
                                           employee_id=employee.get('_id'))
        await event.respond(text, buttons=buttons)
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(data=b'new_task'))
    @auth.event_access(db, config)
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
            start_date = auth.persian_str_to_gregorian_date(response_start_date.text)
            await conv.send_message(msg.get('enter_task_deadline'))
            response_deadline = await conv.get_response()
            deadline = auth.persian_str_to_gregorian_date(response_deadline.text)
            task = {
                'title': title,
                'description': description,
                'start_date': start_date,
                'deadline': deadline,
                'operators': [],
                'status': 'new',
                'creator': event.sender_id
            }
            insert_result = db.insert('task', task)
            page = 1
            checked_list = []
            if event.sender_id not in config.admin_list:
                employee = db.find('employee', {'telegram_id': event.sender_id}).next()
                checked_list.append(employee.get('_id'))
                operator = {
                    'id': ObjectId(employee.get('_id')),
                    'status': 'new',
                    'comment': None,
                    'charge': 0
                }
                db.update('task', {'_id': ObjectId(insert_result.inserted_id)},
                          {'$push': {'operators': operator}})
            text, buttons = helper.list_employees(db, msg, page=page,
                                                  text=msg.get('select_operators'),
                                                  prefix='select_employee', list_prefix='page_employee',
                                                  checked=checked_list)
            text = msg.get('task_saved') + '.\n\n' + text + ': (' + str(len(checked_list)) + ')'
            selection_message = await conv.send_message(text, buttons=buttons)
            while True:
                selection = await conv.wait_event(events.CallbackQuery())
                if selection.data.decode().startswith('select_employee'):
                    employee_id = selection.data.decode().split(':')[1]
                    if ObjectId(employee_id) in checked_list:
                        db.update('task', {'_id': ObjectId(insert_result.inserted_id)},
                                  {'$pull': {'operators': {'id': ObjectId(employee_id)}}})
                        employee = db.find('employee', {'_id': ObjectId(employee_id)}).next()
                        if employee.get('telegram_id') and int(employee.get('telegram_id')) > 0:
                            await bot.send_message(int(employee.get('telegram_id')),
                                                   msg.get('task_unassigned') + '.\n\n' +
                                                   msg.get('title') + ': ' + title + '\n\n' +
                                                   msg.get('description') + ': ' + description + '\n\n' +
                                                   msg.get('start_date') + ': ' +
                                                   auth.gregorian_date_to_persian_str(start_date) +
                                                   '\n\n' + msg.get('deadline') + ': ' +
                                                   auth.gregorian_date_to_persian_str(deadline),
                                                   buttons=helper.get_main_menu_button(msg))
                        checked_list.remove(ObjectId(employee_id))
                    else:
                        operator = {
                            'id': ObjectId(employee_id),
                            'status': 'new',
                            'comment': None,
                            'charge': 0
                        }
                        db.update('task', {'_id': ObjectId(insert_result.inserted_id)},
                                  {'$push': {'operators': operator}})
                        employee = db.find('employee', {'_id': ObjectId(employee_id)}).next()
                        if employee.get('telegram_id') and int(employee.get('telegram_id')) > 0:
                            await bot.send_message(int(employee.get('telegram_id')),
                                                   msg.get('task_assigned') + ': ' + title)
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
    @auth.event_access(db, config, admin_only=True)
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
                task['start_date'] = auth.persian_str_to_gregorian_date(response_start_date.text)
            await conv.send_message(f"{msg.get('enter_task_deadline')}.\n{msg.get('ignore_entry')}")
            response_deadline = await conv.get_response()
            if response_deadline.text != '.':
                task['deadline'] = auth.persian_str_to_gregorian_date(response_deadline.text)
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
                        employee = db.find('employee', {'_id': ObjectId(employee_id)}).next()
                        if employee.get('telegram_id') and int(employee.get('telegram_id')) > 0:
                            await bot.send_message(int(employee.get('telegram_id')),
                                                   msg.get('task_unassigned') + ': ' + response_title.text)
                        checked_list.remove(ObjectId(employee_id))
                    else:
                        operator = {
                            'id': ObjectId(employee_id),
                            'status': 'new',
                            'comment': None,
                            'charge': 0
                        }
                        db.update('task', {'_id': ObjectId(task_id)},
                                  {'$push': {'operators': operator}})
                        employee = db.find('employee', {'_id': ObjectId(employee_id)}).next()
                        if employee.get('telegram_id') and int(employee.get('telegram_id')) > 0:
                            await bot.send_message(int(employee.get('telegram_id')),
                                                   msg.get('task_assigned') + ': ' + response_title.text)
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

    @bot.on(events.CallbackQuery(pattern=b'edit_task:*'))
    @auth.event_access(db, config)
    async def edit_task(event):
        task_id = event.data.decode().split(':')[1]
        old_task = db.find('task', {'_id': ObjectId(task_id)}).next()
        operators = old_task.get('operators')
        is_new = True
        for op in operators:
            if op.get('status') != 'new':
                is_new = False
        if is_new:
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
                    task['start_date'] = auth.persian_str_to_gregorian_date(response_start_date.text)
                await conv.send_message(f"{msg.get('enter_task_deadline')}.\n{msg.get('ignore_entry')}")
                response_deadline = await conv.get_response()
                if response_deadline.text != '.':
                    task['deadline'] = auth.persian_str_to_gregorian_date(response_deadline.text)
                if len(task) > 0:
                    db.update('task', {'_id': ObjectId(task_id)}, {'$set': task})
                await conv.send_message(msg.get('task_saved'), buttons=helper.get_main_menu_button(msg))
        else:
            await bot.send_message(event.sender_id, msg.get('you_can_only_edit_new_tasks'),
                                   buttons=helper.get_main_menu_button(msg))
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(pattern=b'admin_delete_task:*'))
    @auth.event_access(db, config, admin_only=True)
    async def admin_delete_task(event):
        task_id = event.data.decode().split(':')[1]
        async with bot.conversation(event.sender_id) as conv:
            db.delete('task', {'_id': ObjectId(task_id)})
            await conv.send_message(msg.get('task_deleted'),
                                    buttons=helper.get_main_menu_button(msg))
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(pattern=b'admin_mark_task_po:*'))
    @auth.event_access(db, config, admin_only=True)
    async def admin_mark_task_po(event):
        task_id = event.data.decode().split(':')[1]
        db.update('task', {'_id': ObjectId(task_id)},
                  {'$set': {'status': 'po'}})
        await bot.send_message(event.sender_id, msg.get('task_marked_paid_off'),
                               buttons=helper.get_main_menu_button(msg))
        raise events.StopPropagation


    @bot.on(events.CallbackQuery(pattern=b'mark_task_ip:*'))
    @auth.event_access(db, config)
    async def mark_task_ip(event):
        task_id = event.data.decode().split(':')[1]
        employee = db.find('employee', {'telegram_id': event.sender_id}).next()
        task = db.find('task', {'_id': ObjectId(task_id)}).next()
        operators = task.get('operators')
        # is_any_new_left = False
        for op in operators:
            if employee.get('_id') == op.get('id') and op.get('status') == 'new':
                op['status'] = 'ip'
                db.update('task', {'_id': ObjectId(task_id)},
                          {'$set': {'operators': operators}})
                await bot.send_message(event.sender_id, msg.get('task_marked_in_progress'),
                                       buttons=helper.get_main_menu_button(msg))
            # if op.get('status') == 'new':
            #     is_any_new_left = True
            # (not is_any_new_left and)
        if not task.get('status') == 'wfp' and not task.get('status') == 'po':
            db.update('task', {'_id': ObjectId(task_id)},
                      {'$set': {'status': 'ip'}})
        raise events.StopPropagation

    @bot.on(events.CallbackQuery(pattern=b'mark_task_wfp:*'))
    @auth.event_access(db, config)
    async def mark_task_wfp(event):
        task_id = event.data.decode().split(':')[1]
        employee = db.find('employee', {'telegram_id': event.sender_id}).next()
        task = db.find('task', {'_id': ObjectId(task_id)}).next()
        operators = task.get('operators')
        is_any_ip_or_new_left = False
        for op in operators:
            if employee.get('_id') == op.get('id') and op.get('status') == 'ip':
                op['status'] = 'wfp'
                async with bot.conversation(event.sender_id) as conv:
                    await conv.send_message(msg.get('enter_task_comment'))
                    response_comment = await conv.get_response()
                    op['comment'] = response_comment.text
                    await conv.send_message(msg.get('enter_task_payment_offer'))
                    response_payment_offer = await conv.get_response()
                    try:
                        op['charge'] = int(auth.standardize_input(response_payment_offer.text))
                    except:
                        op['charge'] = 0
                    db.update('task', {'_id': ObjectId(task_id)},
                              {'$set': {'operators': operators}})
                    await conv.send_message(msg.get('task_marked_waiting_for_payment'),
                                            buttons=helper.get_main_menu_button(msg))
            if op.get('status') == 'ip' or op.get('status') == 'new':
                is_any_ip_or_new_left = True
        if not is_any_ip_or_new_left and not task.get('status') == 'po':
            db.update('task', {'_id': ObjectId(task_id)},
                      {'$set': {'status': 'wfp'}})
        raise events.StopPropagation


# Connect to Telegram and run in a loop
try:
    print('bot starting...')
    bot.start(bot_token=config.bot_token)
    print('bot started')
    bot.run_until_disconnected()
finally:
    print('never runs in async mode!')
