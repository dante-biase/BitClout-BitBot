import os
import sys
import re
import time
from functools import wraps


def time_it(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        return result, end - start

    return wrapper


def running_on_windows():
    return sys.platform == "win32"


def clear_console():
    os.system('cls' if running_on_windows() else 'clear')


def follows_pattern(blueprint, string):
    matches = re.match("\w+".join(blueprint), string.strip())
    return matches.group(1) if matches else None


def format_as_number(number, precision=2, roundn=False):
    if roundn:
        number = round(number, precision)
    return ("{:,." + str(precision) + "f}").format(number)


def format_as_usd(number, roundn=False):
    return "$" + format_as_number(number, precision=2, roundn=roundn)


def abbreviate_number(number, places):
    number = f"{float(number):,}"
    whole, decimals = number.split('.')
    if places >= len(decimals):
        return number
    else:
        return f"{whole}.{decimals[:places]}..."

def dict_has_path(d, key_path):
    if not d:
        return False
    elif not key_path:
        return True
    else:
        sub_i = d
        for key in key_path:
            try:
                sub_i = sub_i[key]
            except KeyError:
                return False
            except TypeError:
                return False

        return True
