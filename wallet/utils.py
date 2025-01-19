from .models import Wallet, User
from .models import Transaction
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.core.exceptions import ValidationError
from django.db.models import F, QuerySet
from decimal import Decimal
from typing import Dict, Optional
import requests


class InsufficientFundsError(Exception):
    pass


def update_wallet(user, base_currency, quote_currency, amount, price, transaction_type) -> Transaction:
    """
    Updates wallet balances and records a transaction with proper validation and error handling.

    Args:
        user: User instance
        base_currency (str): The primary currency (e.g., BTC)
        quote_currency (str): The secondary currency (e.g., USD)
        amount (Decimal): Amount of base_currency to trade
        price (Decimal): Price per unit in quote_currency
        transaction_type (str): Either 'buy' or 'sell'

    Returns:
        Transaction: The created transaction instance

    Raises:
        InsufficientFundsError: If user has insufficient balance
        ValidationError: If input validation fails
        ValueError: If invalid parameters are provided
    """
    # Input validation
    if not all([user, base_currency, quote_currency, amount, price]):
        raise ValueError("All parameters are required")

    if not isinstance(amount, (Decimal, float, int)):
        raise ValueError("Amount must be a number")

    amount = Decimal(str(amount))
    price = Decimal(str(price))
    total_value = amount * price

    if amount <= 0 or price <= 0:
        raise ValueError("Amount and price must be positive")

    if base_currency == quote_currency:
        raise ValidationError("Base and quote currency cannot be the same")

    # Perform all operations in a transaction block
    with transaction.atomic():
        # Lock the wallet for update
        wallet = Wallet.objects.select_for_update().get(user=user)

        # Ensure balance dictionary exists
        if not wallet.balance:
            wallet.balance = {}

        # Get current balances with default 0
        base_balance = Decimal(str(wallet.balance.get(base_currency, '0')))
        quote_balance = Decimal(str(wallet.balance.get(quote_currency, '0')))

        # Check and update balances based on transaction type
        if transaction_type == 'buy':
            if quote_balance < total_value:
                raise InsufficientFundsError(
                    f"Insufficient {quote_currency} balance. "
                    f"Required: {total_value}, Available: {quote_balance}"
                )
            new_base_balance = base_balance + amount
            new_quote_balance = quote_balance - total_value

        elif transaction_type == 'sell':
            if base_balance < amount:
                raise InsufficientFundsError(
                    f"Insufficient {base_currency} balance. "
                    f"Required: {amount}, Available: {base_balance}"
                )
            new_base_balance = base_balance - amount
            new_quote_balance = quote_balance + total_value

        else:
            raise ValueError("Transaction type must be 'buy' or 'sell'")

        # Update wallet balances
        wallet.balance[base_currency] = str(new_base_balance)
        wallet.balance[quote_currency] = str(new_quote_balance)
        wallet.save()

        # Create and save transaction record
        transaction_record = Transaction.objects.create(
            user=user,
            base_currency=base_currency,
            quote_currency=quote_currency,
            amount=amount,
            price=price,
            total_value=total_value,
            transaction_type=transaction_type,
            status='completed'
        )

        return transaction_record


def get_user_wallet(telegram_user_id):
    """
    Gets or creates a wallet for a given Telegram user ID.
    First ensures user exists, then gets or creates their wallet.

    Args:
        telegram_user_id (str): Telegram user ID

    Returns:
        Wallet: The user's wallet instance

    Raises:
        Http404: If user doesn't exist
    """
    # (404 if not found)
    user = get_object_or_404(User, user_id=telegram_user_id)

    # Get or create their wallet
    wallet, created = Wallet.objects.get_or_create(
        user=user,
        defaults={'balance': {}}  # Default empty balance if created
    )
    return wallet


def get_user_transactions(telegram_user_id: str,
                          transaction_type: Optional[str] = None,
                          currency: Optional[str] = None,
                          limit: Optional[int] = None,
                          offset: Optional[int] = None
                          ) -> QuerySet:
    """
    Gets filtered transactions for a given Telegram user ID.

    Args:
        telegram_user_id: Telegram user ID
        transaction_type: Optional filter by type ('buy', 'sell', 'swap')
        currency: Optional filter by currency (base_currency or to_currency for swaps)
        limit: Optional limit number of results
        offset: Optional offset for pagination

    Returns:
        QuerySet: Ordered queryset of Transaction instances

    Raises:
        Http404: If user doesn't exist
    """
    user = get_object_or_404(User, user_id=telegram_user_id)

    # Start with all user transactions, ordered by newest first
    transactions = user.transactions.all().order_by('-timestamp')

    # Apply filters if provided
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    if currency:
        # Look for currency in both base_currency and to_currency (for swaps)
        transactions = transactions.filter(
            models.Q(base_currency=currency) |
            models.Q(to_currency=currency)
        )

    # Apply pagination if provided
    if offset is not None:
        transactions = transactions[offset:]
    if limit is not None:
        transactions = transactions[:limit]

    return transactions


# "Adapt this function to our project. i need the currency code map to be separate and available from any where in the project"
# XXXX CURRENTLY UNUSABLE
def fetch_price_data(currency_code: str) -> Dict[str, Decimal]:
    url = "https://api.coingecko.com/api/v3/simple/price"

    # Add mapping for common currency codes
    CURRENCY_CODE_MAP = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'USDT': 'tether',
        'DOGE': 'dogecoin',
        'XRP': 'ripple',
        'SOL': 'solana',
        'ADA': 'cardano',
        'AVAX': 'avalanche-2',
        'MATIC': 'matic-network',
        'DOT': 'polkadot'
    }

    # Convert currency code using the map
    if currency_code in CURRENCY_CODE_MAP:
        currency_code = CURRENCY_CODE_MAP[currency_code]
    else:
        raise ValueError(f"Unsupported currency code: {currency_code}")

    params = {'ids': f"{currency_code}", 'vs_currencies': 'usd'}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        price_data = {
            f"{currency_code}/USD": Decimal(str(data.get(currency_code, {}).get('usd', None))),
        }

        return price_data

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
