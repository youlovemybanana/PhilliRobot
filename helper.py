# TODO full text search

from telethon import Button
from bson.objectid import ObjectId


def navigate(current_page=1, total_pages=1, data_prefix=None):
    # TODO fix bugs
    if data_prefix:
        data_prefix += '_'
        keyboard = [Button.inline('<<', str.encode(data_prefix + '1')),
                    Button.inline('<', str.encode(data_prefix + str(current_page - 1))),
                    Button.inline(str(current_page)),
                    Button.inline('>', str.encode(data_prefix + str(current_page + 1))),
                    Button.inline('>>', str.encode(data_prefix + str(total_pages)))]
        return keyboard
    else:
        return None


def paginate(current_page=1, total_pages=1, data_prefix=None, before=None, after=None):
    if data_prefix:
        paginator = navigate(current_page, total_pages, data_prefix)
        if before or after:
            paginator = [paginator]
        if before:
            paginator.insert(0, before)
        if after:
            paginator.append(after)
        return paginator
    else:
        return None


def list_employees(db, msg, text=None, page=1,
                   nav=None, prefix='manage_employee:'):
    page_count = db.page_count('employee')
    employees = db.find('employee', page=page)
    keyboard = []
    if not text:
        text = msg.get('start_keyboard_admin_employees')
        text += '\n'
        text += msg.get('select_employee')
        text += ':'
    for employee in employees:
        keyboard.append(Button.inline(employee.get('name'),
                                      str.encode(prefix + str(employee.get('_id')))))
    if not nav:
        nav = [
            Button.inline(msg.get('main_menu'), b'main_menu')
        ]
    buttons = paginate(current_page=page,
                       total_pages=page_count,
                       data_prefix='list_employees',
                       before=keyboard,
                       after=nav)
    return text, buttons


def manage_employee(db, msg, employee_id):
    employees = db.find('employee', {'_id': ObjectId(employee_id)})
    if employees:
        employee = employees.next()
    else:
        return None, None
    text = employee.get('name')
    keyboard = [
        [Button.inline(msg.get('admin_employees_keyboard_edit_employee'),
                       str.encode('admin_edit_employee:' + str(employee_id))),
         Button.inline(msg.get('admin_employees_keyboard_delete_employee'),
                       str.encode('admin_delete_employee:' + str(employee_id)))],
        [Button.inline(msg.get('main_menu'), b'main_menu')]
    ]
    return text, keyboard
