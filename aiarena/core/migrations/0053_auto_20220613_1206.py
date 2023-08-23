# Generated by Django 3.2.9 on 2022-06-13 12:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0052_alter_bot_plays_race"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="bot",
            name="plays_race",
        ),
        migrations.AlterField(
            model_name="bot",
            name="plays_race_model",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.botrace"),
        ),
    ]
