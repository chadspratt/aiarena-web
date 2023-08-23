# Generated by Django 3.2.16 on 2023-08-10 01:27

import aiarena.core.models.bot
import aiarena.core.storage
from django.db import migrations
import private_storage.fields


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0070_competition_indepth_bot_statistics_enabled"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bot",
            name="bot_zip",
            field=private_storage.fields.PrivateFileField(
                storage=aiarena.core.storage.OverwritePrivateStorage(base_url="/"),
                upload_to=aiarena.core.models.bot.bot_zip_upload_to,
            ),
        ),
    ]
