import uuid
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from shelter.deposits import models, services
from shelter.wallets import models as wallets
from shelter.wallets.factories import WalletFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def wallet():
    return WalletFactory()


class TestCreateDeposit:
    @patch(
        "shelter.deposits.services.uuid.uuid4",
        Mock(return_value="9c7b3114-06da-4fdd-b641-4558a50f9492"),
    )
    def test_when_success(self, wallet):
        amount = wallets.Amount(Decimal("100"), wallets.Currencies.USD)

        deposit = services.create_deposit(wallet, amount)

        deposit.refresh_from_db()
        assert deposit.value == amount.value
        assert deposit.currency == amount.currency
        assert deposit.transaction_id == uuid.UUID(
            "9c7b3114-06da-4fdd-b641-4558a50f9492"
        )
        assert deposit.state == models.TransactionStates.PENDING
        assert deposit.cancelation_reason is None
        assert deposit.wallet == wallet
        assert deposit.payment_system_id == "superpay"
        assert deposit.payment_system_transaction_id == "42"
        assert deposit.confirmation_url == "http://superpay.com/deposit/42/confirmation"
