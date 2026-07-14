from django.contrib import admin

from .models import Category, Expense


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'name', 'user', 'created_at')
    list_filter = ('user',)
    search_fields = ('slug', 'name', 'user__username')
    readonly_fields = ('created_at',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'amount', 'timestamp')
    list_filter = ('category', 'timestamp')
    search_fields = ('user__username', 'description', 'category__slug', 'category__name')
    readonly_fields = ('timestamp',)
