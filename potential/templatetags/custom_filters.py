from django import template

register = template.Library()

@register.filter
def dict_key(value, key):
    """
    Safely gets a value from a dictionary using the provided key.
    If the key doesn't exist, returns "N/A".
    """
    return value.get(key, "N/A")

@register.filter
def smart_round(value):
    """
    Rounds a value to 2 decimal places, but removes the decimal point if it's an integer.
    If the value cannot be converted to a float, it returns the original value unchanged.
    """
    try:
        value = round(float(value), 2)  # ✅ Always round to 2 decimal places
        return f"{value:.2f}".rstrip('0').rstrip('.')  # ✅ Ensure display correctness
    except (ValueError, TypeError):
        return value
    
@register.filter
def get_item(dictionary, key):
    """
    Custom template filter to get a value from a dictionary using a key.
    """
    return dictionary.get(key, "N/A")
