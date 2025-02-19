from rest_framework import generics, permissions
from rest_framework.response import Response
from django.db import models  # Add this import
from .models import Expense
from .serializers import ExpenseSerializer
from django.utils.timezone import make_aware
from datetime import datetime

class ExpenseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Expense.objects.filter(user=user)
        
        category = self.request.query_params.get('category')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if category:
            queryset = queryset.filter(category=category)
        if start_date:
            start_date = make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            end_date = make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            queryset = queryset.filter(timestamp__lte=end_date)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TotalExpenseView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        queryset = Expense.objects.filter(user=user)
        
        if start_date:
            start_date = make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            end_date = make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            queryset = queryset.filter(timestamp__lte=end_date)

        total = queryset.aggregate(total_expenses=models.Sum('amount'))['total_expenses'] or 0

        return Response({'total_expenses': total})
