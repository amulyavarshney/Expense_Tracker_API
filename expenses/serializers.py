from django.conf import settings
from django.db.models import Q
from django.utils.text import slugify
from rest_framework import serializers

from .models import Category, Expense


class CategorySerializer(serializers.ModelSerializer):
    is_system = serializers.BooleanField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'slug', 'name', 'is_system', 'created_at']
        read_only_fields = ['is_system', 'created_at']

    def validate_slug(self, value):
        user = self.context['request'].user
        if Category.objects.filter(user__isnull=True, slug=value).exists():
            raise serializers.ValidationError(
                'This slug is reserved by a system category.'
            )
        qs = Category.objects.filter(user=user, slug=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('You already have a category with this slug.')
        return value

    def validate_name(self, value):
        user = self.context['request'].user
        slug = self.initial_data.get('slug') or slugify(value)
        if Category.objects.filter(user__isnull=True, slug=slug).exists():
            raise serializers.ValidationError(
                'This name conflicts with a system category.'
            )
        qs = Category.objects.filter(user=user, slug=slug)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('You already have a category with this name.')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        if 'slug' not in validated_data:
            validated_data['slug'] = slugify(validated_data['name'])
        return Category.objects.create(user=user, **validated_data)


class ExpenseSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    category = serializers.SlugRelatedField(slug_field='slug', queryset=Category.objects.none())
    category_name = serializers.CharField(source='category.name', read_only=True)
    receipt = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Expense
        fields = [
            'id',
            'username',
            'category',
            'category_name',
            'amount',
            'currency',
            'description',
            'receipt',
            'timestamp',
        ]
        read_only_fields = ['username', 'category_name', 'timestamp']

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

    def validate_currency(self, value):
        if len(value) != 3 or not value.isalpha() or value != value.upper():
            raise serializers.ValidationError(
                'Currency must be a 3-letter uppercase ISO 4217 code (e.g. USD, EUR).'
            )
        return value

    def validate_receipt(self, value):
        if value and value.size > settings.MAX_RECEIPT_UPLOAD_SIZE:
            max_mb = settings.MAX_RECEIPT_UPLOAD_SIZE // (1024 * 1024)
            raise serializers.ValidationError(
                f'Receipt file size must not exceed {max_mb} MB.'
            )
        return value
