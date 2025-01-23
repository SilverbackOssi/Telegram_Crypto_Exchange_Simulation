# from django.test import TestCase
import requests
import requests_cache
from templates.URLS import Coingecko
from decimal import Decimal

requests_cache.install_cache('coingecko_cache', expire_after=3600)
# url = "<https://api.coingecko.com/api/v3/coins/list>"


def fetch_supported_VScurrencies():
    url = "https://api.coingecko.com/api/v3/simple/supported_vs_currencies"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        return data
    return None


def fetch_supported_cryptocurrencies():
    url = "https://api.coingecko.com/api/v3/coins/list"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    return None


def fetch_exchange_rate(base_currency, quote_currency):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={base_currency}&vs_currencies={quote_currency},eur"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
        # return data.get(base_currency, {}).get(quote_currency, None)
    return None


'''
# Check if currency code is supported XXX: This should be cross-checked with the list of supported currencies in the database
def confirm_currency_code(currency_code):
    url = f"https://api.coingecko.com/api/v3/simple/supported_vs_currencies"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return currency_code in data
    return False'''

# print(fetch_supported_VScurrencies())
# coins = fetch_supported_cryptocurrencies()
# vs_currencies = fetch_supported_VScurrencies()

# print(vs_currencies in coins)
# usd = next(
#    (currency for currency in vs_currencies if currency.lower() == "usd"), None)
# print(vs_currencies)
'''bitcoin = next(
    (coin for coin in coins if coin['name'].lower() == "bitcoin"), None)
ethereum = next(
    (coin for coin in coins if coin['name'].lower() == "ethereum"), None)
print(bitcoin) #{'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'}
print(ethereum)'''
# print(fetch_exchange_rate("bitcoin", "usd")
#       )  # {'bitcoin': {'usd': 104254, 'eur': 100146}}
# time.sleep(3)
# print(Coingecko.COIN_PRICE)
# coin_price = requests.get(f"{Coingecko.COIN_PRICE}", params={'ids': 'ethereum', 'vs_currencies': 'usd'}
#                           ).json()
# print(coin_price)
# print("fetch currency, fetch price, sort categories".upper())
#
coins_response = requests.get(f"{Coingecko.API_BASE}/coins/list")
coins = coins_response.json()
print(len(coins))
# Fetch the prices of all coins in one request
coin_ids = ','.join([coin['id'] for coin in coins])
# print(coin_ids)
# coin_prices_response = requests.get(
#     f"{Coingecko.API_BASE}/simple/price",
#     params={'ids': coin_ids, 'vs_currencies': 'usd'}
# )
# coin_prices_response.raise_for_status()
# coin_prices = coin_prices_response.json()
# print(coin_prices)
coin_id = "bitcoin"
quote_currency = "usd"
params = {'ids': f"{coin_id}", 'vs_currencies': f"{quote_currency}"}
response = requests.get(Coingecko.COIN_PRICE, params=params)
response.raise_for_status()  # Raise an exception for HTTP errors
data = response.json()
price = Decimal(data[coin_id][quote_currency])
print(price)
