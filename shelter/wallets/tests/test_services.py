from decimal import Decimal

import pytest

from shelter import money
from shelter.wallets import services
from shelter.wallets.factories import WalletFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def wallet():
    return WalletFactory(deposit=Decimal("2.58"), hold=Decimal("1"))


def test_deposit_amount(wallet):
    amount = money.Amount(Decimal("7.42"), money.Currencies.USD)

    services.deposit_amount(wallet, amount)

    wallet.refresh_from_db()
    assert wallet.deposit == Decimal("10.00")


def test_hold_amount(wallet):
    amount = money.Amount(Decimal("0.58"), money.Currencies.USD)

    services.hold_amount(wallet, amount)

    wallet.refresh_from_db()
    assert wallet.deposit == Decimal("2")
    assert wallet.hold == Decimal("1.58")


def test_hold_amount_when_insufficient(wallet):
    amount = money.Amount(Decimal("2.59"), money.Currencies.USD)

    with pytest.raises(services.InsufficientAmountError):
        services.hold_amount(wallet, amount)


def test_withdraw_amount(wallet):
    amount = money.Amount(Decimal("0.5"), money.Currencies.USD)

    services.withdraw_amount(wallet, amount)

    wallet.refresh_from_db()
    assert wallet.hold == Decimal("0.5")


def test_withdraw_amount_when_insufficient(wallet):
    amount = money.Amount(Decimal("1.5"), money.Currencies.USD)

    with pytest.raises(services.InsufficientAmountError):
        services.withdraw_amount(wallet, amount)
