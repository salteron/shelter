from decimal import Decimal

import pytest

from shelter.wallets import models, services
from shelter.wallets.factories import WalletFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def wallet():
    return WalletFactory(deposit=Decimal("2.58"), hold=Decimal("1"))


def test_deposit_amount(wallet):
    amount = models.Amount(Decimal("7.42"), models.Currencies.USD)

    services.deposit_amount(wallet, amount)

    wallet.refresh_from_db()
    assert wallet.deposit == Decimal("10.00")


def test_hold_amount(wallet):
    amount = models.Amount(Decimal("0.58"), models.Currencies.USD)

    services.hold_amount(wallet, amount)

    wallet.refresh_from_db()
    assert wallet.deposit == Decimal("2")
    assert wallet.hold == Decimal("1.58")


def test_hold_amount_when_insufficient(wallet):
    amount = models.Amount(Decimal("2.59"), models.Currencies.USD)

    with pytest.raises(services.InsufficientAmountError):
        services.hold_amount(wallet, amount)


def test_withdraw_amount(wallet):
    amount = models.Amount(Decimal("0.5"), models.Currencies.USD)

    services.withdraw_amount(wallet, amount)

    wallet.refresh_from_db()
    assert wallet.hold == Decimal("0.5")


def test_withdraw_amount_when_insufficient(wallet):
    amount = models.Amount(Decimal("1.5"), models.Currencies.USD)

    with pytest.raises(services.InsufficientAmountError):
        services.withdraw_amount(wallet, amount)
