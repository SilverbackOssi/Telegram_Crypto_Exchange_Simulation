from typing import Dict, Union
from decimal import Decimal
from dataclasses import dataclass
from django.shortcuts import get_object_or_404
from django.db import transaction
from wallet.models import Transaction, User
from wallet.utils import get_user_wallet
from .models import Coin
from .utils import get_coin_price


@dataclass
class TransactionResult:
    success: bool
    transaction_record: Union[Transaction, None]
    status: str
    message: str
    final_balances: Dict[str, Decimal] = None
    error_type: str = None


# For future reference: All transactions are swaps. A swap is a transaction where one currency is exchanged for another.
# we only support usd as the base currency for now

def simulate_and_execute_swap(user_id: str, origin_currency_id: str, destination_currency_id: str,
                              origin_amount: Union[Decimal, float, str],
                              ) -> TransactionResult:
    """
    Executes and records a cryptocurrency swap as a single transaction.

    Args:
        user_id: Telegram user ID
        origin_currency_id: Currency to swap from
        destination_currency_id: Currency to swap to
        origin_amount: Amount of origin_currency_id to swap

    Returns:
        TransactionResult object containing execution status and details

    Raises:
        Unexpected Error: If an error occurs during the swap transaction  
    """
    try:
        # Input validation
        if not all([user_id, origin_currency_id, destination_currency_id, origin_amount]):
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
        if origin_currency_id == destination_currency_id:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='invalid_pair',
                message="Cannot swap currency for itself",
                error_type='ValidationError'
            )

        supported_coins = Coin.objects.filter(
            is_active=True).values_list('id', flat=True)
        if origin_currency_id not in supported_coins:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='unsupported_currency',
                message="Currency not supported",
                error_type='ValidationError'
            )
        if destination_currency_id not in supported_coins:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='unsupported_currency',
                message="Currency not supported",
                error_type='ValidationError'
            )
        origin_amount = Decimal(str(origin_amount))

        # Get price rates
        origin_usd_price = get_coin_price(origin_currency_id)
        destination_usd_price = get_coin_price(destination_currency_id)
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
            current_destination_balance = Decimal(
                str(wallet.balance.get(destination_currency_id, '0')))
            current_origin_balance = Decimal(
                str(wallet.balance.get(origin_currency_id, '0')))
            if current_origin_balance < origin_amount:
                return TransactionResult(
                    success=False,
                    transaction_record=None,
                    status='insufficient_funds',
                    message=f"Insufficient {origin_currency_id} balance. Current balance is {current_origin_balance}",
                    error_type='InsufficientFundsError'
                )

            # (Perform swap) Update wallet balances
            wallet.balance[origin_currency_id] = str(
                current_origin_balance - origin_amount)
            wallet.balance[destination_currency_id] = str(
                current_destination_balance + destination_amount)
            wallet.save()

            # Record the swap transaction
            transaction_record = Transaction.objects.create(
                user=user,
                wallet=wallet,
                base_currency=origin_currency_id,
                base_amount=origin_amount,
                destination_currency=destination_currency_id,
                destination_amount=destination_amount,
                rate=rate,
                swap_destination_usd_rate=destination_usd_price,
                swap_origin_usd_rate=origin_usd_price,
                transaction_type='swap',
                status='completed',
                transaction_details=f"Swapped {origin_amount} {origin_currency_id} "
                f"for {destination_amount} {destination_currency_id}"
            )
            return TransactionResult(
                success=True,
                transaction_record=transaction_record,
                status='completed',
                message=(
                    f"Successfully swapped {origin_amount} {origin_currency_id} "
                    f"for {destination_amount:.8f} {destination_currency_id}"
                ),
                final_balances={
                    origin_currency_id: wallet.balance[origin_currency_id],
                    destination_currency_id: wallet.balance[destination_currency_id]
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
        cryptocurrency_id: str,
        amount: Union[Decimal, float, str],
        transaction_type: str) -> TransactionResult:
    """
    Simulates and executes a trading transaction, providing detailed status reporting.

    Args:
        user_id: Telegram user ID
        cryptocurrency_id: Cryptocurrency to trade
        amount: Amount of Cryptocurrency to trade
        transaction_type: Type of transaction ('buy' or 'sell')

    Returns:
        TransactionResult object containing execution status and details
    """
    try:
        # Input validation
        if not all([user_id, cryptocurrency_id, amount, transaction_type]):
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='invalid_input',
                message='All parameters are required',
                error_type='ValidationError'
            )
        if not isinstance(amount, (Decimal, float, int)):
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='invalid_input',
                message='Amount must be a number',
                error_type='ValidationError'
            )
        amount = Decimal(str(amount))
        if amount <= 0:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='invalid_input',
                message='Amount must be positive',
                error_type='ValidationError'
            )
        transaction_type = transaction_type.lower()
        if transaction_type not in ['buy', 'sell']:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='invalid_input',
                message="Transaction type must be 'buy' or 'sell'",
                error_type='ValidationError'
            )
        cryptocurrency_id = cryptocurrency_id.lower()
        try:
            coin = Coin.objects.get(id=cryptocurrency_id)
        except:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='unsupported_currency',
                message="Currency not supported",
                error_type='ValidationError'
            )
        # if cryptocurrency_id not in Coin.objects.filter(is_active=True).values_list('id', flat=True):

        price = get_coin_price(cryptocurrency_id)
        # price = 27000.33
        print(f"coin price is {price}")
        if not price:
            return TransactionResult(
                success=False,
                transaction_record=None,
                status='price_unavailable',
                message="Price data unavailable for the currency",
                error_type='ValidationError'
            )
        usd_value = amount * Decimal(price)

        user = get_object_or_404(User, user_id=user_id)
        wallet = get_user_wallet(user_id)

        # Get current balances
        current_usd_balance = Decimal(str(wallet.balance.get('usd', 0)))
        current_crypto_balance = Decimal(
            str(wallet.balance.get(cryptocurrency_id, 0)))

        # Simulate the transaction
        with transaction.atomic():
            if transaction_type == 'buy':
                if current_usd_balance < usd_value:
                    return TransactionResult(
                        success=False,
                        transaction_record=None,
                        status='insufficient_funds',
                        message=f" Need: {usd_value:.8f}(USD) to buy {amount}({coin.name}), Have: {current_usd_balance}(USD)",
                        final_balances={
                            'usd': current_usd_balance,
                            cryptocurrency_id: current_crypto_balance
                        },
                        error_type='InsufficientFundsError'
                    )
                new_usd_balance = current_usd_balance - usd_value
                new_crypto_balance = current_crypto_balance + amount

                # Record the buy transaction
                transaction_record = Transaction.objects.create(
                    user=user,
                    wallet=wallet,
                    base_currency='usd',
                    base_amount=usd_value,
                    destination_currency=cryptocurrency_id,
                    destination_amount=amount,
                    rate=price,
                    transaction_type='buy',
                    status='completed',
                    transaction_details=f"Bought {amount} {cryptocurrency_id} at {price} USD"
                )
            elif transaction_type == 'sell':
                if current_crypto_balance < amount:
                    return TransactionResult(
                        success=False,
                        transaction_record=None,
                        status='insufficient_funds',
                        message=f"Insufficient {cryptocurrency_id} balance. Need: {amount}{cryptocurrency_id}, Have: {current_crypto_balance}",
                        final_balances={
                            'usd': current_usd_balance,
                            cryptocurrency_id: current_crypto_balance
                        },
                        error_type='InsufficientFundsError'
                    )
                new_usd_balance = current_usd_balance + usd_value
                new_crypto_balance = current_crypto_balance - amount

                # Record the sell transaction
                transaction_record = Transaction.objects.create(
                    user=user,
                    wallet=wallet,
                    base_currency=cryptocurrency_id,
                    base_amount=amount,
                    destination_currency='usd',
                    destination_amount=usd_value,
                    rate=price,
                    transaction_type='sell',
                    status='completed',
                    transaction_details=f"Sold {amount} {cryptocurrency_id} at {price} USD"
                )
            else:
                return TransactionResult(
                    success=False,
                    transaction_record=None,
                    status='invalid_transaction_type',
                    message="Transaction type must be 'buy' or 'sell'",
                    error_type='ValidationError'
                )

            # update the wallet balances
            wallet.balance['usd'] = str(new_usd_balance)
            wallet.balance[cryptocurrency_id] = str(new_crypto_balance)
            wallet.save()

            # Return the transaction result
            transaction_type = 'bought' if transaction_type == 'buy' else 'sold'
            return TransactionResult(
                success=True,
                transaction_record=transaction_record,
                status='completed',
                message=f"Successfully {transaction_type} {amount} {cryptocurrency_id} at {price} USD",
                final_balances={
                    'usd': new_usd_balance,
                    cryptocurrency_id: new_crypto_balance
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


def deposit_usd(user_id: str, amount: Union[Decimal, float, int]) -> TransactionResult:
    # validate input
    if not all([user_id, amount]):
        return TransactionResult(
            success=False,
            transaction_record=None,
            status='invalid_input',
            message='All parameters are required',
            error_type='ValidationError'
        )
    if not isinstance(amount, (Decimal, float, int)):
        return TransactionResult(
            success=False,
            transaction_record=None,
            status='invalid_input',
            message='Amount must be a number',
            error_type='ValidationError'
        )
    amount = Decimal(str(amount))
    if amount <= 0:
        return TransactionResult(
            success=False,
            transaction_record=None,
            status='invalid_input',
            message='Amount must be positive',
            error_type='ValidationError'
        )
    # get user and wallet
    try:
        wallet = get_user_wallet(user_id)
        current_balance: dict = wallet.balance
        current_balance['usd'] = Decimal(current_balance.get('usd', 0))
        # current_usd_balance = Decimal(str(wallet.balance.get('usd', '0')))
        # print(f"current usd balance: {current_usd_balance}")
    except:
        return TransactionResult(
            success=False,
            transaction_record=None,
            status='not_found',
            message=f'user with id:{user_id}, wallet not found',
            error_type='DoesNotExistError'
        )
    # update the wallet
    try:
        current_balance['usd'] = str(current_balance['usd'] + amount)
        wallet.balance = current_balance
        wallet.save()
        print(f'new usd balance: {wallet.balance["usd"]}')
    except Exception as e:
        print(f"Error: {e}")
        return TransactionResult(
            success=False,
            transaction_record=None,
            status='failed_deposit',
            message=f' Deposit of {amount} USD was unsuccessful',
            error_type='DoesNotExistError'
        )
    # return status
    return TransactionResult(
        success=True,
        transaction_record=None,
        status="deposit_successful",
        message=f" Successfully deposited {amount} USD",
        final_balances={
            "USD": wallet.balance['usd']
        }
    )
