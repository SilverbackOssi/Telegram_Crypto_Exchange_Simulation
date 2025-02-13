# from django.test import TestCase
import requests
import requests_cache
from templates.URLS import Coingecko
from decimal import Decimal
from wallet.models import User
from wallet.utils import get_user_wallet, get_user_transactions
from .models import Coin, Vs_currencies
from .utils import get_swap_destination_amount
from .services import simulate_and_execute_buy_sell, simulate_and_execute_swap, get_object_or_404, deposit_usd
from django.db.models import Count

requests_cache.install_cache('coingecko_cache', expire_after=3600)

rand_id = '123456'
test_user, _ = User.objects.get_or_create(
    user_id=rand_id, username='test_user')
if _:
    print('New user created')
else:
    print('User Found')
test_user_wallet = get_user_wallet(test_user.user_id)
# test creating same user raise unique key constraint error
if test_user_wallet:
    print(f"user {test_user.username}: {test_user.user_id}, wallet found")

# test fetch coins and vs
currency_code = "eth"
cryptocurrency_id = "ethereum"
vs_currency = "usd"


# test deposit = PASS
# deposit_result = deposit_usd(test_user.user_id, 500000)
# print(
#     f"\ntransaction status: {deposit_result.status},{deposit_result.message}")
#  test buy = PASS
# buy_result = simulate_and_execute_buy_sell(
#     test_user.user_id, "ethereum", 16, "buy")
# print(f"\ntransaction status: {buy_result.status},{buy_result.message}")
# # test sell = PASS
# sell_result = simulate_and_execute_buy_sell(
#     test_user.user_id, "ethereum", 49, "sell")
# print(f"\ntransaction status: {sell_result.status},{sell_result.message}")

# test swap
# swap_result = simulate_and_execute_swap(
#     test_user.user_id, cryptocurrency_id, "bitcoin", 300)
# print(f"\ntransaction status: {swap_result.status},{swap_result.message}")
# print(f"new balance: {test_user_wallet.balance}")

# get user transactions - PASS
# test_user_transactions = get_user_transactions(
#     test_user.user_id, currency="usd")
# for transaction in test_user_transactions:
#     rate = transaction.rate
#     print(rate)
# print(test_user_transactions)

# get swap destination
amoount = 1
destination_amount = get_swap_destination_amount(
    'bitcoin', 'ethereum', amoount)
print(f'swap {amoount} bitcoin for [{destination_amount}] ethereum')
# =====================================
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
# coins_response = requests.get(f"{Coingecko.API_BASE}/coins/list")
# coins = coins_response.json()
# print(len(coins))
# # Fetch the prices of all coins in one request
# coin_ids = ','.join([coin['id'] for coin in coins])
# # print(coin_ids)
# # coin_prices_response = requests.get(
# #     f"{Coingecko.API_BASE}/simple/price",
# #     params={'ids': coin_ids, 'vs_currencies': 'usd'}
# # )
# # coin_prices_response.raise_for_status()
# # coin_prices = coin_prices_response.json()
# # print(coin_prices)
# coin_id = "bitcoin"
# quote_currency = "usd"
# params = {'ids': f"{coin_id}", 'vs_currencies': f"{quote_currency}"}
# response = requests.get(Coingecko.COIN_PRICE, params=params)
# response.raise_for_status()  # Raise an exception for HTTP errors
# data = response.json()
# price = Decimal(data[coin_id][quote_currency])
# print(price)
