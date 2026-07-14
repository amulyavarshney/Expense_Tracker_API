from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from expenses.models import Expense


class AuthTests(APITestCase):
    def test_register_creates_user(self):
        response = self.client.post(
            reverse('auth-register'),
            {'username': 'alice', 'email': 'alice@example.com', 'password': 'securepass1'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='alice').exists())

    def test_token_obtain_pair(self):
        User.objects.create_user(username='bob', password='securepass1')
        response = self.client.post(
            reverse('token-obtain-pair'),
            {'username': 'bob', 'password': 'securepass1'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_refresh(self):
        User.objects.create_user(username='carol', password='securepass1')
        token_response = self.client.post(
            reverse('token-obtain-pair'),
            {'username': 'carol', 'password': 'securepass1'},
            format='json',
        )
        response = self.client.post(
            reverse('token-refresh'),
            {'refresh': token_response.data['refresh']},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_unauthenticated_expense_list_returns_401(self):
        response = self.client.get(reverse('expense-list-create'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ExpenseCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='securepass1')
        self.other_user = User.objects.create_user(username='other', password='securepass1')
        self.client.force_authenticate(user=self.user)

    def test_create_expense(self):
        response = self.client.post(
            reverse('expense-list-create'),
            {'category': 'food', 'amount': '25.50', 'description': 'Lunch'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'tester')
        self.assertEqual(response.data['description'], 'Lunch')
        self.assertNotIn('user', response.data)

    def test_negative_amount_rejected(self):
        response = self.client.post(
            reverse('expense-list-create'),
            {'category': 'food', 'amount': '-5.00'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_expenses_paginated(self):
        Expense.objects.create(user=self.user, category='food', amount=Decimal('10.00'))
        Expense.objects.create(user=self.user, category='transport', amount=Decimal('20.00'))
        Expense.objects.create(user=self.other_user, category='food', amount=Decimal('99.00'))

        response = self.client.get(reverse('expense-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_retrieve_expense(self):
        expense = Expense.objects.create(user=self.user, category='food', amount=Decimal('15.00'))
        response = self.client.get(reverse('expense-detail', kwargs={'pk': expense.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '15.00')

    def test_update_expense(self):
        expense = Expense.objects.create(user=self.user, category='food', amount=Decimal('15.00'))
        response = self.client.patch(
            reverse('expense-detail', kwargs={'pk': expense.pk}),
            {'amount': '20.00', 'description': 'Updated'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expense.refresh_from_db()
        self.assertEqual(expense.amount, Decimal('20.00'))
        self.assertEqual(expense.description, 'Updated')

    def test_delete_expense(self):
        expense = Expense.objects.create(user=self.user, category='food', amount=Decimal('15.00'))
        response = self.client.delete(reverse('expense-detail', kwargs={'pk': expense.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Expense.objects.filter(pk=expense.pk).exists())

    def test_user_isolation_on_detail(self):
        other_expense = Expense.objects.create(
            user=self.other_user, category='food', amount=Decimal('50.00')
        )
        response = self.client.get(reverse('expense-detail', kwargs={'pk': other_expense.pk}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ExpenseFilterTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='filteruser', password='securepass1')
        self.client.force_authenticate(user=self.user)

        Expense.objects.create(user=self.user, category='food', amount=Decimal('10.00'))
        Expense.objects.create(user=self.user, category='transport', amount=Decimal('20.00'))

    def test_filter_by_category(self):
        response = self.client.get(reverse('expense-list-create'), {'category': 'food'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['category'], 'food')

    def test_bad_date_format_returns_400(self):
        response = self.client.get(reverse('expense-list-create'), {'start_date': 'not-a-date'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_end_date_is_inclusive(self):
        today = timezone.now().date()
        Expense.objects.create(user=self.user, category='other', amount=Decimal('5.00'))

        response = self.client.get(
            reverse('expense-list-create'),
            {
                'start_date': today.strftime('%Y-%m-%d'),
                'end_date': today.strftime('%Y-%m-%d'),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)


class AggregateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='agguser', password='securepass1')
        self.client.force_authenticate(user=self.user)

        Expense.objects.create(user=self.user, category='food', amount=Decimal('10.00'))
        Expense.objects.create(user=self.user, category='food', amount=Decimal('15.00'))
        Expense.objects.create(user=self.user, category='transport', amount=Decimal('30.00'))

    def test_total_expenses(self):
        response = self.client.get(reverse('total-expenses'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_expenses'], 55.0)

    def test_total_with_category_filter(self):
        response = self.client.get(reverse('total-expenses'), {'category': 'food'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_expenses'], 25.0)

    def test_summary_by_category(self):
        response = self.client.get(reverse('expense-summary'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_category = {item['category']: item for item in response.data['by_category']}
        self.assertEqual(by_category['food']['total'], 25.0)
        self.assertEqual(by_category['food']['count'], 2)
        self.assertEqual(by_category['transport']['total'], 30.0)


class HealthTests(APITestCase):
    def test_health_endpoint(self):
        response = self.client.get(reverse('health-check'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], 'ok')
