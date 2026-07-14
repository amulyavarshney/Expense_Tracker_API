from django.contrib.auth.models import User
from django.db import models

from expenses.models import Category


class Budget(models.Model):
    class Period(models.TextChoices):
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='budgets',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=10, choices=Period.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__slug', 'period']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'period'],
                name='unique_user_category_period_budget',
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'period']),
        ]

    def __str__(self):
        return (
            f'{self.user.username} - {self.category.slug} - '
            f'{self.period} - {self.amount}'
        )
