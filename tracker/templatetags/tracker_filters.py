from django import template

register = template.Library()

@register.filter
def sum_attr(queryset, attr_name):
    """
    Sum the values of a specific attribute in a queryset
    Usage: {{ tenders|sum_attr:'total_value' }}
    """
    if not queryset:
        return 0
    try:
        return sum(getattr(item, attr_name, 0) for item in queryset if hasattr(item, attr_name))
    except (TypeError, ValueError):
        return 0

@register.filter
def filter_status(queryset, status):
    """
    Filter a queryset by status
    Usage: {{ tenders|filter_status:'Pending' }}
    """
    if not queryset:
        return []
    try:
        return [item for item in queryset if getattr(item, 'status', None) == status]
    except (TypeError, ValueError):
        return []