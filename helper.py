# TODO full text search

from telethon import Button
from bson.objectid import ObjectId
import auth


def get_start_admin_buttons(msg, config):
    k_admin = []
    if config.module_employee:
        k_admin.append([Button.inline(msg.get('admin_employees_keyboard_add_employee'), b'admin_add_employee')])
        k_admin.append([Button.inline(msg.get('start_keyboard_admin_employees'), b'admin_employees')])
    if config.module_task:
        k_admin.append([Button.inline(msg.get('new_task'), b'new_task')])
        k_admin.append([Button.inline(msg.get('new_tasks'), b'list_tasks:new:1')])
        k_admin.append([Button.inline(msg.get('in_progress_tasks'), b'list_tasks:ip:1')])
        k_admin.append([Button.inline(msg.get('waiting_for_payment_tasks'), b'list_tasks:wfp:1')])
        k_admin.append([Button.inline(msg.get('paid_off_tasks'), b'list_tasks:po:1')])
    return k_admin


def get_start_user_buttons(msg, config, employee_id=None):
    k_user = []
    if config.module_employee:
        if not employee_id:
            k_user.append(Button.request_phone(msg.get('share_phone_number')))
    if config.module_task:
        if employee_id:
            k_user.append([Button.inline(msg.get('new_task'), b'new_task')])
            k_user.append([Button.inline(msg.get('new_tasks'),
                                         str.encode('list_tasks:new:' + str(employee_id) + ':1'))])
            k_user.append([Button.inline(msg.get('in_progress_tasks'),
                                         str.encode('list_tasks:ip:' + str(employee_id) + ':1'))])
            k_user.append([Button.inline(msg.get('waiting_for_payment_tasks'),
                                         str.encode('list_tasks:wfp:' + str(employee_id) + ':1'))])
            k_user.append([Button.inline(msg.get('paid_off_tasks'),
                                         str.encode('list_tasks:po:' + str(employee_id) + ':1'))])
    if len(k_user) == 0:
        return None
    else:
        return k_user


def get_main_menu_button(msg):
    return [Button.inline(msg.get('main_menu'), b'main_menu')]


def get_clear_button():
    return Button.clear()


def navigate(msg, current_page=1, total_pages=1, data_prefix=None, delimiter=':',
             mode='a'):
    current_page = int(current_page)
    total_pages = int(total_pages)
    if data_prefix:
        data_prefix += delimiter
        keyboard = []
        if mode == 'a':
            if total_pages > current_page + 1:
                keyboard.append(Button.inline(msg.get('last'), str.encode(data_prefix + str(total_pages))))
            if total_pages > current_page:
                keyboard.append(Button.inline(msg.get('next'), str.encode(data_prefix + str(current_page + 1))))
            if total_pages > 1:
                keyboard.append(Button.inline(str(current_page) + ' ' + msg.get('from') + ' ' + str(total_pages)))
            if current_page > 1:
                keyboard.append(Button.inline(msg.get('previous'), str.encode(data_prefix + str(current_page - 1))))
            if current_page > 2:
                keyboard.append(Button.inline(msg.get('first'), str.encode(data_prefix + '1')))
        return keyboard
    else:
        return None


def paginate(msg, current_page=1, total_pages=1, data_prefix=None, delimiter=':',
             before=None, after=None):
    if data_prefix:
        paginator = navigate(msg, current_page, total_pages, data_prefix, delimiter)
        if before or after:
            paginator = [paginator]
        if before:
            paginator = before + paginator
        if after:
            paginator.append(after)
        return paginator
    else:
        return None


def list_tasks(db, msg, text=None, page=1, nav=None,
               prefix='admin_manage_task', list_prefix='list_tasks', delimiter=':',
               status=None, employee=None):
    q = {}
    if status:
        if employee:
            # employee = db.find('employee', {'_id': employee}).next()
            # q['$or'] = [{'operators': {'id': ObjectId(employee)}}, {'creator': employee.get('telegram_id')}]
            if status == 'po':
                q['status'] = status
                list_prefix += ':' + status
                q['operators.id'] = ObjectId(employee)
                list_prefix += ':' + str(employee)
            else:
                q['operators'] = {"$elemMatch": {"status": status, "id": ObjectId(employee)}}
                q['status'] = {"$ne": "po"}
                list_prefix += ':' + status
                list_prefix += ':' + str(employee)
        else:
            q['status'] = status
            list_prefix += ':' + status
    page_count = db.page_count('task', query=q)
    tasks = db.find('task', query=q, page=page, sort_by='start_date')
    keyboard, tmp_keyboard = [], []

    if not text:
        text = msg.get('start_keyboard_admin_tasks')
        text += '\n'
        text += msg.get('select_task')
        text += ':'

    for c, task in enumerate(tasks):
        tmp_keyboard.append(Button.inline(task.get('title'),
                                          str.encode(prefix + delimiter + str(task.get('_id')))))
        if True:  # c % 2 != 0:
            keyboard.append(tmp_keyboard)
            tmp_keyboard = []

    if len(tmp_keyboard) != 0:
        keyboard.append(tmp_keyboard)

    if not nav:
        nav = get_main_menu_button(msg)

    buttons = paginate(msg,
                       current_page=page,
                       total_pages=page_count,
                       data_prefix=list_prefix,
                       before=keyboard,
                       after=nav,
                       delimiter=delimiter)
    return text, buttons


