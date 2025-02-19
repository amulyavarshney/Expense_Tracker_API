from django.urls import path
from .views import ExpenseListCreateView, TotalExpenseView

urlpatterns = [
    path('expenses/', ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('expenses/total/', TotalExpenseView.as_view(), name='total-expenses'),
]