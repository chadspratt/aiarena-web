# Generated by Django 3.2.16 on 2023-01-08 15:42

import aiarena.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0062_auto_20230108_1113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competitionbotmapstats',
            name='crash_count',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='competitionbotmapstats',
            name='crash_perc',
            field=models.FloatField(blank=True, default=0, validators=[aiarena.core.validators.validate_not_nan, aiarena.core.validators.validate_not_inf]),
        ),
        migrations.AlterField(
            model_name='competitionbotmapstats',
            name='loss_count',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='competitionbotmapstats',
            name='loss_perc',
            field=models.FloatField(blank=True, default=0, validators=[aiarena.core.validators.validate_not_nan, aiarena.core.validators.validate_not_inf]),
        ),
        migrations.AlterField(
            model_name='competitionbotmapstats',
            name='match_count',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='competitionbotmapstats',
            name='tie_count',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='competitionbotmapstats',
            name='tie_perc',
            field=models.FloatField(blank=True, default=0, validators=[aiarena.core.validators.validate_not_nan, aiarena.core.validators.validate_not_inf]),
        ),
        migrations.AlterField(
            model_name='competitionbotmapstats',
            name='win_count',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='competitionbotmapstats',
            name='win_perc',
            field=models.FloatField(blank=True, default=0, validators=[aiarena.core.validators.validate_not_nan, aiarena.core.validators.validate_not_inf]),
        ),
    ]
