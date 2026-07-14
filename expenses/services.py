from django.db.models import Count, Sum

from .filters import apply_expense_filters
from .models import Expense


def get_user_expenses(user, query_params=None):
    queryset = Expense.objects.filter(user=user).select_related('category')
    if query_params:
        queryset = apply_expense_filters(queryset, query_params)
    return queryset


def _category_rows(queryset):
    return (
        queryset.values('category__slug', 'category__name')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('category__slug')
    )


def _format_category_rows(rows):
    return [
        {
            'category': item['category__slug'],
            'category_name': item['category__name'],
            'total': item['total'],
            'count': item['count'],
        }
        for item in rows
    ]


def _distinct_currencies(queryset):
    return list(
        queryset.order_by('currency').values_list('currency', flat=True).distinct()
    )


def get_total_expenses(user, query_params=None):
    queryset = get_user_expenses(user, query_params)
    by_currency = list(
        queryset.values('currency')
        .annotate(total=Sum('amount'))
        .order_by('currency')
    )

    if len(by_currency) <= 1:
        if by_currency:
            return {
                'total_expenses': by_currency[0]['total'] or 0,
                'currency': by_currency[0]['currency'],
            }
        return {'total_expenses': 0, 'currency': 'USD'}

    return {
        'by_currency': [
            {'currency': item['currency'], 'total': item['total'] or 0}
            for item in by_currency
        ]
    }


def get_category_summary(user, query_params=None):
    queryset = get_user_expenses(user, query_params)
    currencies = _distinct_currencies(queryset)

    if len(currencies) <= 1:
        currency = currencies[0] if currencies else 'USD'
        return {
            'currency': currency,
            'by_category': _format_category_rows(_category_rows(queryset)),
        }

    by_currency = []
    for currency in sorted(currencies):
        currency_qs = queryset.filter(currency=currency)
        by_currency.append(
            {
                'currency': currency,
                'by_category': _format_category_rows(_category_rows(currency_qs)),
            }
        )
    return {'by_currency': by_currency}
