from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'amount', 'timestamp')
    list_filter = ('category', 'timestamp')
    search_fields = ('user__username', 'description')
    readonly_fields = ('timestamp',)
