from decimal import Decimal
from unittest.mock import patch

import pytest

from shelter.deposits import factories, models, services
from shelter.payment_systems import models as payment_systems
from shelter.payment_systems.superpay import Superpay
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
    def test_when_success(self, user):
        amount = wallets.Amount(Decimal("100"), wallets.Currencies.USD)

        deposit = services.create_deposit(user, Superpay, amount)

        deposit.refresh_from_db()
        assert deposit.value == amount.value
        assert deposit.currency == amount.currency
        assert deposit.is_created()
        assert deposit.cancelation_reason is None
        assert deposit.wallet is None
        assert deposit.user == user
        assert deposit.payment_system_id == "superpay"
        assert deposit.confirmation_url is None


class TestCreatePaymentSystemDeposit:
    def test_when_deposit_is_created(self):
        deposit = factories.DepositFactory(created=True)

        services.create_payment_system_deposit(deposit.pk)

        deposit.refresh_from_db()
        assert deposit.is_pending()
        assert deposit.confirmation_url == "http://superpay.com/deposit/42/confirmation"

    def test_when_deposit_is_already_not_created(self):
        deposit = factories.DepositFactory(canceled=True)

        services.create_payment_system_deposit(deposit.pk)

        deposit.refresh_from_db()
        assert deposit.is_canceled()

    @patch.object(Superpay, "create_deposit", lambda *args, **kwargs: 1 / 0)
    def test_when_request_fails(self):
        deposit = factories.DepositFactory(created=True)

        with pytest.raises(Exception):
            services.create_payment_system_deposit(deposit.pk)

        deposit.refresh_from_db()
        assert deposit.is_created()


class TestCreatePayout:
    def test_when_success(self, wallet):
        amount = wallets.Amount(Decimal("100"), wallets.Currencies.USD)

        payout = services.create_payout(wallet, amount)

        payout.refresh_from_db()
        wallet.refresh_from_db()
        assert payout.value == amount.value
        assert payout.currency == amount.currency
        assert payout.is_created()
        assert payout.cancelation_reason is None
        assert payout.wallet == wallet
        assert payout.payment_system_id == "superpay"
        assert wallet.deposit == Decimal("50")
        assert wallet.hold == Decimal("140")

    def test_when_insufficient_amount(self, wallet):
        amount = wallets.Amount(Decimal("200"), wallets.Currencies.USD)

        with pytest.raises(wallets_services.InsufficientAmountError):
            services.create_payout(wallet, amount)


class TestCreatePaymentSystemPayout:
    def test_when_payout_is_created(self):
        payout = factories.PayoutFactory(created=True)

        services.create_payment_system_payout(payout.pk)

        payout.refresh_from_db()
        assert payout.is_pending()

    def test_when_payout_is_already_not_created(self):
        payout = factories.PayoutFactory(canceled=True)

        services.create_payment_system_payout(payout.pk)

        payout.refresh_from_db()
        assert payout.is_canceled()

    @patch.object(Superpay, "create_payout", lambda *args, **kwargs: 1 / 0)
    def test_when_request_fails(self):
        payout = factories.PayoutFactory(created=True)

        with pytest.raises(Exception):
            services.create_payment_system_payout(payout.pk)

        payout.refresh_from_db()
        assert payout.is_created()


class TestHandleDepositSucceededEvent:
    @pytest.fixture
    def event(self, deposit):
        return payment_systems.DepositSucceededEvent(
            transaction_id=deposit.transaction_id, account_number="superpay-007"
        )

    def test_when_wallet_does_not_exist_yet(self, deposit, event):
        services.handle_deposit_succeeded_event(event)

        deposit.refresh_from_db()
        assert deposit.is_succeeded()

        wallet = deposit.wallet
        assert wallet.user == deposit.user
        assert wallet.payment_system_id == "superpay"
        assert wallet.payment_system_account_number == "superpay-007"
        assert wallet.deposit == Decimal("10")
        assert wallet.hold == Decimal("0")
        assert wallet.currency == models.Currencies.USD

    def test_when_wallet_already_exists(self, deposit, event):
        wallet = wallets_factories.WalletFactory(
            user=deposit.user,
            payment_system_id=deposit.payment_system_id,
            payment_system_account_number="superpay-007",
            deposit=Decimal("5"),
        )

        services.handle_deposit_succeeded_event(event)

        deposit.refresh_from_db()
        assert deposit.is_succeeded()

        wallet = deposit.wallet
        assert wallet.user == deposit.user
        assert wallet.payment_system_id == "superpay"
        assert wallet.payment_system_account_number == "superpay-007"
        assert wallet.deposit == Decimal("15")
        assert wallet.hold == Decimal("0")
        assert wallet.currency == models.Currencies.USD

    def test_when_deposit_is_already_not_pending(self, deposit, event):
        deposit.state = models.TransactionStates.CANCELED
        deposit.save()

        services.handle_deposit_succeeded_event(event)

        deposit.refresh_from_db()
        assert deposit.is_canceled()
        assert deposit.wallet is None


class TestHandleDepositCanceledEvent:
    @pytest.fixture
    def event(self, deposit):
        return payment_systems.DepositCanceledEvent(
            transaction_id=deposit.transaction_id,
            cancelation_reason="cancelation-reason",
        )

    def test_when_deposit_is_pending(self, deposit, event):
        services.handle_deposit_canceled_event(event)

        deposit.refresh_from_db()
        assert deposit.is_canceled()
        assert deposit.cancelation_reason == "cancelation-reason"
        assert deposit.wallet is None

    def test_when_deposit_is_already_not_pending(self, deposit, event):
        deposit.state = models.TransactionStates.SUCCEEDED
        deposit.save()

        services.handle_deposit_canceled_event(event)

        deposit.refresh_from_db()
        assert deposit.is_succeeded()
        assert deposit.cancelation_reason is None


class TestHandlePayoutSucceededEvent:
    @pytest.fixture
    def event(self, payout):
        return payment_systems.PayoutSucceededEvent(
            transaction_id=payout.transaction_id
        )

    def test_when_payout_is_pending(self, payout, event):
        services.handle_payout_succeeded_event(event)

        payout.refresh_from_db()
        assert payout.is_succeeded()

        wallet = payout.wallet
        assert wallet.hold == Decimal("30")

    def test_when_payout_is_already_not_pending(self, payout, event):
        payout.state = models.TransactionStates.CANCELED
        payout.save()

        services.handle_payout_succeeded_event(event)

        payout.refresh_from_db()
        assert payout.is_canceled()

        wallet = payout.wallet
        assert wallet.hold == Decimal("40")


class TestHandlePayoutCanceledEvent:
    @pytest.fixture
    def event(self, payout):
        return payment_systems.PayoutCanceledEvent(
            transaction_id=payout.transaction_id,
            cancelation_reason="cancelation-reason",
        )

    def test_when_payout_is_pending(self, payout, event):
        services.handle_payout_canceled_event(event)

        payout.refresh_from_db()
        assert payout.is_canceled()
        assert payout.cancelation_reason == "cancelation-reason"

        wallet = payout.wallet
        assert wallet.deposit == Decimal("160")
        assert wallet.hold == Decimal("30")

    def test_when_payout_is_already_not_pending(self, payout, event):
        payout.state = models.TransactionStates.SUCCEEDED
        payout.save()

        services.handle_payout_canceled_event(event)

        payout.refresh_from_db()
        assert payout.is_succeeded()
        assert payout.cancelation_reason is None

        wallet = payout.wallet
        assert wallet.deposit == Decimal("150")
        assert wallet.hold == Decimal("40")
