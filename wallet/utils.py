from .models import Wallet, User
from django.shortcuts import get_object_or_404
from django.db import models
from django.db.models import QuerySet
from typing import Optional


class InsufficientFundsError(Exception):
    pass


def get_user_wallet(telegram_user_id: str) -> Wallet:
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
    try:
        user = get_object_or_404(User, user_id=telegram_user_id)

        # Get or create their wallet (a fallback if create wallet signal failed)
        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': {}}  # set empty balance if created
        )
        return wallet
    except:
        return None


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
            models.Q(destination_currency=currency)
        )

    # Apply pagination if provided
    if offset is not None:
        transactions = transactions[offset:]
    if limit is not None:
        transactions = transactions[:limit]

    return transactions
