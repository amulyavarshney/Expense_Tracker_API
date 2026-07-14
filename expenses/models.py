from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Category(models.Model):
    DEFAULT_CATEGORIES = [
        ('food', 'Food'),
        ('transport', 'Transport'),
        ('entertainment', 'Entertainment'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='categories',
        null=True,
        blank=True,
        help_text='Null for system-wide default categories.',
    )
    slug = models.SlugField(max_length=50)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['slug'],
                condition=Q(user__isnull=True),
                name='unique_system_category_slug',
            ),
            models.UniqueConstraint(
                fields=['user', 'slug'],
                condition=Q(user__isnull=False),
                name='unique_user_category_slug',
            ),
        ]

    def __str__(self):
        owner = self.user.username if self.user_id else 'system'
        return f'{owner}:{self.slug}'

    @property
    def is_system(self):
        return self.user_id is None


def receipt_upload_path(instance, filename):
    date = instance.timestamp if instance.timestamp else timezone.now()
    return date.strftime('receipts/%Y/%m/') + filename


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='expenses',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    description = models.TextField(blank=True, default='')
    receipt = models.FileField(upload_to=receipt_upload_path, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['user', 'category']),
        ]

    def __str__(self):
        return (
            f'{self.user.username} - {self.category.slug} - '
            f'{self.amount} - {self.timestamp}'
        )
