import re
import time
from datetime import timedelta


def comma(amount):
    """
    Converts a string to a comma separated human readable form.
    """
    orig = amount
    new = re.sub("^(-?\d+)(\d{3})", '\g<1>,\g<2>', amount)
    if orig == new:
        return new
    else:
        return comma(new)

def human_time(ti):
    """
    Converts the epoch time to human readable time
    """
    return time.strftime("%d %b %Y %H:%M", time.localtime(float(ti)))

def humanize_time(secs):
    """
    Convert the seconds to hours and minutes
    """
    d = timedelta(seconds=int(secs))
    return str(d)

def convert_bytes(bytes):
    """
    Convert the bytes to human readable Kb, Mb, Gb or Tb format
    """
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fTb' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fGb' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fMb' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fKb' % kilobytes
    else:
        size = '%.2fB' % bytes
    return size

