# Generated manually for currency and receipt fields

from django.db import migrations, models

import expenses.models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0003_category_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='currency',
            field=models.CharField(default='USD', max_length=3),
        ),
        migrations.AddField(
            model_name='expense',
            name='receipt',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=expenses.models.receipt_upload_path,
            ),
        ),
    ]