def list_employees(db, msg, text=None, page=1, checked=None,
                   nav=None, prefix='manage_employee', list_prefix='list_employees',
                   delimiter=':'):
    if not checked:
        checked = []
    page_count = db.page_count('employee')
    employees = db.find('employee', page=page)
    keyboard, tmp_keyboard = [], []
    if not text:
        text = msg.get('start_keyboard_admin_employees')
        text += '\n'
        text += msg.get('select_employee')
        text += ':'

    for c, employee in enumerate(employees):
        if employee.get('_id') in checked:
            name = '✅ ' + employee.get('name') + ' ✅'
        else:
            name = employee.get('name')
        tmp_keyboard.append(Button.inline(name, str.encode(prefix + delimiter + str(employee.get('_id')))))
        if True:  # c % 2 != 0:
            keyboard.append(tmp_keyboard)
            tmp_keyboard = []

    if len(tmp_keyboard) != 0:
        keyboard.append(tmp_keyboard)

    if not nav:
        nav = get_main_menu_button(msg)

    buttons = paginate(msg,
                       current_page=page,
                       total_pages=page_count,
                       data_prefix=list_prefix,
                       before=keyboard,
                       after=nav,
                       delimiter=delimiter)
    return text, buttons


def manage_employee(db, msg, employee_id):
    employees = db.find('employee', {'_id': ObjectId(employee_id)})
    employee = employees.next()
    if int(employee.get('number')) == 0:
        employee_number = '+98----------'
    else:
        employee_number = employee.get('number')
    if employee.get('telegram_id') and int(employee.get('telegram_id')) > 0:
        employee_status = msg.get('verified')
    else:
        employee_status = msg.get('not_verified')
    text = f"{msg.get('employee_name')}: {employee.get('name')}\n\n" \
           f"{msg.get('number')}: {employee_number}\n\n" \
           f"{msg.get('status')}: {employee_status}"
    keyboard = [
        [Button.inline(msg.get('admin_employees_keyboard_edit_employee'),
                       str.encode('admin_edit_employee:' + str(employee_id))),
         Button.inline(msg.get('admin_employees_keyboard_delete_employee'),
                       str.encode('admin_delete_employee:' + str(employee_id)))],
        [Button.inline(msg.get('start_keyboard_admin_employees'), b'admin_employees'),
         Button.inline(msg.get('admin_employees_keyboard_add_employee'), b'admin_add_employee')],
        [Button.inline(msg.get('main_menu'), b'main_menu')]
    ]
    return text, keyboard


def manage_task(db, msg, task_id, employee_id=None):
    tasks = db.find('task', {'_id': ObjectId(task_id)})
    task = tasks.next()
    employee_task_status = None
    operators = ''
    is_new = True
    for op in task.get('operators'):
        employee = db.find('employee', {'_id': op.get('id')}).next()
        operators += '🔹 ' + employee.get('name') + ' - ' + msg.get(op.get('status'))
        if op.get('status') == 'wfp' and (employee_id == op.get('id') or not employee_id):
            operators += ' - ' + op.get('comment') + ' - ' + \
                         msg.get('payment_offer') + ': ' + str(op.get('charge'))
        operators += '\n'
        if op.get('status') != 'new':
            is_new = False
        if employee_id == op.get('id'):
            employee_task_status = op.get('status')
    start_date_persian = auth.gregorian_date_to_persian_str(task.get('start_date'))
    deadline_persian = auth.gregorian_date_to_persian_str(task.get('deadline'))
    text = f"{msg.get('title')}: {task.get('title')}\n\n" \
           f"{msg.get('description')}: {task.get('description')}\n\n" \
           f"{msg.get('start_date')}: {start_date_persian}\n" \
           f"{msg.get('deadline')}: {deadline_persian}\n\n" \
           f"{msg.get('operators')}:\n{operators}"
    if not employee_id:
        keyboard = [[Button.inline(msg.get('admin_tasks_keyboard_edit_task'),
                                   str.encode('admin_edit_task:' + str(task_id))),
                     Button.inline(msg.get('admin_tasks_keyboard_delete_task'),
                                   str.encode('admin_delete_task:' + str(task_id)))]]
        if task.get('status') == 'wfp':
            keyboard.append([Button.inline(msg.get('keyboard_mark_po'),
                             str.encode('admin_mark_task_po:' + str(task_id)))])
        keyboard.append([Button.inline(msg.get('main_menu'), b'main_menu')])
    else:
        if employee_task_status == 'new':
            keyboard = [[Button.inline(msg.get('keyboard_mark_ip'),
                                       str.encode('mark_task_ip:' + str(task_id)))]]
            if is_new:
                keyboard.append([Button.inline(msg.get('admin_tasks_keyboard_edit_task'),
                                 str.encode('edit_task:' + str(task_id)))])
            keyboard.append([Button.inline(msg.get('main_menu'), b'main_menu')])
        elif employee_task_status == 'ip':
            keyboard = [
                [Button.inline(msg.get('keyboard_mark_wfp'),
                               str.encode('mark_task_wfp:' + str(task_id)))],
                [Button.inline(msg.get('main_menu'), b'main_menu')]]
        else:
            keyboard = get_main_menu_button(msg)
    return text, keyboard
