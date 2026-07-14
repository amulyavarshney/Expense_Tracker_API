from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import Expense
from .serializers import ExpenseSerializer
from .services import get_category_summary, get_total_expenses, get_user_expenses


class ExpenseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return get_user_expenses(self.request.user, self.request.query_params)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)


class TotalExpenseView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        total = get_total_expenses(request.user, request.query_params)
        return Response({'total_expenses': total})


class ExpenseSummaryView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        summary = get_category_summary(request.user, request.query_params)
        return Response({'by_category': list(summary)})
