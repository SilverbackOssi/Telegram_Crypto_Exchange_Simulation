import requests
from wallet.utils import fetch_price_data, get_user_wallet, update_wallet
from django.core.exceptions import ValidationError
from decimal import Decimal
from typing import Union, Dict
from dataclasses import dataclass
from wallet.models import Transaction, User
from django.shortcuts import get_object_or_404
from django.db import transaction


@dataclass
class TransactionResult:
    success: bool
    transaction_record: Union[Transaction, None]
    status: str
    message: str
    final_balances: Dict[str, Decimal] = None
    error_type: str = None


class InsufficientFundsError(Exception):
    pass


class UnexpectedError(Exception):
    pass


'''def fetch_exchange_rate(base_currency, quote_currency):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={base_currency}&vs_currencies={quote_currency}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get(base_currency, {}).get(quote_currency, None)
    return None

# Helper function to confirm if a currency code is supported
# !!!This is useful for validating user input before processing any transaction


# Check if currency code is supported XXX: This should be cross-checked with the list of supported currencies in the database
def confirm_currency_code(currency_code):
    url = f"https://api.coingecko.com/api/v3/simple/supported_vs_currencies"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return currency_code in data
    return False'''


def get_swap_destination_amount(
        origin_currency_code: str, destination_currency_code: str,
        origin_amount: Union[int, float, str, Decimal]
) -> Union[Decimal, float, None]:
    try:
        origin_amount = Decimal(str(origin_amount))
        # Get price rates
        origin_usd_price = fetch_price_data(
            origin_currency_code).get(f"{origin_currency_code}/USD")
        destination_usd_price = fetch_price_data(
            destination_currency_code).get(f"{destination_currency_code}/USD")

        # Validate price data
        if not (origin_usd_price and destination_usd_price):
            raise ValidationError(
                "Price data unavailable for one or both currencies")

        # Calculate swap amounts
        total_swap_value = origin_amount * origin_usd_price
        destination_amount = total_swap_value / destination_usd_price
    except Exception as e:
        print(f"Error: {e}")
        return None
    else:
        return destination_amount


def simulate_and_execute_swap(user_id: str, origin_currency_code: str, destination_currency_code: str,
                              origin_amount: Union[Decimal, float, str],
                              ) -> TransactionResult:
    """
    Executes and records a cryptocurrency swap as a single transaction.

    Args:
        user_id: Telegram user ID
        origin_currency_code: Currency to swap from
        destination_currency_code: Currency to swap to
        origin_amount: Amount of origin_currency_code to swap

    Returns:
        TransactionResult object containing execution status and details

    Raises:
        Unexpected Error: If an error occurs during the swap transaction  
    """
    try:
        # Input validation
        if not all([user_id, origin_currency_code, destination_currency_code, origin_amount]):
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='invalid_input',
                message="All parameters are required",
                error_type='ValidationError'
            )
        if not isinstance(origin_amount, (Decimal, float, int)):
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='invalid_input',
                message="Amount must be a number",
                error_type='ValidationError'
            )
        if origin_amount <= 0:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='invalid_input',
                message="Amount must be positive",
                error_type='ValidationError'
            )
        if origin_currency_code == destination_currency_code:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='invalid_pair',
                message="Cannot swap currency for itself",
                error_type='ValidationError'
            )

        # XXX: Remember to Check if currency is supported
        '''if origin_currency_code not in ['BTC', 'ETH', 'LTC', 'XRP', 'BCH', 'USDT']:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='unsupported_currency',
                message="Currency not supported",
                error_type='ValidationError'
            )
        if destination_currency_code not in ['BTC', 'ETH', 'LTC', 'XRP', 'BCH', 'USDT']:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='unsupported_currency',
                message="Currency not supported",
                error_type='ValidationError'
            )'''

        origin_amount = Decimal(str(origin_amount))
        # Get price rates
        origin_usd_price = fetch_price_data(
            origin_currency_code).get(f"{origin_currency_code}/USD")
        destination_usd_price = fetch_price_data(
            destination_currency_code).get(f"{destination_currency_code}/USD")

        # Validate price data
        if not (origin_usd_price and destination_usd_price):
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='price_unavailable',
                message="Price data unavailable for one or both currencies",
                error_type='ValidationError'
            )

        # Calculate swap amounts
        total_swap_value = origin_amount * origin_usd_price
        destination_amount = total_swap_value / destination_usd_price
        rate = destination_amount / origin_amount

        # Execute the swap as a single unit of work (transaction)
        with transaction.atomic():
            user = get_object_or_404(User, user_id=user_id)
            wallet = get_user_wallet(user_id)

            # Check if user has sufficient balance
            current_origin_balance = Decimal(
                str(wallet.balance.get(origin_currency_code, '0')))
            if current_origin_balance < origin_amount:
                return TransactionResult(
                    success=False,
                    transaction_record=None,
                    status='insufficient_funds',
                    message=f"Insufficient {origin_currency_code} balance. Current balance is {current_origin_balance}",
                    error_type='InsufficientFundsError'
                )

            # (Perform swap) Update wallet balances
            wallet.balance[origin_currency_code] = Decimal(
                str(current_origin_balance - origin_amount))
            wallet.balance[destination_currency_code] = Decimal(str(
                Decimal(str(wallet.balance.get(destination_currency_code, '0'))) + destination_amount))
            wallet.save()

            # Record the swap transaction
            transaction_record = Transaction.objects.create(
                user=user,
                wallet=wallet,
                base_currency=origin_currency_code,
                base_amount=origin_amount,
                destination_currency=destination_currency_code,
                destination_amount=destination_amount,
                rate=rate,
                swap_destination_usd_rate=destination_usd_price,
                swap_origin_usd_rate=origin_usd_price,
                transaction_type='swap',
                status='completed',
                transaction_details=f"Swapped {origin_amount} {origin_currency_code} for {destination_amount} {destination_currency_code}"
            )
            return TransactionResult(
                success=True,
                transaction_record=transaction_record,
                status='completed',
                message=(
                    f"Successfully swapped {origin_amount} {origin_currency_code} "
                    f"for {destination_amount:.8f} {destination_currency_code}"
                ),
                final_balances={
                    origin_currency_code: wallet.balance[origin_currency_code],
                    destination_currency_code: wallet.balance[destination_currency_code]
                }
            )
    except Exception as e:
        # Log unexpected error here
        print(f"Unexpected Error: {str(e)}")
        return TransactionResult(
            success=False,
            transaction_record=None,
            status='error',
            message=f"Unexpected error: {str(e)}",
            error_type=e.__class__.__name__
        )


