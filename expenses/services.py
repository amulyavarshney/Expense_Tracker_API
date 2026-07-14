from django.db.models import Count, Sum

from .filters import apply_expense_filters
from .models import Expense


def get_user_expenses(user, query_params=None):
    queryset = Expense.objects.filter(user=user)
    if query_params:
        queryset = apply_expense_filters(queryset, query_params)
    return queryset


def get_total_expenses(user, query_params=None):
    queryset = get_user_expenses(user, query_params)
    return queryset.aggregate(total=Sum('amount'))['total'] or 0


def get_category_summary(user, query_params=None):
    queryset = get_user_expenses(user, query_params)
    return (
        queryset.values('category')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('category')
    )
