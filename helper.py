# TODO full text search

from telethon import Button
from bson.objectid import ObjectId


def get_start_admin_buttons(msg):
    return [
        [Button.inline(msg.get('start_keyboard_admin_employees'), b'admin_employees'),
         Button.inline(msg.get('admin_employees_keyboard_add_employee'), b'admin_add_employee')],
        [Button.inline(msg.get('start_keyboard_admin_tasks'), b'admin_tasks'),
         Button.inline(msg.get('new_task'), b'new_task')]
    ]


def get_start_user_buttons(msg):
    return [
        [Button.request_phone(msg.get('share_phone_number')),
         Button.inline(msg.get('new_task'), b'new_task')]
    ]


def get_main_menu_button(msg):
    return [Button.inline(msg.get('main_menu'), b'main_menu')]


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


def list_tasks(db, msg, text=None, page=1,
                   nav=None, prefix='manage_task', delimiter=":"):
    page_count = db.page_count('task')
    tasks = db.find('task', page=page, sort_by='start_date')
    keyboard, tmp_keyboard = [], []

    if not text:
        text = msg.get('start_keyboard_admin_tasks')
        text += '\n'
        text += msg.get('select_task')
        text += ':'

    for c, task in enumerate(tasks):
        tmp_keyboard.append(Button.inline(task.get('title'),
                                          str.encode(prefix + delimiter + str(task.get('_id')))))
        if c % 2 != 0:
            keyboard.append(tmp_keyboard)
            tmp_keyboard = []
    if len(tmp_keyboard) != 0:
        keyboard.append(tmp_keyboard)

    if not nav:
        nav = [
            Button.inline(msg.get('main_menu'), b'main_menu')
        ]
    buttons = paginate(msg,
                       current_page=page,
                       total_pages=page_count,
                       data_prefix='list_tasks',
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
        if c % 2 != 0:
            keyboard.append(tmp_keyboard)
            tmp_keyboard = []
    if len(tmp_keyboard) != 0:
        keyboard.append(tmp_keyboard)

    if not nav:
        nav = [
            Button.inline(msg.get('main_menu'), b'main_menu')
        ]
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
    text = f"{employee.get('name')}\n{employee_number}"
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


def manage_task(db, msg, task_id):
    tasks = db.find('task', {'_id': ObjectId(task_id)})
    task = tasks.next()
    text = f"{task.get('title')}\n{task.get('description')}\n" \
           f"{task.get('start_date')}\n{task.get('deadline')}"
    keyboard = [
        [Button.inline(msg.get('admin_tasks_keyboard_edit_task'),
                       str.encode('admin_edit_task:' + str(task_id))),
         Button.inline(msg.get('admin_tasks_keyboard_delete_task'),
                       str.encode('admin_delete_task:' + str(task_id)))],
        [Button.inline(msg.get('main_menu'), b'main_menu')]
    ]
    return text, keyboard
