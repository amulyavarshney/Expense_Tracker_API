from decimal import Decimal

from django.db.models import Q
from rest_framework import serializers

from expenses.models import Category

from .models import Budget
from .services import get_budget_usage


class BudgetSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='slug', queryset=Category.objects.none())
    category_name = serializers.CharField(source='category.name', read_only=True)
    spent = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    remaining = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    period_start = serializers.DateField(read_only=True)
    period_end = serializers.DateField(read_only=True)

    class Meta:
        model = Budget
        fields = [
            'id',
            'category',
            'category_name',
            'amount',
            'period',
            'spent',
            'remaining',
            'period_start',
            'period_end',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'category_name',
            'spent',
            'remaining',
            'period_start',
            'period_end',
            'created_at',
            'updated_at',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['category'].queryset = Category.objects.filter(
                Q(user__isnull=True) | Q(user=request.user)
            )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        category = attrs.get('category', getattr(self.instance, 'category', None))
        period = attrs.get('period', getattr(self.instance, 'period', None))

        if category and period:
            queryset = Budget.objects.filter(user=user, category=category, period=period)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    'You already have a budget for this category and period.'
                )

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        usage = get_budget_usage(
            instance.user,
            instance.category,
            instance.amount,
            instance.period,
        )
        data['spent'] = format(usage['spent'].quantize(Decimal('0.01')), 'f')
        data['remaining'] = format(usage['remaining'].quantize(Decimal('0.01')), 'f')
        data['period_start'] = usage['period_start']
        data['period_end'] = usage['period_end']
        return data
