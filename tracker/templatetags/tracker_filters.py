from django import template
register = template.Library()

@register.filter
def sum_attr(queryset, attr):
    """Sum an attribute across a queryset: e.g. tenders|sum_attr:'total_value'"""
    try:
        return sum(getattr(x, attr) for x in queryset)
    except (TypeError, AttributeError):
        return 0

@register.filter
def filter_status(queryset, status):
    """Filter queryset by payment_status"""
    return [x for x in queryset if getattr(x, 'payment_status', None) == status]

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)