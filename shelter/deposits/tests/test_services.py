import uuid
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from shelter.deposits import factories, models, services
from shelter.wallets import (
    factories as wallets_factories,
    models as wallets,
    services as wallets_services,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def wallet(user):
    return wallets_factories.WalletFactory(
        user=user, deposit=Decimal("150"), hold=Decimal("40")
    )


@pytest.fixture
def user():
    return wallets_factories.UserFactory()


@pytest.fixture
def deposit(user):
    return factories.DepositFactory(
        pending=True,
        user=user,
        value=Decimal("10"),
        currency=models.Currencies.USD,
        payment_system_id="superpay",
    )


@pytest.fixture
def payout(wallet):
    return factories.PayoutFactory(
        pending=True,
        wallet=wallet,
        value=Decimal("10"),
        currency=models.Currencies.USD,
        payment_system_id="superpay",
    )


class TestCreateDeposit:
    @patch(
        "shelter.deposits.services.uuid.uuid4",
        Mock(return_value="9c7b3114-06da-4fdd-b641-4558a50f9492"),
    )
    def test_when_success(self, user):
        amount = wallets.Amount(Decimal("100"), wallets.Currencies.USD)

        deposit = services.create_deposit(user, amount)

        deposit.refresh_from_db()
        assert deposit.value == amount.value
        assert deposit.currency == amount.currency
        assert deposit.transaction_id == uuid.UUID(
            "9c7b3114-06da-4fdd-b641-4558a50f9492"
        )
        assert deposit.state == models.TransactionStates.PENDING
        assert deposit.cancelation_reason is None
        assert deposit.wallet is None
        assert deposit.user == user
        assert deposit.payment_system_id == "superpay"
        assert deposit.confirmation_url == "http://superpay.com/deposit/42/confirmation"


class TestCreatePayout:
    def test_when_success(self, wallet):
        amount = wallets.Amount(Decimal("100"), wallets.Currencies.USD)

        payout = services.create_payout(wallet, amount)

        payout.refresh_from_db()
        wallet.refresh_from_db()
        assert payout.value == amount.value
        assert payout.currency == amount.currency
        assert payout.state == models.TransactionStates.PENDING
        assert payout.cancelation_reason is None
        assert payout.wallet == wallet
        assert payout.payment_system_id == "superpay"
        assert wallet.deposit == Decimal("50")
        assert wallet.hold == Decimal("140")

    def test_when_insufficient_amount(self, wallet):
        amount = wallets.Amount(Decimal("200"), wallets.Currencies.USD)

        with pytest.raises(wallets_services.InsufficientAmountError):
            services.create_payout(wallet, amount)


class TestHandleSucceededDeposit:
    def test_when_wallet_does_not_exist_yet(self, deposit):
        services.handle_succeeded_deposit(deposit.transaction_id, "superpay-007")

        deposit.refresh_from_db()
        assert deposit.state == models.TransactionStates.SUCCEEDED

        wallet = deposit.wallet
        assert wallet.user == deposit.user
        assert wallet.payment_system_id == "superpay"
        assert wallet.payment_system_account_number == "superpay-007"
        assert wallet.deposit == Decimal("10")
        assert wallet.hold == Decimal("0")
        assert wallet.currency == models.Currencies.USD

    def test_when_wallet_already_exists(self, deposit):
        wallet = wallets_factories.WalletFactory(
            user=deposit.user,
            payment_system_id=deposit.payment_system_id,
            payment_system_account_number="superpay-007",
            deposit=Decimal("5"),
        )

        services.handle_succeeded_deposit(deposit.transaction_id, "superpay-007")

        deposit.refresh_from_db()
        assert deposit.state == models.TransactionStates.SUCCEEDED

        wallet = deposit.wallet
        assert wallet.user == deposit.user
        assert wallet.payment_system_id == "superpay"
        assert wallet.payment_system_account_number == "superpay-007"
        assert wallet.deposit == Decimal("15")
        assert wallet.hold == Decimal("0")
        assert wallet.currency == models.Currencies.USD

    def test_when_deposit_is_already_not_pending(self, deposit):
        deposit.state = models.TransactionStates.CANCELED
        deposit.save()

        services.handle_succeeded_deposit(deposit.transaction_id, "superpay-007")

        deposit.refresh_from_db()
        assert deposit.state == models.TransactionStates.CANCELED
        assert deposit.wallet is None


class TestHandleCanceledDeposit:
    def test_when_deposit_is_pending(self, deposit):
        services.handle_canceled_deposit(deposit.transaction_id, "cancelation-reason")

        deposit.refresh_from_db()
        assert deposit.state == models.TransactionStates.CANCELED
        assert deposit.cancelation_reason == "cancelation-reason"
        assert deposit.wallet is None

    def test_when_deposit_is_already_not_pending(self, deposit):
        deposit.state = models.TransactionStates.SUCCEEDED
        deposit.save()

        services.handle_canceled_deposit(deposit.transaction_id, "cancelation-reason")

        deposit.refresh_from_db()
        assert deposit.state == models.TransactionStates.SUCCEEDED
        assert deposit.cancelation_reason is None


class TestHandleSucceededPayout:
    def test_when_payout_is_pending(self, payout):
        services.handle_succeeded_payout(payout.transaction_id)

        payout.refresh_from_db()
        assert payout.state == models.TransactionStates.SUCCEEDED

        wallet = payout.wallet
        assert wallet.hold == Decimal("30")

    def test_when_payout_is_already_not_pending(self, payout):
        payout.state = models.TransactionStates.CANCELED
        payout.save()

        services.handle_succeeded_payout(payout.transaction_id)

        payout.refresh_from_db()
        assert payout.state == models.TransactionStates.CANCELED

        wallet = payout.wallet
        assert wallet.hold == Decimal("40")


class TestHandleCanceledPayout:
    def test_when_payout_is_pending(self, payout):
        services.handle_canceled_payout(payout.transaction_id, "cancelation-reason")

        payout.refresh_from_db()
        assert payout.state == models.TransactionStates.CANCELED
        assert payout.cancelation_reason == "cancelation-reason"

        wallet = payout.wallet
        assert wallet.deposit == Decimal("160")
        assert wallet.hold == Decimal("30")

    def test_when_payout_is_already_not_pending(self, payout):
        payout.state = models.TransactionStates.SUCCEEDED
        payout.save()

        services.handle_canceled_payout(payout.transaction_id, "cancelation-reason")

        payout.refresh_from_db()
        assert payout.state == models.TransactionStates.SUCCEEDED
        assert payout.cancelation_reason is None

        wallet = payout.wallet
        assert wallet.deposit == Decimal("150")
        assert wallet.hold == Decimal("40")
