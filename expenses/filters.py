from datetime import datetime, time

from django.utils.timezone import make_aware
from rest_framework.exceptions import ValidationError


def _parse_date(value, param_name):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            {param_name: 'Invalid date format. Use YYYY-MM-DD.'}
        ) from exc


def apply_expense_filters(queryset, query_params):
    """Apply category and date filters shared by list, total, and summary views."""
    category = query_params.get('category')
    start_date = query_params.get('start_date')
    end_date = query_params.get('end_date')

    if category:
        queryset = queryset.filter(category__slug=category)

    if start_date:
        parsed = _parse_date(start_date, 'start_date')
        start_dt = make_aware(datetime.combine(parsed, time.min))
        queryset = queryset.filter(timestamp__gte=start_dt)

    if end_date:
        parsed = _parse_date(end_date, 'end_date')
        end_dt = make_aware(datetime.combine(parsed, time.max))
        queryset = queryset.filter(timestamp__lte=end_dt)

    currency = query_params.get('currency')
    if currency:
        queryset = queryset.filter(currency=currency.upper())

    return queryset
