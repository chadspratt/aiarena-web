# Generated by Django 2.1.7 on 2019-05-06 19:16

from django.db import migrations
import private_storage.fields
import private_storage.storage.files


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_user_serviceaccount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bot',
            name='bot_zip',
            field=private_storage.fields.PrivateFileField(storage=private_storage.storage.files.PrivateFileSystemStorage(), upload_to='bots'),
        ),
    ]