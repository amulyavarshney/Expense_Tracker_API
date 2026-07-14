from django.urls import path

from .views import (
    ExpenseDetailView,
    ExpenseListCreateView,
    ExpenseSummaryView,
    TotalExpenseView,
)

urlpatterns = [
    path('expenses/', ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('expenses/total/', TotalExpenseView.as_view(), name='total-expenses'),
    path('expenses/summary/', ExpenseSummaryView.as_view(), name='expense-summary'),
    path('expenses/<int:pk>/', ExpenseDetailView.as_view(), name='expense-detail'),
]
