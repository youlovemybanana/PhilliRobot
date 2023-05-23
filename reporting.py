from persian_calendar import Gregorian
from datetime import datetime


def welcome_admin(db, msg, config):
    welcome_msg = f"{msg.get('admin')}, {msg.get('start_welcome')}!\n\n"
    if config.module_employee:
        welcome_msg += f"{admin_overall_employee_report(db, msg)}\n\n"
    if config.module_task:
        welcome_msg += f"{admin_overall_task_report(db, msg)}\n\n"
    welcome_msg += f"{today(msg)}\n\n"
    return welcome_msg


def welcome_employee(msg, config, employee):
    welcome_msg = f"{employee.get('name')}, {msg.get('start_welcome')}!\n\n"
    welcome_msg += f"{today(msg)}\n\n"
    return welcome_msg


def today(msg):
    persian_date = Gregorian(datetime.now().date()).persian_string('{}/{}/{}')
    return f"{msg.get('today')}: {persian_date}"


def admin_overall_employee_report(db, msg):
    count_all_employee = db.count('employee')
    count_verified_employee = db.count('employee', {'telegram_id': {'$gt': 0}})
    return f"{msg.get('verified_employees')}: {count_verified_employee} " \
           f"{msg.get('from')} {count_all_employee}"


def admin_overall_task_report(db, msg):
    count_new_task = db.count('task', {'status': 'new'})
    count_ip_task = db.count('task', {'status': 'ip'})
    count_wfp_task = db.count('task', {'status': 'wfp'})
    count_po_task = db.count('task', {'status': 'po'})
    return f"{msg.get('count_new_task')}: {count_new_task}\n" \
           f"{msg.get('count_ip_task')}: {count_ip_task}\n" \
           f"{msg.get('count_wfp_task')}: {count_wfp_task}\n" \
           f"{msg.get('count_po_task')}: {count_po_task}"


def report_today(db, msg, config):
    if config.module_task:
        today_date = datetime.today().replace(minute=0, hour=0, second=0, microsecond=0)
        tasks = db.find('task', {'start_date': today_date})
        task_reminder = f"{today(msg)}\n\n" \
                        f"{msg.get('new_tasks_today')}:\n\n"
        for task in tasks:
            task_reminder += f"🔸 {task.get('title')}\n\n"
        tasks = db.find('task', {'status': 'ip'})
        task_reminder += f"{msg.get('ip_tasks_today')}:\n\n"
        for task in tasks:
            task_reminder += f"🔹 {task.get('title')}\n\n"
        return task_reminder

