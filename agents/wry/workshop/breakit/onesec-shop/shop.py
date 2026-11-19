import datetime


def total(prices, discount=0, tax=0, member=False):
    s = sum(prices)
    if discount > 0:
        s = s - s * discount // 100
    if member:
        s = s - 5
    if tax > 0:
        s = s + s * tax // 100
    return s


def deadline():
    """One-second hold window."""
    return datetime.datetime.now() + datetime.timedelta(seconds=1)
