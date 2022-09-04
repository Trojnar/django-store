from django import template

register = template.Library()


@register.filter(name="zip")
def zip_lists(a, b):
    return zip(a, b)


@register.filter(name="decimal_separator")
def decimal_separator(price):
    price_str = str(price)
    if len(price_str) < 3:
        for i in range(3 - len(price_str)):
            price_str = "0" + price_str
    return price_str[:-2] + "," + price_str[-2:]


@register.filter(name="every")
def every(num, val):
    return num % val == 0
