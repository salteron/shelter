import contextlib

from django.db import models as django_models, transaction

from shelter.wallets import models


class InsufficientAmountError(Exception):
    pass


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
