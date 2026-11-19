import datetime


def total(prices, discount=0):
    s = sum(prices)
    if discount > 0:
        s = s - s * discount // 100
    return s


def label(n):
    if n == 1:
        return "1 item"
    return "%d items" % n


def deadline():
    """When an order must be confirmed: 5 seconds from now."""
    return datetime.datetime.now() + datetime.timedelta(seconds=5)
