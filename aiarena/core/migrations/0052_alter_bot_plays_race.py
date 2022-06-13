# Generated by Django 3.2.9 on 2022-06-13 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_competition_playable_races'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bot',
            name='plays_race',
            field=models.CharField(blank=True, choices=[('T', 'Terran'), ('Z', 'Zerg'), ('P', 'Protoss'), ('R', 'Random')], max_length=1, null=True),
        ),
    ]
