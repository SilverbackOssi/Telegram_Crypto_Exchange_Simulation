from django.db import models
from django.core.validators import MinValueValidator


class User(models.Model):
    user_id = models.CharField(max_length=255, unique=True)  # Telegram User ID
    username = models.CharField(max_length=255, unique=True)


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Stores balances in different currencies
    balance = models.JSONField(default=dict)


class Transaction(models.Model):
    # Constants
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('swap', 'Swap')
    ]
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ]

    # Fields (14 Columns, 2 Auto Fields)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='transactions')
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name='transactions')
    # currency = models.ForeignKey(Coin, on_delete=models.CASCADE, related_name='trades')
    # XXX: Use currency object foreign instead of currency symbol, create currency model
    # use currency symbol like 'btc', 'eth', 'usd'
    base_currency = models.CharField(max_length=50, db_index=True)
    destination_currency = models.CharField(max_length=50, db_index=True)
    base_amount = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        validators=[MinValueValidator(0.0)],
        help_text="Value of transaction in base currency (Amount sent)"
    )
    destination_amount = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        validators=[MinValueValidator(0.0)],
        help_text="Value of transaction in quote currency (Amount received)"
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        validators=[MinValueValidator(0.0)],
        help_text="Exchange rate in USD (Price of 1 unit of origin currency in destination currency for swaps)"
    )
    transaction_type = models.CharField(
        max_length=4, choices=TRANSACTION_TYPES, db_index=True)
    swap_origin_usd_rate = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0)],
        help_text="Price of 1 unit of base currency in USD at the time of swap"
    )
    swap_destination_usd_rate = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0)],
        help_text="Price of 1 unit of quote currency in USD at the time of swap"
    )
    status = models.CharField(
        max_length=10, choices=TRANSACTION_STATUS, default='pending', db_index=True)
    transaction_details = models.TextField(
        blank=True, help_text="Additional details about the transaction")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Indexes and ordering
    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['base_currency', 'destination_currency'])
        ]
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'

    '''
    # Methods
    def save(self, *args, **kwargs):
        # Calculate total value before saving
        if self.base_amount and self.rate:
            self.destination_amount = self.base_amount * self.rate
        super().save(*args, **kwargs)'''

    def __str__(self):
        return f"{self.transaction_type.upper()} {self.base_amount} {self.base_currency} @ {self.rate} {self.destination_currency}"
