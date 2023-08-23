# Generated by Django 3.0.8 on 2020-12-18 21:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("wiki", "0003_mptt_upgrade"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="bot",
            name="wiki_article",
            field=models.OneToOneField(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="wiki.Article"
            ),
        ),
    ]
