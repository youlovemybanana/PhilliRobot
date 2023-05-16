from functools import wraps
from persian_calendar import Persian, Gregorian
from datetime import datetime


def standardize_input(i: str):
    i = i.strip()
    i = i.replace('۰', '0')
    i = i.replace('۱', '1')
    i = i.replace('۲', '2')
    i = i.replace('۳', '3')
    i = i.replace('۴', '4')
    i = i.replace('۵', '5')
    i = i.replace('۶', '6')
    i = i.replace('۷', '7')
    i = i.replace('۸', '8')
    i = i.replace('۹', '9')
    i = i.replace('٠', '0')
    i = i.replace('١', '1')
    i = i.replace('٢', '2')
    i = i.replace('٣', '3')
    i = i.replace('٤', '4')
    i = i.replace('٥', '5')
    i = i.replace('٦', '6')
    i = i.replace('٧', '7')
    i = i.replace('٨', '8')
    i = i.replace('٩', '9')
    return i


def persian_str_to_gregorian_date(d: str):
    try:
        d = standardize_input(d)
        if '/' in d:
            t = d.split('/')
        elif '\\' in d:
            t = d.split('\\')
        elif '-' in d:
            t = d.split('-')
        else:
            return None
        year = int(t[0])
        month = int(t[1])
        day = int(t[2])
        if day > year:
            day, year = year, day
        return Persian(year, month, day).gregorian_datetime()
    except:
        return None


def gregorian_date_to_persian_str(d: datetime):
    try:
        return Gregorian(d.date()).persian_string('{}/{}/{}')
    except:
        return None


def phone_number(n: str):  # TODO make sure no phone duplicates exist
    if n.isdecimal() and n.startswith('0') and len(n) == 11:
        return '+98' + n[1:]
    elif n.isdecimal() and n.startswith('9') and len(n) == 10:
        return '+98' + n
    elif n.startswith('+98') and len(n) == 13:
        return n
    elif n.startswith('+98') and len(n) == 16:
        return n.replace(' ', '')
    else:
        return 0


def event_access(db, config, admin_only=False):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            event = args[0]
            has_access = False
            if config.module_employee:
                if len(list(db.find('employee', {'telegram_id': event.sender_id}))) > 0:
                    if not admin_only:
                        has_access = True
            if event.sender_id in config.admin_list:
                has_access = True
            if has_access:
                return await func(*args, **kwargs)
        return wrapper
    return decorator
