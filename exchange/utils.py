import requests
from django.core.exceptions import ValidationError
from decimal import Decimal
from typing import Union, Optional
from models import Coin, Vs_currencies
from django.shortcuts import get_object_or_404

from templates.URLS import Coingecko


class InsufficientFundsError(Exception):
    pass


class UnexpectedError(Exception):
    pass


def get_coin_price(currency_code: str, vs_currency: str = 'usd') -> Optional[Decimal]:
    '''
    Fetches the current price of a cryptocurrency in USD(or otherwise stated) from the CoinGecko API.
    Returns The price of the coin in USD, or None
    '''
    try:
        url = Coingecko.COIN_PRICE

        # Validate currency codes
        currency_code = currency_code.lower()
        vs_currency = vs_currency.lower()
        try:
            coin = Coin.objects.get_object_or_404(Coin, symbol=currency_code)
            quote = Vs_currencies.objects.get_object_or_404(
                Vs_currencies, currency=vs_currency)
        except:
            raise ValueError(
                f"Unsupported currency(ies): {currency_code}/{vs_currency}")

        # Fetch price data
        try:
            coin_id = coin.id
            quote_currency = quote.currency

            params = {'ids': f"{coin_id}",
                      'vs_currencies': f"{quote_currency}"}
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()
            price = Decimal(data[coin_id][quote_currency])

            return price
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred: {req_err}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def get_swap_destination_amount(
        origin_currency_code: str, destination_currency_code: str,
        origin_amount: Union[int, float, str, Decimal]
) -> Union[Decimal, float, None]:
    '''
    Calculates the amount of a destination currency that can be obtained from a given amount of an origin currency.
    Returns The amount of the destination currency that can be obtained, or None
    '''
    try:
        origin_amount = Decimal(str(origin_amount))
        origin_currency_code = origin_currency_code.lower()
        destination_currency_code = destination_currency_code.lower()

        # Validate currency codes
        try:
            coin = Coin.objects.get_object_or_404(
                Coin, symbol=origin_currency_code)
            quote = Coin.objects.get_object_or_404(
                Coin, symbol=destination_currency_code)
        except:
            raise ValueError(
                f"Either currencies are unsupported: {origin_currency_code}, {destination_currency_code}")

        # Get price rates
        origin_usd_price = get_coin_price(origin_currency_code)
        destination_usd_price = get_coin_price(destination_currency_code)

        # Validate price data
        if not (origin_usd_price and destination_usd_price):
            raise ValidationError(
                "Price data unavailable for one or both currencies")

        # Calculate swap amounts
        total_swap_value = origin_amount * origin_usd_price
        destination_amount = total_swap_value / destination_usd_price
        return destination_amount
    except Exception as e:
        print(f"Error: {e}")
        return None
