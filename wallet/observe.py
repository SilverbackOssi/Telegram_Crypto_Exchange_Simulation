from decimal import Decimal
from typing import Dict, Union
from dataclasses import dataclass
from django.db import transaction
from django.shortcuts import get_object_or_404
from .utils import fetch_price_data, get_user_wallet
from .models import User, Transaction


@dataclass
class TransactionResult:
    success: bool
    transaction_record: Union[Transaction, None]
    status: str
    message: str
    final_balances: Dict[str, Decimal] = None
    error_type: str = None


def execute_crypto_swap(user_id: str, origin_currency_code: str, destination_currency_code: str,
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
