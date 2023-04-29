# Generated by Django 4.2 on 2023-04-26 05:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Offer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('offer_id', models.CharField(max_length=255, unique=True)),
                ('owner_type', models.PositiveSmallIntegerField()),
                ('owner_type_name', models.CharField(max_length=255)),
                ('status', models.PositiveSmallIntegerField()),
                ('status_name', models.CharField(max_length=255)),
                ('offer_type', models.PositiveSmallIntegerField()),
                ('offer_type_name', models.CharField(max_length=255)),
                ('currency', models.CharField(max_length=5)),
                ('conversion_currency', models.CharField(max_length=5)),
                ('payment_method', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'offerbot_offer',
            },
        ),
        migrations.CreateModel(
            name='OfferHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_offer_price', models.DecimalField(decimal_places=8, max_digits=28)),
                ('updated_offer_price', models.DecimalField(decimal_places=8, max_digits=28)),
                ('competitor_offer_price', models.DecimalField(decimal_places=8, max_digits=28)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('competitor_offer', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='competitor_offer', to='src.offer')),
                ('offer', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='internal_offer', to='src.offer')),
            ],
            options={
                'db_table': 'offerbot_offer_history',
            },
        ),
    ]
