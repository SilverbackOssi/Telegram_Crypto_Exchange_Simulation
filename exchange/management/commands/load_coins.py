from ...models import Coin, Vs_currencies
import requests
from django.core.management.base import BaseCommand
import time


class Command(BaseCommand):
    help = 'Load database with supported currencies from CoinGecko API'

    def handle(self, *args, **kwargs):
        start_time = time.time()
        coingecko_url = "https://api.coingecko.com/api/v3"

        # Fetch the list of vs_currencies
        vs_currencies_response = requests.get(
            f"{coingecko_url}/simple/supported_vs_currencies")
        vs_currencies = vs_currencies_response.json()
        # Update or create the vs_currencies in the database
        for vs_currency in vs_currencies:
            Vs_currencies.objects.update_or_create(
                currency=vs_currency
            )

        # Fetch the list of available coins
        coins_response = requests.get(f"{coingecko_url}/coins/list")
        coins = coins_response.json()
        # Update or create the coins in the database
        for coin in coins:
            coin_data = {
                'id': coin['id'],
                'name': coin['name'],
                'symbol': coin['symbol'],
                'is_active': True
            }
            Coin.objects.update_or_create(
                id=coin_data['id'],
                defaults=coin_data
            )

        end_time = time.time()
        total_time = end_time - start_time
        self.stdout.write(self.style.SUCCESS(
            f'Successfully loaded currencies from CoinGecko API in {total_time:.2f} seconds'))
