from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from budgets.models import Budget
from expenses.models import Category, Expense


def system_category(slug):
    return Category.objects.get(user__isnull=True, slug=slug)


class BudgetCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='budgetuser', password='securepass1')
        self.other_user = User.objects.create_user(username='other', password='securepass1')
        self.client.force_authenticate(user=self.user)

    def test_create_budget(self):
        response = self.client.post(
            reverse('budget-list-create'),
            {'category': 'food', 'amount': '500.00', 'period': 'monthly'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['category'], 'food')
        self.assertEqual(response.data['category_name'], 'Food')
        self.assertEqual(response.data['amount'], '500.00')
        self.assertEqual(response.data['period'], 'monthly')
        self.assertIn('spent', response.data)
        self.assertIn('remaining', response.data)
        self.assertIn('period_start', response.data)
        self.assertIn('period_end', response.data)

    def test_negative_amount_rejected(self):
        response = self.client.post(
            reverse('budget-list-create'),
            {'category': 'food', 'amount': '-10.00', 'period': 'monthly'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_category_period_rejected(self):
        Budget.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('300.00'),
            period=Budget.Period.MONTHLY,
        )
        response = self.client.post(
            reverse('budget-list-create'),
            {'category': 'food', 'amount': '400.00', 'period': 'monthly'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_budgets_user_scoped(self):
        Budget.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('300.00'),
            period=Budget.Period.MONTHLY,
        )
        Budget.objects.create(
            user=self.other_user,
            category=system_category('transport'),
            amount=Decimal('200.00'),
            period=Budget.Period.WEEKLY,
        )

        response = self.client.get(reverse('budget-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['category'], 'food')

    def test_filter_by_category_and_period(self):
        Budget.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('300.00'),
            period=Budget.Period.MONTHLY,
        )
        Budget.objects.create(
            user=self.user,
            category=system_category('transport'),
            amount=Decimal('100.00'),
            period=Budget.Period.WEEKLY,
        )

        response = self.client.get(
            reverse('budget-list-create'),
            {'category': 'food', 'period': 'monthly'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['period'], 'monthly')

    def test_retrieve_budget(self):
        budget = Budget.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('250.00'),
            period=Budget.Period.YEARLY,
        )
        response = self.client.get(reverse('budget-detail', kwargs={'pk': budget.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '250.00')
        self.assertEqual(response.data['period'], 'yearly')

    def test_update_budget(self):
        budget = Budget.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('250.00'),
            period=Budget.Period.MONTHLY,
        )
        response = self.client.patch(
            reverse('budget-detail', kwargs={'pk': budget.pk}),
            {'amount': '350.00'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        budget.refresh_from_db()
        self.assertEqual(budget.amount, Decimal('350.00'))

    def test_delete_budget(self):
        budget = Budget.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('250.00'),
            period=Budget.Period.MONTHLY,
        )
        response = self.client.delete(reverse('budget-detail', kwargs={'pk': budget.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Budget.objects.filter(pk=budget.pk).exists())

    def test_user_isolation_on_detail(self):
        other_budget = Budget.objects.create(
            user=self.other_user,
            category=system_category('food'),
            amount=Decimal('999.00'),
            period=Budget.Period.MONTHLY,
        )
        response = self.client.get(reverse('budget-detail', kwargs={'pk': other_budget.pk}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse('budget-list-create'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BudgetSpendTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='spenduser', password='securepass1')
        self.client.force_authenticate(user=self.user)

    def test_spent_and_remaining_reflect_current_period_expenses(self):
        Budget.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('100.00'),
            period=Budget.Period.MONTHLY,
        )
        Expense.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('30.00'),
        )
        Expense.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('20.00'),
        )
        Expense.objects.create(
            user=self.user,
            category=system_category('transport'),
            amount=Decimal('50.00'),
        )

        response = self.client.get(reverse('budget-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        budget = response.data['results'][0]
        self.assertEqual(budget['spent'], '50.00')
        self.assertEqual(budget['remaining'], '50.00')

    def test_spent_excludes_expenses_outside_current_period(self):
        budget = Budget.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('100.00'),
            period=Budget.Period.MONTHLY,
        )
        old_expense = Expense.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('40.00'),
        )
        Expense.objects.filter(pk=old_expense.pk).update(
            timestamp=timezone.now().replace(year=timezone.now().year - 1)
        )
        Expense.objects.create(
            user=self.user,
            category=system_category('food'),
            amount=Decimal('10.00'),
        )

        response = self.client.get(reverse('budget-detail', kwargs={'pk': budget.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['spent'], '10.00')
        self.assertEqual(response.data['remaining'], '90.00')
