from django.db import models
from django.core.validators import MinValueValidator


class Coin(models.Model):
    # e.g., 'bitcoin' for BTC
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)                 # e.g., 'Bitcoin'
    symbol = models.CharField(max_length=50)                # e.g., 'btc'
    price_usd = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=0.0,
        blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Current price in USD"
    )
    last_updated = models.DateTimeField(auto_now=True, db_index=True)
    last_updated.short_description = "Last Updated"
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name_plural = "Coins"
        ordering = ['symbol']

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class Vs_currencies(models.Model):
    currency = models.CharField(max_length=50, primary_key=True)

    class Meta:
        verbose_name_plural = "Vs_currencies"

    def __str__(self):
        return self.currency
