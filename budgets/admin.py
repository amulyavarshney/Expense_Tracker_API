from django.contrib import admin

from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'period', 'created_at']
    list_filter = ['period']
    search_fields = ['user__username', 'category__slug', 'category__name']
