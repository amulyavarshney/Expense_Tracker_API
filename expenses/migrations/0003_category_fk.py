# Generated manually for Category FK migration

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


DEFAULT_CATEGORIES = [
    ('food', 'Food'),
    ('transport', 'Transport'),
    ('entertainment', 'Entertainment'),
    ('other', 'Other'),
]


def seed_categories_and_migrate_expenses(apps, schema_editor):
    Category = apps.get_model('expenses', 'Category')
    Expense = apps.get_model('expenses', 'Expense')

    slug_to_category = {}
    for slug, name in DEFAULT_CATEGORIES:
        category, _ = Category.objects.get_or_create(
            user=None,
            slug=slug,
            defaults={'name': name},
        )
        slug_to_category[slug] = category

    fallback = slug_to_category['other']
    for expense in Expense.objects.all():
        old_slug = expense.category_old
        expense.category = slug_to_category.get(old_slug, fallback)
        expense.save(update_fields=['category'])


def reverse_migration(apps, schema_editor):
    Category = apps.get_model('expenses', 'Category')
    Expense = apps.get_model('expenses', 'Expense')

    for expense in Expense.objects.select_related('category').all():
        expense.category_old = expense.category.slug
        expense.save(update_fields=['category_old'])

    Category.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0002_alter_expense_options_expense_description_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('slug', models.SlugField(max_length=50)),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'user',
                    models.ForeignKey(
                        blank=True,
                        help_text='Null for system-wide default categories.',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='categories',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.RenameField(
            model_name='expense',
            old_name='category',
            new_name='category_old',
        ),
        migrations.AddField(
            model_name='expense',
            name='category',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='expenses',
                to='expenses.category',
            ),
        ),
        migrations.RunPython(
            seed_categories_and_migrate_expenses,
            reverse_migration,
        ),
        migrations.RemoveIndex(
            model_name='expense',
            name='expenses_ex_user_id_207090_idx',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='category_old',
        ),
        migrations.AlterField(
            model_name='expense',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='expenses',
                to='expenses.category',
            ),
        ),
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(
                condition=models.Q(('user__isnull', True)),
                fields=('slug',),
                name='unique_system_category_slug',
            ),
        ),
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(
                condition=models.Q(('user__isnull', False)),
                fields=('user', 'slug'),
                name='unique_user_category_slug',
            ),
        ),
        migrations.AddIndex(
            model_name='expense',
            index=models.Index(fields=['user', 'category'], name='expenses_ex_user_id_207090_idx'),
        ),
    ]
