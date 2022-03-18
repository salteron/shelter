import contextlib
from decimal import Decimal

from django.contrib.auth import models as users
from django.db import models as django_models, transaction

from shelter.deposits import models as deposits
from shelter.wallets import models


class InsufficientAmountError(Exception):
    pass


# TODO: комментарий про неэффективность
def get_or_create_wallet_for_deposit(
    deposit: deposits.Deposit, payment_system_account_number: str
) -> models.Wallet:
    wallet, _ = deposit.user.wallets.get_or_create(
        payment_system_id=deposit.payment_system_id,
        payment_system_account_number=payment_system_account_number,
        defaults={
            "deposit": Decimal("0"),
            "hold": Decimal("0"),
            "currency": deposit.currency,
        },
    )

    return wallet


def deposit_amount(wallet: models.Wallet, amount: models.Amount):
    amount_in_wallet_currency = convert_amount(amount, wallet.currency)

    with locked(wallet) as w:
        w.deposit += amount_in_wallet_currency.value
        w.save()


def hold_amount(wallet: models.Wallet, amount: models.Amount):
    amount_in_wallet_currency = convert_amount(amount, wallet.currency)

    with locked(wallet) as w:
        if w.deposit < amount_in_wallet_currency.value:
            raise InsufficientAmountError

        w.deposit -= amount_in_wallet_currency.value
        w.hold += amount_in_wallet_currency.value
        w.save()


def withdraw_amount(wallet: models.Wallet, amount: models.Amount):
    amount_in_wallet_currency = convert_amount(amount, wallet.currency)

    with locked(wallet) as w:
        if w.hold < amount_in_wallet_currency.value:
            raise InsufficientAmountError

        w.hold -= amount_in_wallet_currency.value
        w.save()


# TODO: to utils?
@contextlib.contextmanager
def locked(instance: django_models.Model):
    with transaction.atomic():
        yield instance.__class__.objects.select_for_update().get(pk=instance.pk)


# TODO: to utils
def convert_amount(amount: models.Amount, target_currency: str) -> models.Amount:
    if amount.currency == target_currency:
        return amount
    else:
        raise NotImplementedError
