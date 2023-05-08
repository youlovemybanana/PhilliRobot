from functools import wraps


def phone_number(n: str):  # TODO make sure no phone duplicates exist
    if n.isdecimal() and n.startswith('0') and len(n) == 11:
        return '+98' + n[1:]
    elif n.isdecimal() and n.startswith('9') and len(n) == 10:
        return '+98' + n
    elif n.startswith('+98') and len(n) == 13:
        return n
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