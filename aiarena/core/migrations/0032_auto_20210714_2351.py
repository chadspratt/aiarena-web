# Generated by Django 3.0.14 on 2021-07-14 13:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0031_competition_interest"),
    ]

    operations = [
        migrations.AlterField(
            model_name="competition",
            name="interest",
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