def simulate_and_execute_buy_sell(
        user_id: str,
        base_currency: str,
        quote_currency: str,
        amount: Union[Decimal, float, str],
        price: Union[Decimal, float, str],
        transaction_type: str) -> TransactionResult:
    """
    Simulates and executes a trading transaction, providing detailed status reporting.

    Args:
        user_id: Telegram user ID
        base_currency: Primary currency (e.g., BTC)
        quote_currency: Secondary currency (e.g., USD)
        amount: Amount to trade
        price: Price per unit
        transaction_type: 'buy' or 'sell'

    Returns:
        TransactionResult object containing execution status and details
    """
    try:
        # Convert amounts to Decimal
        amount = Decimal(str(amount))
        price = Decimal(str(price))
        total_value = amount * price

        # Get user and wallet
        user = get_object_or_404(User, user_id=user_id)
        wallet = get_user_wallet(user_id)

        # Get current balances
        current_base = Decimal(str(wallet.balance.get(base_currency, '0')))
        current_quote = Decimal(str(wallet.balance.get(quote_currency, '0')))

        # Simulate the transaction
        if transaction_type == 'buy':
            if current_quote < total_value:
                return TransactionResult(
                    success=False,
                    transaction_record=None,
                    status='insufficient_funds',
                    message=f"Insufficient {quote_currency} balance. Need: {total_value}, Have: {current_quote}",
                    predicted_balances={
                        base_currency: current_base,
                        quote_currency: current_quote
                    },
                    error_type='InsufficientFundsError'
                )
            predicted_base = current_base + amount
            predicted_quote = current_quote - total_value

        elif transaction_type == 'sell':
            if current_base < amount:
                return TransactionResult(
                    success=False,
                    transaction_record=None,
                    status='insufficient_funds',
                    message=f"Insufficient {base_currency} balance. Need: {amount}, Have: {current_base}",
                    predicted_balances={
                        base_currency: current_base,
                        quote_currency: current_quote
                    },
                    error_type='InsufficientFundsError'
                )
            predicted_base = current_base - amount
            predicted_quote = current_quote + total_value

        else:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='invalid_transaction_type',
                message="Transaction type must be 'buy' or 'sell'",
                error_type='ValidationError'
            )

        # If simulation successful, execute the actual transaction
        transaction_record = update_wallet(
            user=user,
            base_currency=base_currency,
            quote_currency=quote_currency,
            amount=amount,
            price=price,
            transaction_type=transaction_type
        )

        return TransactionResult(
            success=True,
            transaction_record=transaction_record,
            status='completed',
            message=f"Successfully {transaction_type} {amount} {base_currency} at {price} {quote_currency}",
            predicted_balances={
                base_currency: predicted_base,
                quote_currency: predicted_quote
            }
        )
    except ValidationError as e:
        print(f"Validation Error: {str(e)}")
        return TransactionResult(
            success=False,
            transaction_record=None,
            status='validation_error',
            message=str(e),
            error_type='ValidationError'
        )
    except Exception as e:
        # Log unexpected error here
        print(f"Unexpected Error: {str(e)}")
        return TransactionResult(
            success=False,
            transaction_record=None,
            status='error',
            message=f"Unexpected error: {str(e)}",
            error_type=e.__class__.__name__
        )


# Test fetch_exchange_rate and confirm_currency_code functions
'''if __name__ == "__main__":
    rate = fetch_exchange_rate("btc", "usd")

    if rate:
        print(f"1 Bitcoin = {rate} USD")
    else:
        print("Failed to fetch exchange rate.")

    print(confirm_currency_code("eth"))  # True'''
