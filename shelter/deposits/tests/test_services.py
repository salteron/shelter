import uuid
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from shelter.deposits import factories, models, services
from shelter.wallets import factories as wallets_factories, models as wallets

pytestmark = pytest.mark.django_db


@pytest.fixture
def wallet(user):
    return wallets_factories.WalletFactory(user=user, deposit=Decimal("150"))


@pytest.fixture
def user():
    return wallets_factories.UserFactory()


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
        assert wallet.hold == Decimal("100")


class TestHandleSucceededDeposit:
    @pytest.fixture
    def deposit(self, user):
        return factories.DepositFactory(
            user=user,
            value=Decimal("10"),
            currency=models.Currencies.USD,
            payment_system_id="superpay",
        )

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
