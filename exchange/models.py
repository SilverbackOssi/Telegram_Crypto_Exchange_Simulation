from django.db import models


class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    current_price = models.DecimalField(max_digits=20, decimal_places=8)
    last_updated = models.DateTimeField(auto_now=True)
    last_updated.short_description = "Last Updated"

    def __str__(self):
        return f"{self.code} - {self.name}"


'''class Trade(models.Model):
    TRADE_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='trades')
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trade_type} {self.amount} {self.currency.code} at {self.price}"'''
