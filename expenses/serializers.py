from rest_framework import serializers
from .models import Expense

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'user', 'category', 'amount', 'timestamp']
        read_only_fields = ['user', 'timestamp']
