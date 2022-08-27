from django import template

register = template.Library()


@register.filter(name="zip")
def zip_lists(a, b):
    return zip(a, b)


@register.filter(name="decimal_separator")
def decimal_separator(price):
    price_str = str(price)
    return price_str[:-2] + "," + price_str[-2:]
