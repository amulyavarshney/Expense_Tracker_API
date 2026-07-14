from calendar import monthrange
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from django.utils.timezone import make_aware

from expenses.models import Expense


def get_period_date_range(period, reference_date=None):
    """Return inclusive calendar start/end dates for the current budget period."""
    today = reference_date or timezone.localdate()

    if period == 'weekly':
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    elif period == 'monthly':
        start = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        end = today.replace(day=last_day)
    elif period == 'yearly':
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)
    else:
        raise ValueError(f'Unknown period: {period}')

    return start, end


def get_category_spend_for_period(user, category, period, reference_date=None):
    start_date, end_date = get_period_date_range(period, reference_date)
    start_dt = make_aware(datetime.combine(start_date, time.min))
    end_dt = make_aware(datetime.combine(end_date, time.max))

    total = Expense.objects.filter(
        user=user,
        category=category,
        timestamp__gte=start_dt,
        timestamp__lte=end_dt,
    ).aggregate(total=Sum('amount'))['total']

    return total or Decimal('0')


def get_budget_usage(user, category, amount, period, reference_date=None):
    spent = get_category_spend_for_period(user, category, period, reference_date)
    remaining = amount - spent
    period_start, period_end = get_period_date_range(period, reference_date)

    return {
        'spent': spent,
        'remaining': remaining,
        'period_start': period_start,
        'period_end': period_end,
    }
