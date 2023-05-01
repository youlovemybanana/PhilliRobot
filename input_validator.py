def phone_number(n: str):
    if n.isdecimal() and n.startswith('0') and len(n) == 11:
        return '+98' + n[1:]
    elif n.isdecimal() and n.startswith('9') and len(n) == 10:
        return '+98' + n
    elif n.startswith('+98') and len(n) == 13:
        return n
    else:
        return 0

