from django.urls import path

from .category_views import CategoryDetailView
from .views import (
    CategoryListCreateView,
    ExpenseDetailView,
    ExpenseListCreateView,
    ExpenseSummaryView,
    TotalExpenseView,
)

urlpatterns = [
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('expenses/', ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('expenses/total/', TotalExpenseView.as_view(), name='total-expenses'),
    path('expenses/summary/', ExpenseSummaryView.as_view(), name='expense-summary'),
    path('expenses/<int:pk>/', ExpenseDetailView.as_view(), name='expense-detail'),
]
